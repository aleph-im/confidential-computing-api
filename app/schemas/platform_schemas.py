from pydantic import BaseModel


class FirmwareInfoSchema(BaseModel):
    class Config:
        orm_mode = True

    api_major: int
    api_minor: int
    build: int
