from tldextract import tldextract

from .mongodb import MongoDB
from .mybullmq import BullMQAPI
from .myData import *
from .auth import Auth
from .fillData  import main as filldatamain
from .myrequests import MyRequests, MyAsyncRequests
import asyncio


class API:
    def __init__(self, server_url: str, username: str, password: str, mongodbConStr: str = "mongodb://localhost:27017/", redis_server: str = "redis"):
        self.server_url = server_url
        self.auth = Auth(server_url, username, password)
        self.myrequests = MyRequests(server_url, self.auth)
        self.myasyncrequests = MyAsyncRequests(server_url, self.auth)
        self.mongodb = MongoDB(mongodbConStr)
        self.mongodb.ping()
        self.mydns = DNS(server_url, self.myrequests, self.myasyncrequests, self.mongodb)
        self.myregistrar = Registrar_Class(server_url, self.myrequests, self.myasyncrequests, self.mongodb)
        self.mybullmq = BullMQAPI(redis_server=redis_server)
        # self.myfillData = FillData(server_url, self.myrequests, self.myasyncrequests)

    def dns(self) -> DNS:
        return self.mydns

    def registrar(self) -> Registrar_Class:
        return self.myregistrar

    async def fillData(self, dnstypes: list[str], infile: str):
        await filldatamain(self.server_url, self.mybullmq, dnstypes, infile )

    def dnsEnumerate(self) -> list[str]:
        # data = self.myrequests.get(f'http://{self.server_url}/dns-enumerate', {})['NS']
        data = self.mongodb.destinct("dns", "NS")
        resultMap = dict()
        for i in data:
            tld = tldextract.extract(i)
            if tld.registered_domain not in resultMap.keys():
                resultMap.update({tld.registered_domain: []})
            resultMap[tld.registered_domain].append(i)

        result = []
        for i in sorted(resultMap.keys()):
            values = sorted(resultMap[i])
            result.extend(values)
        return result



    def bullmq(self) -> BullMQAPI:
        return self.mybullmq

    async def close(self):
        await self.mybullmq.close()
        await self.myasyncrequests.close()
