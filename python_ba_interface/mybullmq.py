from bullmq import Queue


class BullMQAPI:
    def __init__(self, redis_server: str = "redis", redis_port: int = 6379, queue_name: str = "JobQueue"):
        self.queue = Queue(queue_name, {
            "connection": {
                "host": redis_server,
                "port": redis_port,
            },
            "defaultJobOptions": {
                "attempts": 2,
                "backoff": {
                    "type": 'fixed',
                    "delay": 3900000
                }
            }
        })

    async def add(self, job: dict[str, dict | str]) -> dict:
        data = await self.queue.add(job["name"], job["data"], job["opts"])
        return data
    async def addBulk(self, jobs: list[dict[str,dict | str]]):

        data = await self.queue.addBulk(jobs)
        return data
    async def getStats(self) -> dict:
        my_dict = await self.queue.getJobCounts()
        count = 0
        for i in my_dict.keys():
            count += my_dict[i]
        my_dict.update({"all": count})
        return my_dict

    async def printStats(self):
        print(await self.getStats())

    async def getJobCountByType(self, job_type: str) -> int:
        if not self.isJobType(job_type):
            raise ValueError(f"Job type {job_type} does not exist")

        if job_type == "all":
            return await self.queue.getJobCounts()

        return await self.queue.getJobCountByTypes(job_type)

    def getJobTypes(self) -> list[str]:
        list = self.queue.sanitizeJobTypes()
        list.append("all")
        return list

    def isJobType(self, job_type: str) -> bool:
        return job_type in self.getJobTypes()

    async def getJobsOfType(self, job_type: str) -> list[dict]:
        if not self.isJobType(job_type):
            raise ValueError(f"Job type {job_type} does not exist")

        match job_type:
            case "all":
                return await self.queue.getJobs()
            case "active":
                return await self.queue.getActive()
            case "waiting":
                return await self.queue.getWaiting()
            case "completed":
                return await self.queue.getCompleted()
            case "failed":
                return await self.queue.getFailed()
            case "delayed":
                return await self.queue.getDelayed()
            case "prioritized":
                return await self.queue.getPrioritized()
            case "waiting-children":
                return await self.queue.getWaitingChildren()
            case _:
                raise ValueError(f"Job type {job_type} is not implemented in getJobsOfType")

    async def close(self):
        await self.queue.close()