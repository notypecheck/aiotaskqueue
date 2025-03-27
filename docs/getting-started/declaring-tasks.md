
Tasks are what you'll be scheduling and what would be executed by the worker.

To declare a task you simply need to decorate a function with `task` decorator:

```python
--8<-- "docs/code/getting-started/task_example.py"
```


## TaskRouter
Task router is a simpler way to create a collection of tasks:
```python
--8<-- "docs/code/getting-started/task_router_example.py"
```


## Markers
Different extensions could provide markers to add metadata to your task 
definitions, for example to add retries to your tasks you could use `Retry` marker:

```python
--8<-- "docs/code/getting-started/task_markers.py"
```

!!! tip "Retry Extension"
    In order for this specific example to work you need to add `RetryExtension`
    to your [Configuration][aiotaskqueue.Configuration]
