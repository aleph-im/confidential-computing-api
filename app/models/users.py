from .db import Base
from sqlalchemy import Column, DateTime, String, func


class User(Base):
    __tablename__ = "users"

    username = Column(String, primary_key=True)
    hashed_password = Column(String, nullable=False)
    creation_datetime = Column(DateTime, nullable=False, server_default=func.now())
