import dataclasses
from datetime import datetime
from typing import List, Optional
import bson


def timestamp_factory() -> bson.Timestamp:
    return bson.Timestamp(datetime.now(), 0)


@dataclasses.dataclass
class VolumeMapping:
    source: str
    destination: str


@dataclasses.dataclass
class Build:
    output: str
    status: str = dataclasses.field(default_factory=lambda: "FINISHED")
    started_at: bson.Timestamp = dataclasses.field(default_factory=timestamp_factory)
    built_at: Optional[bson.Timestamp] = dataclasses.field(default=None)
    _id: bson.ObjectId = dataclasses.field(default_factory=bson.ObjectId)


@dataclasses.dataclass
class RepositoryConfiguration:
    repository_url: str
    private_key: str
    builds: List["Build"] = dataclasses.field(default_factory=lambda: [])
    volume_mappings: List["VolumeMapping"] = dataclasses.field(
        default_factory=lambda: []
    )
    created_at: bson.Timestamp = dataclasses.field(default_factory=timestamp_factory)
    last_ran_at: Optional[bson.Timestamp] = dataclasses.field(default=None)
    _id: bson.ObjectId = dataclasses.field(default_factory=bson.ObjectId)


@dataclasses.dataclass
class User:
    email: str
    password: bytes
    repository_configurations: List["RepositoryConfiguration"] = dataclasses.field(
        default_factory=lambda: []
    )
    _id: bson.ObjectId = dataclasses.field(default_factory=bson.ObjectId)
