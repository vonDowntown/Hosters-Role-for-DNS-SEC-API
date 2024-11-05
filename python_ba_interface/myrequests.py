import urllib.parse
from typing import TypedDict, TypeVar, Generic

import requests
from .auth import Auth
from .mytypes import DNS, Registrar, CouldNotSetDataExeption
import aiohttp

T = TypeVar('T', bound=TypedDict)
U = TypeVar('U', bound=TypedDict)
def possibleKeys():
    mylist = list(DNS.__annotations__.keys())
    mylist.extend(Registrar.__annotations__.keys())
    return mylist # not beautiful but functional

def moveToNewQueryIfExists(query: dict, newQuery: dict, key: str):
    if key in query.keys():
        newQuery.update({key: query.pop(key)})


def sortQuery(query: dict) -> dict:
    result = {}
    moveToNewQueryIfExists(query, result, "$sort")
    moveToNewQueryIfExists(query, result, "$limit")
    moveToNewQueryIfExists(query, result, "$skip")
    moveToNewQueryIfExists(query, result, "_id")
    moveToNewQueryIfExists(query, result, "$or")

    for key in list(query.keys()):
        if key in possibleKeys():
            result.update({key: query.pop(key)})

    if len(query) != 0:
        print(f"Query not empty: {query}")

    return result

class MyAsyncRequests(Generic[T]):
    def __init__(self, server: str, auth: Auth):
        self.auth = auth
        self.session = aiohttp.ClientSession()


    def _headers(self)-> dict:
        token = self.auth.auth()
        headers = {"Authorization": f"Bearer {token}"}
        return headers

    def _url(self, url: str, query: dict)-> str:
        url = f"http://{url}" if not (url.startswith('http://') or url.startswith('https://')) else url
        if '_id' in query:
            if type(query.get('_id')) is str:
                _id = query.get('_id')
                url = f"{url}/{_id}"
                query.pop('_id')
                if query != {}:
                    raise NotImplemented("No Query allows the simultaneous use of _id and other queries. Only _id is allowed.")
        query = sortQuery(query)
        final_url = f"{url}?{self.encode_query(query)}" if len(query) != 0 else url
        return final_url

    async def get(self, url: str, query: dict)-> T:
        headers = self._headers()
        final_url = self._url(url, query)
        # print(final_url)
        data = await self.session.get(final_url, headers=headers)
        return await data.json()

    async def post(self, url: str, json: dict):
        token = self.auth.auth()
        headers = {"Authorization": f"Bearer {token}"}
        url = f"http://{url}" if not (url.startswith('http://') or url.startswith('https://')) else url
        data = await self.session.post(url, json=json, headers=headers)
        if data.status == 500:
            data = await self.session.post(url, json=json, headers=headers)
        if data.status != 201:
            raise CouldNotSetDataExeption(data.text)
        return await data.json()

    async def update(self, url: str, query: dict, json: dict):
        headers = self._headers()
        final_url = self._url(url, query)
        data = await self.session.put(final_url, json=json, headers=headers)
        return await data.json()

    async def patch(self, url: str, query: dict, json: dict):
        headers = self._headers()
        final_url = self._url(url, query)
        data = await self.session.patch(final_url, json=json, headers=headers)
        return await data.json()

    async def delete(self, url: str, query: dict):
        headers = self._headers()
        final_url = self._url(url, query)
        data = await self.session.delete(final_url, headers=headers)
        return await data.json()

    def resetSession(self):
        session = aiohttp.ClientSession()
        if not self.session.closed:
            self.session.close()
        self.session = session

    def encode_query(self, query: dict) -> str:
        result = ""
        for key in query.keys():
            if key in possibleKeys():
                options: dict = query.get(key)
                array_result = self._handle_array_query(key, options)
                result = self.append_query(result, array_result)
                continue
            match key:
                case "$or":
                    options: dict = query.get(key)
                    array_result = self._handle_array_query(key, options)
                    result = self.append_query(result, array_result)
                case '$sort':
                    val: dict = query.get(key)
                    for k, v in val.items():
                        if k is str and v is int and (v == 1 or v == -1):
                            result = self.append_query(result, f"$sort[{k}]={v}")
                        else:
                            assert Exception("Sort must be a dict with str as key and 1 or -1 as value")
                case '$skip':
                    val: int = query.get(key)
                    # if val > 0:
                    result = self.append_query(result, f"$skip={val}")
                case '$limit':
                    val: int = query.get(key)
                    if 0 <= val <= 50:
                        result = self.append_query(result, f"$limit={val}")
                    else:
                        assert Exception("Limit must be between 0 and 50")
                case _:
                    print(f"Case {key} not implemented in encodeQuery")

        return result

    def _handle_array_query(self, array_name: str, query: dict):
        result = ""
        if type(query) is str:
            result = self.append_query(result, f"{array_name}={query}")
        elif type(query) is dict:
            for key in query.keys():
                match key:
                    case "$exists":
                        exists = "true" if query.get(key) else "false"
                        result = self.append_query(result, f"{array_name}[{key}]={exists}")
                    case "$size":
                        val: int = query.get(key)
                        result = self.append_query(result, f"{array_name}[{key}]={val}")
                    case "$gt":
                        val = query.get(key)
                        result = self.append_query(result, f"{array_name}[{key}]={val}")
                    case "$gte":
                        val = query.get(key)
                        result = self.append_query(result, f"{array_name}[{key}]={val}")
                    case "$all":
                        val: list[str] = query.get(key)
                        for element in val:
                            encoded_element = urllib.parse.quote_plus(element)
                            result = self.append_query(result, f"{array_name}[{key}][]={encoded_element}")
                    case "$in":
                        val: list[str] = query.get(key)
                        for element in val:
                            encoded_element = urllib.parse.quote_plus(element)
                            result = self.append_query(result, f"{array_name}[{key}][]={encoded_element}")
                    case _:
                        print(f"Case {key} not implemented in _handle_array_query")
        else:
            print(f"Type {type(query)} not implemented in _handle_array_query")
        return result

    def append_query(self, target: str, source: str) -> str:
        if (target == ""):
            return source
        elif (source == ""):
            return target
        else:
            return f"{target}&{source}"

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

    def __del__(self):
        if self.session:
            print("Session should be closed after use with  await obj.close()")


class MyRequests(Generic[U]):
    def __init__(self, server: str, auth: Auth):
        self.auth = auth

    def _headers(self):
        token = self.auth.auth()
        headers = {"Authorization": f"Bearer {token}"}
        return headers

    def _url(self, url: str, query: dict) -> str:
        url = f"http://{url}" if not (url.startswith('http://') or url.startswith('https://')) else url
        if '_id' in query:
            if type(query.get('_id')) is str:
                _id = query.get('_id')
                url = f"{url}/{_id}"
                query.pop('_id')
                if query != {}:
                    raise NotImplemented(
                        "No Query allows the simultaneous use of _id and other queries. Only _id is allowed.")
        query = sortQuery(query)
        final_url = f"{url}?{self.encode_query(query)}" if len(query) != 0 else url
        return final_url
    def get(self, url: str, query: dict)-> U:
        headers = self._headers()
        final_url = self._url(url, query)
        # print(final_url)
        data = requests.get(final_url, headers=headers)
        return data.json()

    def post(self, url: str, json: dict):
        headers = self._headers()
        final_url = self._url(url, {})
        data = requests.post(final_url, json=json, headers=headers)
        if data.status_code != 201:
            raise CouldNotSetDataExeption(data.text)
        return data.json()

    def update(self, url: str, query: dict, json: dict):
        headers = self._headers()
        final_url = self._url(url, query)
        data = requests.put(final_url, json=json, headers=headers)
        return data.json()

    def patch(self, url: str, query: dict, json: dict):
        headers = self._headers()
        final_url = self._url(url, query)
        data = requests.patch(final_url, json=json, headers=headers)
        return data.json()

    def delete(self, url: str, query: dict):
        headers = self._headers()
        final_url = self._url(url, query)
        data = requests.delete(final_url, headers=headers)
        return data.json()

    def encode_query(self, query: dict) -> str:
        result = ""
        for key in query.keys():
            if key in possibleKeys():
                options: dict = query.get(key)
                array_result = self._handle_array_query(key, options)
                result = self.append_query(result, array_result)
                continue
            match key:
                case '$sort':
                    val: dict = query.get(key)
                    for k, v in val.items():
                        if k is str and v is int and (v == 1 or v == -1):
                            result = self.append_query(result, f"$sort[{k}]={v}")
                        else:
                            assert Exception("Sort must be a dict with str as key and 1 or -1 as value")
                case '$skip':
                    val: int = query.get(key)
                    # if val > 0:
                    result = self.append_query(result, f"$skip={val}")
                case '$limit':
                    val: int = query.get(key)
                    if 0 <= val <= 50:
                        result = self.append_query(result, f"$limit={val}")
                    else:
                        assert Exception("Limit must be between 0 and 50")
                case _:
                    print(f"Case {key} not implemented in encodeQuery")


        return result

    def _handle_array_query(self, array_name: str, query: dict):
        result = ""
        if type(query) is str:
            result = self.append_query(result, f"{array_name}={query}")
        elif type(query) is dict:
            for key in query.keys():
                match key:
                    case "$exists":
                        exists = "true" if query.get(key) else "false"
                        result = self.append_query(result, f"{array_name}[{key}]={exists}")
                    case "$size":
                        val: int = query.get(key)
                        result = self.append_query(result, f"{array_name}[{key}]={val}")
                    case "$gt":
                        val = query.get(key)
                        result = self.append_query(result, f"{array_name}[{key}]={val}")
                    case "$gte":
                        val = query.get(key)
                        result = self.append_query(result, f"{array_name}[{key}]={val}")
                    case "$all":
                        val: list[str] = query.get(key)
                        for element in val:
                            encoded_element = urllib.parse.quote_plus(element)
                            result = self.append_query(result, f"{array_name}[{key}][]={encoded_element}")
                    case "$in":
                        val: list[str] = query.get(key)
                        for element in val:
                            encoded_element = urllib.parse.quote_plus(element)
                            result = self.append_query(result, f"{array_name}[{key}][]={encoded_element}")
                    case _:
                        print(f"Case {key} not implemented in _handle_array_query")
        else:
            print(f"Type {type(query)} not implemented in _handle_array_query")
        return result

    def append_query(self, target: str, source: str) -> str:
        if (target == ""):
            return source
        elif (source == ""):
            return target
        else:
            return f"{target}&{source}"
