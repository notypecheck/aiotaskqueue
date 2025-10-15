## 0.14.0 (2025-10-15)

### Feat

- **redis**: acquire lock when trying to perform maintenance tasks
- scheduled task broker
- sqlalchemy broker & result backenC

### Refactor

- move serialize_task call into Publisher.enqueue

## 0.13.1 (2025-05-23)

### Fix

- convert TimeLimit into a dataclass

## 0.13.0 (2025-05-23)

### Feat

- add built-in TimeLimitExtension

## 0.12.0 (2025-05-14)

### Refactor

- internal task management

## 0.11.0 (2025-05-12)

### Feat

- add state to ExecutionContext

## 0.10.0 (2025-04-09)

### Feat

- add OnTaskExecution extension (aka middleware)

## 0.9.0 (2025-03-27)

### Feat

- **redis**: automatically trim stream
- allow passing parameters directly into `@task` decorator

## 0.8.0 (2025-03-24)

### Feat

- add retry extension

## 0.7.0 (2025-03-09)

### Feat

- wrap ResultBackend.get return value into Some[] container type to differentiate between missing and None values
- add ResultBackend.get method
- allow enqueueing tasks with specific id
- **result-backend**: allow configuring result key in Configuration

### Fix

- skip tasks in "sequential" if there's a result present already
- **scheduler**: don't call OnScheduleExtension when initializing tasks on scheduler startup

## 0.6.0 (2025-03-06)

### Feat

- allow configuring result backend TTL

## 0.5.0 (2025-03-06)

### Feat

- **worker**: add shutdown deadline

## 0.4.0 (2025-03-05)

### Feat

- **worker**: add OnTaskException and OnTaskCompletion extensions
- **scheduler**: add OnScheduleExtension

## 0.3.0 (2025-03-05)

### Feat

- add built-in "sequential" task to run tasks in sequence
- allow injecting "Publisher" instances into tasks

## 0.2.0 (2025-03-04)

### Feat

- **scheduler**: allow passing TaskRouter instead of a list of tasks
- add redis result backend
- **publisher**: add default serialization backend to serialization backends by default

### Fix

- python 3.10-3.11 compatability
- **redis**: reclaim owned tasks in background
- change project name

### Refactor

- rename projec to "aiotaskqueue"
