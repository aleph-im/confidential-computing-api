from pydantic import BaseModel
import datetime as dt
from typing import Optional
from models.vm import VmState


class VmImageSchema(BaseModel):
    class Config:
        orm_mode = True

    filename: str
    upload_datetime: dt.datetime


class VmImagePostSchema(BaseModel):
    vm_id: str
    filename: str
    upload_datetime: dt.datetime


class VmSchema(BaseModel):
    class Config:
        orm_mode = True

    id: str
    state: VmState
    memory: int
    number_of_cores: int
    sev_policy: Optional[str]
    creation_datetime: dt.datetime
    image: Optional[VmImageSchema]
    ssh_port: Optional[int]


class VmSevInfoSchema(BaseModel):
    api_major: int
    api_minor: int
    build_id: int
    policy: str


class VmStartResponseSchema(BaseModel):
    vm: VmSchema
    sev_info: VmSevInfoSchema
    launch_measure: str
