import dataclasses
from typing import Optional
import pymongo
import os
import dotenv
import pymongo.database
import redis
import data
import git

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
        _REDIS_CLIENT = redis.Redis.from_url(url=os.environ["REDIS_URL"])

    return _REDIS_CLIENT


def get_mongo_collection(collection: str) -> pymongo.database.Collection:
    return (
        get_mongo_client()
        .get_database(os.environ["MONGO_DB"])
        .get_collection(collection)
    )


def seed() -> None:
    import bcrypt
    import string
    import random

    existing_admin = get_mongo_collection("users").find_one(
        {"email": "root@vulnb0x.xyz"}
    )

    if not existing_admin:
        with open("/var/data/privkey", "r") as f:
            repo_configuration = data.RepositoryConfiguration(
                repository_url="git@github.com:AlphaZoneR/softsec.git",
                private_key=f.read(),
            )

        repo_fullpath = os.path.join(
            os.environ["REPOS_PATH"], str(repo_configuration._id)
        )

        git_interface = git.Git()
        git_interface.update_environment(GIT_SSH_COMMAND=f"ssh -i /var/data/privkey")
        git.Repo._clone(
            git_interface,
            "git@github.com:AlphaZoneR/softsec.git",
            repo_fullpath,
            git.GitCmdObjectDB,
        )

        password = ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(12)])
        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        admin_user = data.User(email="root@vulnb0x.xyz", password=hashed_pw)
        admin_user.repository_configurations.append(repo_configuration)

        get_mongo_collection("users").insert_one(dataclasses.asdict(admin_user))
