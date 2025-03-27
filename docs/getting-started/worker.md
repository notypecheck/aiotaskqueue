Worker would read queue in your broker and execute all tasks it reads from it.

To create a worker you need:

- [Broker][aiotaskqueue.broker.abc.Broker] instance
- [Configuration][aiotaskqueue.Configuration]
- Task Router or list of your tasks.
- (Optionally) a [result backend][aiotaskqueue.result.abc.ResultBackend] if you 
want to store execution results of your tasks.

```python
--8<-- "docs/code/getting_started/worker.py"
```
