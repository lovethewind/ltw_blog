import asyncio
import datetime

from bson import ObjectId
from pydantic import BaseModel, Field, field_validator
from motor.motor_asyncio import AsyncIOMotorClient


class UserInfo(BaseModel):
    id: ObjectId = Field(alias="_id")
    username: str
    password: str
    age: int
    create_time: datetime.datetime

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    @field_validator("id", mode="before")
    def validate_id(cls, v):
        return str(v)


class MongoUtil:

    def __init__(self):
        self.client = AsyncIOMotorClient(username="mongoadmin", password="secret")

    def close(self):
        self.client.close()


async def main():
    mongo_util = MongoUtil()
    # uu = UserInfo(username="test", password="123456", age=18, create_time=datetime.datetime.now())
    # mongo_util.client.test.user.insert_one(uu.model_dump())
    tt = await mongo_util.client.test.user.find_one({"username": "test"})
    tt = UserInfo(**tt)
    print(tt)


if __name__ == '__main__':
    asyncio.run(main())
