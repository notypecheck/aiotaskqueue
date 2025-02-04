from asyncqueue import TaskParams, TaskRouter
from asyncqueue._util import utc_now
from asyncqueue.scheduler import crontab
from msgspec import Struct
from pydantic import BaseModel

router = TaskRouter()
n = 0


class Person(Struct):
    id: int
    name: str


class Email(BaseModel):
    text: str
    cc: list[str]


@router.task(
    TaskParams(
        name="email-send",
    )
)
async def send_email(person: Person, email: Email) -> str:
    return email.text + person.name


@router.task(
    TaskParams(
        name="periodic-task",
        schedule=crontab("* * * * *"),
    )
)
async def periodic_task() -> str:
    print("Periodic task", utc_now())  # noqa: T201
    return str(utc_now())
