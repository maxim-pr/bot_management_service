import asyncio

from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument

from schemas import User, UserWithoutId, Bot, Bots


class Database:
    def __init__(self):
        self._client = None
        self._db = None
        self._users_collection = None

    async def connect(self, db_url: str, db_name: str, users_collection_name: str):
        self._client = AsyncIOMotorClient(host=db_url, io_loop=asyncio.get_event_loop())
        self._db = self._client[db_name]
        self._users_collection = self._db[users_collection_name]

    async def add_user(self, user: UserWithoutId) -> str:
        result = await self._users_collection.insert_one(user.dict())
        return str(result.inserted_id)

    async def get_user_by_id(self, user_id: str) -> User:
        user = await self._users_collection.find_one({"_id": ObjectId(user_id)})
        if user is None:
            raise KeyError("Invalid user")
        return User(**user, user_id=str(user["_id"]))

    async def get_user_by_username(self, username: str) -> User:
        user = await self._users_collection.find_one({"username": username})
        if user is None:
            raise KeyError("Invalid user")
        return User(**user, user_id=str(user["_id"]))

    async def exists(self, username: str):
        user = await self._users_collection.find_one({"username": username})
        if user is None:
            return False
        return True

    async def add_bot(self, user_id: str, bot: Bot) -> Bots:
        # check bot token for duplicates in database
        async for user in self._users_collection.find({}, projection={"_id": False,
                                                                      "username": False,
                                                                      "first_name": False,
                                                                      "last_name": False,
                                                                      "hashed_password": False}):
            for user_bot in user["bots"]:
                if bot.bot_token == user_bot["bot_token"]:
                    raise KeyError("This bot token is already registered")

        user = await self._users_collection.find_one_and_update({"_id": ObjectId(user_id)},
                                                                {"$push": {"bots": bot.dict()}},
                                                                return_document=ReturnDocument.AFTER)
        if user is None:
            raise KeyError("Invalid user")
        return Bots(bots=user["bots"])

    async def delete_bot(self, user_id: str, bot_token: str) -> Bots:
        # get user data before deletion
        user_before = await self._users_collection.find_one({"_id": ObjectId(user_id)})
        if user_before is None:
            raise KeyError("Invalid user")

        # apply deletion
        user_after = await self._users_collection.find_one_and_update({"_id": ObjectId(user_id)},
                                                                {"$pull": {"bots": {"bot_token": bot_token}}},
                                                                return_document=ReturnDocument.AFTER)

        if len(user_before["bots"]) == len(user_after["bots"]):
            raise KeyError("Bot token doesn't belong to the user")

        return Bots(bots=user_after["bots"])

    async def get_user_bots(self, user_id: str) -> Bots:
        user = await self._users_collection.find_one({"_id": ObjectId(user_id)})
        if user is None:
            raise KeyError("Invalid user")
        return Bots(bots=user["bots"])

    async def get_users(self):
        async for user in self._users_collection.find({}, projection={"hashed_password": False}):
            yield user
