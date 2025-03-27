
Retry extension enqueues task again if it raised an exception.
```python hl_lines="8 16"
--8<-- "docs/code/extensions/builtin/retry.py"
```

1. You need to add the `Retry` marker and configure amount of retries
2. Don't forget to add the extension into your configuration

!!! warning "Scheduling"
    On retry task is simply added to the queue again, so the following applies:

    - Task may be scheduled on different node
    - Task won't be retried immediately if there are any tasks in front of it in the queue
