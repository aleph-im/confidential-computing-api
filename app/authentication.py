import secrets
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from models.db import get_db_session
from models.users import User
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from passlib.context import CryptContext

security = HTTPBasic()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def get_user(session: Session, username: str) -> Optional[User]:
    users = (
        await session.execute(select(User).where(User.username == username))
    ).one_or_none()
    return users[0] if users is not None else None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


async def get_current_user(
    credentials: HTTPBasicCredentials = Depends(security),
    session: Session = Depends(get_db_session),
):
    user = await get_user(session, credentials.username)
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    return user
