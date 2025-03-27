import pytest
from aiotaskqueue.router import TaskRouter, task


@task(name="name")
async def task_1() -> None:
    pass


@task(name="name")
async def task_2() -> None:
    pass


@pytest.fixture
def router() -> TaskRouter:
    return TaskRouter()


async def test_task_decorator(router: TaskRouter) -> None:
    name = "task-name"

    async def func() -> None:
        pass

    router.task(name)(func)

    assert router.tasks[name].func is func
    assert router.tasks[name].name == name


async def test_include(router: TaskRouter) -> None:
    router_to_include = TaskRouter()

    @router_to_include.task(name="name")
    async def new_task() -> None:
        pass

    router.include(router_to_include)
    assert router.tasks == {"name": new_task}


async def test_include_raises_error_if_tasks_have_duplicate_names() -> None:
    router = TaskRouter((task_1,))
    router_2 = TaskRouter((task_2,))

    with pytest.raises(ValueError, match="Task .* already registered"):
        router.include(router_2)

    # Should allow if it's the same task
    router_2 = TaskRouter((task_1,))
    router.include(router_2)
