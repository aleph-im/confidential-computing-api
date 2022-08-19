from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from toolkit.db_connection import get_db_url


engine = create_async_engine(get_db_url(), future=True, echo=True)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()


async def get_db_session():
    async with async_session() as session:
        async with session.begin():
            yield session
            await session.commit()
