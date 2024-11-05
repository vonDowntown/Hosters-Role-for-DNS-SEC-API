import copy
from tqdm import tqdm

from . import MongoDB
from .myrequests import MyRequests, MyAsyncRequests
from .mytypes import DNS as DNS_Type, Registrar, PartialRegistrar, CouldNotSetDataExeption
from .mytypes import PartialDNS


# Generic class (based on results)
# uses my requests to get/set data from the server
# should implement:
# - get All: get all data from the server pagination would be great
# - get
# - set (check prior if it exists)
# - update
# - delete
# - find (query)

# write iterator for that so i can call a basic query and manage everything in the back

# see https://medium.com/geekculture/asynchronous-iterators-in-python-fdf55198287d

def slize_Array(array: list, size: int) -> list[list]:
    result = []
    for i in range(0, len(array), size):
        result.append(array[i:i + size])
    return result


class DNSIterator:
    def __init__(self, url: str, myRequest: MyAsyncRequests, myoldRequest: MyRequests, query: dict, stepsize: int = 50):
        self.url = url
        self.my_request = myRequest
        self.my_old_request = myoldRequest
        self.query = query
        self.stepsize = stepsize
        myquery = copy.deepcopy(self.query)
        self.results = []
        self.query.update({"$sort": {"_id": 1}})
        myquery.update({
            "$sort": {"_id": 1},
            "$limit": 0
        })
        data = self.my_old_request.get(self.url, myquery)
        length = data["total"]
        index = 0
        self.results.extend(data["data"])
        self.length = length
        self.index = index

    def __aiter__(self):
        # self.index = 0
        return self

    async def __anext__(self):
        try:
            # extract the keys one at a time
            i = self.index
            # return values for a key
            myquery = copy.deepcopy(self.query)
            if type(i) is int:
                myquery.update({"$limit": self.stepsize, "$skip": i})
            if type(i) is str:
                myquery.update({"_id": {"$gt": i}, "$limit": self.stepsize})
            # print(myquery)
            data = await self.my_request.get(self.url, myquery)
            result = data["data"]
            result = sorted(result, key=lambda x: x["_id"])
            if len(result) == 0:
                raise StopAsyncIteration
            self.results.extend(result)
            *_, last = result
            self.index = last["_id"]
            return result
        except StopIteration:
            # raise stopasynciteration at the end of iterator
            raise StopAsyncIteration


class DNS:
    def __init__(self, server: str, myRequest: MyRequests, myAsyncRequest: MyAsyncRequests, myMongoDB: MongoDB):
        self.url = f'http://{server}/dns'
        self.my_request = myRequest
        self.my_async_request = myAsyncRequest
        self.my_mongo_db = myMongoDB
        self.collectionName = "dns"

    def get_all(self) -> [DNS_Type]:
        data = self.my_mongo_db.find(self.collectionName, {})
        return data

    def get(self, domain: str) -> DNS_Type:
        query = {"domain": domain}
        data = self.my_request.get(self.url, query)
        return data

    def set(self, data: DNS_Type):
        try:
            return self.my_request.post(self.url, data)
        except:
            print("could not set data")

    def find(self, query, sort: dict = None, logging = False, idReplace: bool = None) -> [DNS_Type]:
        data = self.my_mongo_db.find(self.collectionName, query, sort=sort, logging=logging, idReplace=idReplace)
        return data

    def update(self, data: PartialDNS, _id: str = "", query={}):
        if query == {} and _id == "":
            print("error: no query or id")
            return
        new_url = f"{self.url}/{_id}"
        self.my_request.patch(new_url, query, data)

    def delete(self, domain: str):
        query = {"domain": domain}
        self.my_request.delete(self.url, query)

    def get_data_size(self, query: dict):
        data = self.my_mongo_db.count(self.collectionName, query)
        return data

class Registrar_Class:
    def __init__(self, server: str, myRequest: MyRequests, myAsyncRequest: MyAsyncRequests, myMongoDB: MongoDB):
        self.url = f'http://{server}/registrar'
        self.my_request = myRequest
        self.my_async_request = myAsyncRequest
        self.my_mongo_db = myMongoDB
        self.collectionName = "registrar"

    def get_all(self) -> [Registrar]:
        data = self.my_mongo_db.find(self.collectionName, {}, logging=True)
        return data

    def get(self, domain: str) -> Registrar:
        query = {"domain": domain}
        data = self.my_request.get(self.url, query)
        return data

    def set_bulk(self, data: [Registrar]):
        could_not: [Registrar] = []
        for i in data:
            try:
                self.set(i)
            except CouldNotSetDataExeption as e:
                could_not.append((i, e))

        if len(could_not) > 0:
            could_not = list(map(lambda x: (x[0]["domain"], x[1]), could_not))
            print("could not Set the following Objects:")
            print(could_not)

    def set(self, data: Registrar):
        try:
            self.my_request.post(self.url, data)
        except CouldNotSetDataExeption as e:
            raise e

    def find(self, query, sort: dict = None, logging = False, idReplace: bool = None) -> [Registrar]:
        data = self.my_mongo_db.find(self.collectionName, query, sort=sort, logging=logging, idReplace=idReplace)
        return data

    def update(self, data: PartialRegistrar, _id: str = "", query={}):
        if query == {} and _id == "":
            print("error: no query or id")
            return
        new_url = f"{self.url}/{_id}"
        self.my_request.patch(new_url, query, data)

    def delete(self, domain: str):
        query = {"domain": domain}
        self.my_request.delete(self.url, query)

    def bulk_delete(self, query: dict):
        data = self.find(query, idReplace=True)
        todelete = map(lambda x: x["_id"], data)
        for i in todelete:
            self.my_request.delete(self.url, {"_id": i})

    def get_data_size(self, query: dict):
        data = self.my_mongo_db.count(self.collectionName, query)
        return data

    def findDoublicates(self) -> list[Registrar]:
        result = []
        data = self.get_all()
        mytqdm = tqdm(data)
        mytqdm.set_description("Finding Doublicates")
        for element in mytqdm:
            domainExistsMoreThanOnce = self.get_data_size({"domain": element["domain"]}) > 1
            NameserverUsedMoreThanOnce = self.get_data_size({"nsServer": {"$in": element["nsServer"]}}) > 1

            if domainExistsMoreThanOnce or NameserverUsedMoreThanOnce:
                result.append(element)

        return result

