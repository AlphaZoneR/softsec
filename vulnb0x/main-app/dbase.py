from typing import Optional
import pymongo
import os
import dotenv
import pymongo.database
import redis

dotenv.load_dotenv()

_MONGO_CLIENT: Optional[pymongo.MongoClient] = None
_REDIS_CLIENT: Optional[redis.Redis] = None

def get_mongo_client() -> pymongo.MongoClient:
    global _MONGO_CLIENT

    if not _MONGO_CLIENT:
        _MONGO_CLIENT = pymongo.MongoClient(os.environ["MONGO_URL"])

    return _MONGO_CLIENT

def get_redis_client() -> redis.Redis:
    global _REDIS_CLIENT

    if not _REDIS_CLIENT:
        _REDIS_CLIENT = redis.Redis.from_url(url=os.environ['REDIS_URL'])

    return _REDIS_CLIENT

def get_mongo_collection(collection: str) -> pymongo.database.Collection:
    return (
        get_mongo_client()
        .get_database(os.environ["MONGO_DB"])
        .get_collection(collection)
    )
