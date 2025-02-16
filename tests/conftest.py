import pkgutil
from datetime import datetime
from typing import cast

import pytest
from _pytest.fixtures import SubRequest
from asyncqueue._util import utc_now

import tests.plugins

pytest_plugins = [
    "anyio",
    *(
        mod.name
        for mod in pkgutil.walk_packages(
            tests.plugins.__path__,
            prefix="tests.plugins.",
        )
        if not mod.ispkg
    ),
]


@pytest.fixture(scope="session", autouse=True, params=["asyncio"])
def anyio_backend(request: SubRequest) -> str:
    return cast(str, request.param)


@pytest.fixture
def now() -> datetime:
    return utc_now()
