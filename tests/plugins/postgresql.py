from collections.abc import AsyncIterator

import pytest
from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer  # type: ignore[import-untyped]

from tests.models import (
    Base,
    PostgresBrokerTask,
    PostgresResultTask,
)


@pytest.fixture(scope="session")
async def postgres_container() -> AsyncIterator[PostgresContainer]:
    with PostgresContainer(image="postgres:16", driver="asyncpg") as container:
        yield container


@pytest.fixture(scope="session")
async def sqlalchemy_engine(
    postgres_container: PostgresContainer,
) -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(postgres_container.get_connection_url())
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def _sqlalchemy_run_migration(sqlalchemy_engine: AsyncEngine) -> None:
    async with sqlalchemy_engine.begin() as connection:
        await connection.execute(text("SET timezone = 'UTC'"))
        await connection.run_sync(Base.metadata.create_all)


@pytest.fixture(scope="session")
async def _sqlalchemy_session_maker(
    sqlalchemy_engine: AsyncEngine,
    _sqlalchemy_run_migration: None,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(sqlalchemy_engine)


@pytest.fixture
async def sqlalchemy_session_maker(
    _sqlalchemy_session_maker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    yield _sqlalchemy_session_maker

    async with _sqlalchemy_session_maker.begin() as session:
        await session.execute(delete(PostgresBrokerTask))
        await session.execute(delete(PostgresResultTask))


@pytest.fixture
async def sqlalchemy_session(
    sqlalchemy_session_maker: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with sqlalchemy_session_maker.begin() as session:
        yield session
