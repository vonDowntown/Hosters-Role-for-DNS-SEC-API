import argparse
import asyncio

import tldextract
from aiohttp import client_exceptions

from python_ba_interface import BullMQAPI, Auth
from .mytypes import Percentile, AuthDict
from .myrequests import MyAsyncRequests
from tqdm import tqdm



class FillData:
    def __init__(self, server_url: str, my_bullMQ: BullMQAPI):
        self.mybullMQ = my_bullMQ
        self.url = f'http://{server_url}/jobs'

    async def send_bulk(self, domains: list[str], record: str):
        data = self.__build_bulk(domains, record)
        formatedData = self.__build_bullMQ_Jobs(data)
        return await self.mybullMQ.addBulk(formatedData)

    def createBullMQJobs(self, domains: list[str], record: str):
       return self.__build_bullMQ_Jobs(self.__build_bulk(domains, record))
    def createHTTPJobs(self, domains: list[str], record: str):
        return self.__build_bulk(domains, record)


    def __build_bullMQ_Jobs(self, jobs: list[dict]) -> list[dict]:
        return list(map(self.__build_bullMQ_Job, jobs))

    def __build_bullMQ_Job(self, data: dict) -> dict:
        return {
            'name': f'{data["domain"]} {data["recordType"]}',
            'data': data,
            'opts': {
                'jobId': f'{data["domain"]} {data["recordType"]}'
            }
        }

    def __build_job_data(self, domain: str, dnstype: str) -> dict:
        return {
            'domain': domain, 'recordType': dnstype
        }

    def __build_jobs_data(self, jobs: list[tuple]) -> list[dict]:
        return list(map(lambda x: self.__build_job_data(x[0], x[1]), jobs))

    def __build_bulk(self, domains: list[str], record: str) -> list[dict]:
        prepare = map(lambda x: (x, record), domains)
        return self.__build_jobs_data(prepare)


def checkfordomain(domain: str) -> str:
    ext = tldextract.extract(domain)
    len = ext.__len__()
    return '.'.join(ext[1:len])

def slize_Array(array: list, size: int) -> list[list]:
    result = []
    for i in range(0, len(array), size):
        result.append(array[i:i + size])
    return result

async def sentAndUpdate(myasync: MyAsyncRequests, fill_data: FillData, mytqdm: tqdm, job: list[str], type: str):

    data = fill_data.createHTTPJobs(job, type)
    try:
        await myasync.post(f'http://localhost:3030/jobs', data)
    except client_exceptions.ServerDisconnectedError and client_exceptions.ClientConnectionError:
        new_con = MyAsyncRequests("localhost:3030", myasync.auth)
        await new_con.post(f'http://localhost:3030/jobs', data)
        await new_con.close()

    mytqdm.update(len(job))

async def main(url: str, bullMQ: BullMQAPI, dnstypes: list[str], infile: str):
    fill_data = FillData(url, bullMQ)
    errors = []
    bulk = []

    with open(infile) as file:
        data = file.readlines()
    data = list(filter(lambda x: x != "\n", data))
    data = list(map(lambda x: x.strip(), data))

    if "NS" in dnstypes:
        sortedDNS = []
        sortedDNS.append("NS")
        sortedDNS.extend(sorted(list(filter(lambda x: x != "NS", dnstypes))))
    else:
        sortedDNS = sorted(dnstypes)
    print(f"dnsTypes: {sortedDNS}")

    jobs: list[list] = slize_Array(data, 5000)
    mytqdm = tqdm(total=len(data)*len(sortedDNS))

    for index, type in enumerate(sortedDNS, start=1):
        mytqdm.set_description(f"Sending {type}({index} of {len(sortedDNS)})")
        server = "localhost:3030"
        username = "bot@test.com"
        password = "supersecret"
        myasync = MyAsyncRequests("localhost:3030", Auth(server, username, password, False))

        tasks = [sentAndUpdate(myasync, fill_data, mytqdm, job, type) for job in jobs]
        await asyncio.gather(*tasks)

        await myasync.close()

    # mytqdm = tqdm(total=len(data) * len(sortedDNS))
    # for index, type in enumerate(sortedDNS, start=1):
    #     mytqdm.set_description(f"Sending {type}({index} of {len(sortedDNS)})")
    #     jobs = fill_data.createJobs(data, type)
    #     for job in jobs:
    #         result = await bullMQ.add(job)
    #         mytqdm.update(1)





if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='sends')
    parser.add_argument('type')
    parser.add_argument('inputFilename')
    parser.add_argument('-v', '--verbosity')
    args = parser.parse_args()

    asyncio.run(main([args.type], args.inputFilename))
