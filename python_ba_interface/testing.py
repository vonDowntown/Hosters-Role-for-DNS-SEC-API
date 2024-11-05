import asyncio
import json
import itertools
import time

from python_ba_interface import *
from python_ba_interface.mongodb import MongoDB
DNS_TYPES = [
        "A",
        "AAAA",
        "CNAME",
        "DNAME",
        "MX",
        "CAA",
        "CDNSKEY",
        "CDS",
        "CERT",
        "DLV",
        "DNSKEY",
        "DS",
        "IPSECKEY",
        "KEY",
        "KX",
        "NS",
        "NSEC",
        "NSEC3",
        "NSEC3PARAM",
        "OPENPGPKEY",
        "RRSIG",
        "SSHFP",
        "TLSA",
        "TXT",
        "SFP",
        "SRV",
        "NAPTR",
        "AFSDB",
        "SOA",
        "HINFO",
        "RP",
        "LOC",
        "URI",
        "HTTPS",
        "PTR",
        "SMIMEA",
        "SVCB",
        "SSHFP",
        "APL",
        "DHCID",
        "ISDN",
        "NINFO",
        "WKS",
        "SPF",
        "HIP",
        "L32",
        "L64",
        "LP",
        "EUI48",
        "EUI64",
        "NID",
        "CSYNC"
    ]


# from myData import MyRequests, MyAsyncRequests, DNS

def filterfoo(val: [str]):
    count = 0
    for x in ["ns0.transip.net", "ns1.transip.nl", "ns2.transip.eu"]:
        if x in val:
            count += 1
    return count == 3

async def test_registrarfoo():
    api = API("localhost:3030", "bot@test.com", "supersecret", redis_server="localhost")
    dns = api.dns()

    tldr = api.dnsEnumerate()
    foo = dns.get_all()

    data = dns.find({"NS": {"$in": tldr}})
    print(len(foo))
    print(len(data))

    registrar = api.registrar()
    regdata = registrar.find({})
    print(len(regdata))

    doubl = registrar.findDoublicates()
    print(doubl)

    registrar.bulk_delete({})
    await api.close()

async def test_create_jobs():
    api = API("localhost:3030", "bot@test.com", "supersecret", redis_server="localhost")

    await api.fillData(DNS_TYPES, "python_ba_interface/testdata.txt")

    await api.close()

async def test_destinct():
    api = API("localhost:3030", "bot@test.com", "supersecret", redis_server="localhost")
    mongo = api.mongodb

    data = mongo.destinct("dns", "NS")
    vergleich = mongo._manualDestinct("dns", "NS")

    data.sort()
    vergleich.sort()

    print(f"Selbe Ergebnis: {data == vergleich}")


    await api.close()

async def test():
    # await test_create_jobs()
    await test_destinct()
    # myauth = Auth("localhost:3030", "bot@test.com", "supersecret")
    # myrequests = MyRequests("localhost:3030", myauth)
    # myass = MyAsyncRequests(server="localhost:3030", auth=myauth)
    # mydns = DNS("localhost:3030", myrequests, myass)
    #
    # await mydns.resolveIterator(await mydns.get_all())
    # iterator = await mydns.get_all()
    # async for val in iterator:
    #     print(val)

    # await myass.close()


    # print(len(data))
    # with open("python_ba_interface/dns-backend.dns.json", "r") as f:
    #     compare: [dict] = json.load(f)
    # for i in compare:
    #     if "_id" in i:
    #         if type(i["_id"]) is str:
    #             continue
    #         else:
    #             if "$oid" in i["_id"]:
    #                 i.update({"_id": i["_id"]["$oid"]})
    # compareMap = {i["_id"]: i for i in compare}
    # print(f"len compare: {len(list(filter(lambda x: 'NS' in x.keys(), compare)))}")
    #
    # for i in range(1, 0, -1):
    #     data = await dns.bigfind({"NS": {"$in": tldr}}, size=i)
    #     print(f"{i}: {len(data)}")
        # time.sleep(5)

    # dataMap = {i["_id"]: i for i in data}
    # print(f"len data: {len(data)}")
    # notfound = []
    # for i in compareMap.keys():
    #     if i not in dataMap.keys():
    #         notfound.append(i)
    #
    # notfound = list(filter(lambda x: 'NS' in compareMap.get(x).keys(), notfound))
    # listOfMissingNS = list(set(list(itertools.chain.from_iterable(list(map(lambda x: compareMap.get(x).get("NS"), notfound))))))
    # notinTLD = list(filter(lambda x: x not in tldr, listOfMissingNS))
    #
    # print(list(map(lambda x: compareMap.get(x), notfound)))
    #
    # with open("python_ba_interface/test.json", "r") as f:
    #     check = json.load(f)
    # mydict = {i["_id"]: i for i in check}
    # progress = 0
    # for i in notfound:
    #     if i in mydict.keys():
    #         progress += 1
    #
    # print(f"progress: {progress/len(check)}")


    # await api.close()
    # dns_iterator = dns.get_all()
    # async for val in dns_iterator:
    #     print(val)
    #result = await dns.resolveIterator(dns_iterator)
    # iterator = dns.find({"NS": {"$in": ["ns0.transip.net",
    #         "ns1.transip.nl",
    #         "ns2.transip.eu"
    # ]}})
    # result = await dns.resolveIterator(iterator)
    # valwithout  = list(filter(lambda x: not filterfoo(x.get("NS")), result))
    # val = list(filter(lambda x: filterfoo(x.get("NS")), result))
    # print(len(valwithout)+ len(val) == len(result))
    # pass

if __name__ == '__main__':
    # resolver = dns.resolver.Resolver()
    asyncio.run(test())
    foo = 1
