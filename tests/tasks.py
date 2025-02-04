from asyncqueue import TaskParams, task


@task(TaskParams(name="test-task"))
async def noop_task() -> None:
    pass


@task(TaskParams(name="task-with-params"))
async def task_with_params(a: int, b: str) -> None:
    pass
