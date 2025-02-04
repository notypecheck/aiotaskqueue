from datetime import datetime
from typing import cast

import pytest
from _pytest.fixtures import SubRequest
from asyncqueue._util import utc_now

pytest_plugins = [
    "anyio",
    "tests.fixtures",
]


@pytest.fixture(scope="session", autouse=True, params=["asyncio"])
def anyio_backend(request: SubRequest) -> str:
    return cast(str, request.param)


@pytest.fixture
def now() -> datetime:
    return utc_now()
