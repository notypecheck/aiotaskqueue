from asyncqueue import TaskParams, TaskRouter
from asyncqueue._util import utc_now
from asyncqueue.scheduler import crontab

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
    return str(utc_now())
