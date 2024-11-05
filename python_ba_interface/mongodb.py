import copy
import itertools

from pymongo.errors import OperationFailure
from pymongo.mongo_client import MongoClient
from pymongo.cursor import Cursor
from pymongo.database import Database
from tqdm import tqdm


class MongoDB:
    def __init__(self, uri, databaseUri: str = "dns-backend"):
        self.client = MongoClient(uri)
        self.dbUri = databaseUri
        self.db: Database = self.client.get_database(databaseUri)

    def ping(self):
        try:
            self.client.admin.command('ping')
            print("Pinged your deployment. You successfully connected to MongoDB!")
            return True
        except Exception as e:
            print(e)

    def count(self, collectionName, query=None):
        if query is None:
            query = {}
        return self.db.get_collection(collectionName).count_documents(query)

    def _find(self, collectionName, query: dict, sort=None):
        if sort is None:
            sort = [('_id', 1)]
        return self.db.get_collection(collectionName).find(query, sort=sort)

    def find(self, collectionName, query: dict, sort=None, logging: bool = False, idReplace: bool = None):
        cursor = self._find(collectionName, query, sort)
        return self.resolve(cursor, query, logging=logging, idReplace=idReplace)

    def resolve(self, cursor: Cursor, query: dict, logging: bool = False, idReplace: bool = True):
        if idReplace == None:
            idReplace = True
        count = self.count(cursor.collection.name, query)
        logquery = copy.deepcopy(query)
        if "NS" in logquery.keys():
            if "$in" in logquery["NS"]:
                if len(logquery["NS"]["$in"]) > 5:
                    logquery["NS"].update({"$in": "[...]"})

        mytqdm = tqdm(total=count, disable=not logging)
        mytqdm.set_description(f"Resolving MongoDB/{self.dbUri}/{cursor.collection.name}: {logquery}")

        result = []
        for data in cursor:
            mytqdm.update(1)
            if idReplace:
                data["_id"] = str(data["_id"])
            result.append(data)

        mytqdm.close()

        return result

    def _has_index(self, collectionName, index: dict):
        indexes = self.db.get_collection(collectionName).list_indexes()
        for i in indexes:
            if i["key"] == index:
                return True
        return False

    def _createIndex(self, collectionName, index: dict):
        if not self._has_index(collectionName, index):
            return self.db.get_collection(collectionName).create_index(index)

    def _manualDestinct(self, collectionName, field: str) -> list[str]:
        self._createIndex(collectionName, {field: 1})

        data = self.db.get_collection(collectionName).aggregate([
            {"$sort": {field: 1}},
            {"$group": {
                "_id": f"${field}"
            }
            }], allowDiskUse=True)
        list_of_lists = list(map(lambda x: x["_id"], data))
        list_of_lists = list(filter(lambda x: type(x) == list, list_of_lists))
        result = list(set(list(itertools.chain.from_iterable(list_of_lists))))
        return result

    def destinct(self, collectionName, field: str) -> list[str]:
        try:
            return self.db.get_collection(collectionName).distinct(field)
        except OperationFailure as e:
            return self._manualDestinct(collectionName, field)
        # return result
