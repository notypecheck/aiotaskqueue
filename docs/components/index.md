AioTaskQueue consists of multiple components that work together:

### [Broker](./broker/index.md)
Broker communicates with the underlying queue and is needed to send and receive tasks.

### Publisher
Publisher is a common interface for queueing tasks to avoid duplicating logic between
different brokers.

### Result Backend
Result backend is needed to store execution results of task execution.

### Scheduler
Scheduler is needed to schedule periodic tasks

### Worker
Worker listens to a broker and runs tasks.
