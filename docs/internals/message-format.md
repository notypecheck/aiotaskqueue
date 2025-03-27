
All tasks are serialized by [TaskRecord][aiotaskqueue.serialization.TaskRecord] 
msgspec model using json format

::: aiotaskqueue.serialization.TaskRecord
    options:
        merge_init_into_class: false
        show_source: true

Since parameters can be encoded using different serialization backends
args, kwargs and result values are stored as a tuple (array in json) with
serialization backend name and encoded value.
```json
{
  "id":"90ca5786-02c7-4320-a8d2-7db161f91955",
  "task_name":"task-name",
  "enqueue_time":"2025-03-27T09:59:25.185591Z",
  "args":[
    ["msgspec","1"],
    ["msgspec","2"],
    ["msgspec","3"]
  ],
  "kwargs": {
    "pydantic_arg":["pydantic","{\"a\":42,\"b\":\"str\"}"],
    "msgspec_arg":["msgspec","{\"a\":42,\"b\":\"str\"}"]
  },
  "meta":{
    "retry_count": 1
  }
}
```
