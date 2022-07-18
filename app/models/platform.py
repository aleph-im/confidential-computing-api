from sqlalchemy import Column, Integer

from .db import Base


class FirmwareInfo(Base):
    __tablename__ = "firmware_info"

    api_major = Column(Integer, primary_key=True)   # Note: fake primary key, SQLAlchemy wants one
    api_minor = Column(Integer, nullable=False)
    platform_state = Column(Integer, nullable=False)
    owner = Column(Integer, nullable=False)
    config = Column(Integer, nullable=False)
    build = Column(Integer, nullable=False)
