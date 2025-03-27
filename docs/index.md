---
hide:
  - navigation
---

# AioTaskQueue

AioTaskQueue is a modular task queue similar to 
[celery](https://docs.celeryq.dev/en/stable/),
[arq](https://github.com/python-arq/arq),
[taskiq](https://taskiq-python.github.io/) and alike.

## Features
### Fully Typed
Tasks created with @task decorator are fully typed, 
so you could catch errors such as passing wrong arguments to tasks early.

### Modularity
All of the components are loosely coupled, you're free to mix and match them however you want.

### Serialization Backends
Using different serialization backends you can serialize models from [pydantic](https://docs.pydantic.dev/latest/), 
[msgspec](https://jcristharif.com/msgspec/) and integrate any other library the same way.
