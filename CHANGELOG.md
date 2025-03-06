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
