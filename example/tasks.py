from asyncqueue._util import utc_now
from asyncqueue.router import TaskRouter
from asyncqueue.scheduler import crontab
from asyncqueue.task import TaskParams

router = TaskRouter()


@router.task(
    TaskParams(
        name="email-send",
    )
)
async def send_email(message: str, address: str) -> str:
    return message


@router.task(
    TaskParams(
        name="periodic-task",
        schedule=crontab("* * * * *"),
    )
)
async def periodic_task() -> str:
    print("Periodic task", utc_now())
