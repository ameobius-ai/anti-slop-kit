# Jobs API

## Create a job

```
POST /v1/jobs
```

Send a JSON body with these fields:

| Field | Type | Required | Function |
|---|---|---|---|
| `name` | string | yes | Shows the job in the console. Maximum 64 characters. |
| `queue` | string | no | Puts the job in this queue. The default queue is `default`. |
| `payload` | object | yes | Gives the job its input. Maximum 256 KB. |

Example:

```
curl -X POST https://api.example.com/v1/jobs \
  -H 'Authorization: Bearer $TOKEN' \
  -d '{"name": "nightly-export", "payload": {"day": "2026-08-04"}}'
```

## Responses

| Code | Meaning | What to do |
|---|---|---|
| 201 | The server made the job. | Read the job ID from `id`. |
| 400 | A field is missing or too large. | Correct the field named in `error.field`. |
| 429 | You sent more than 100 jobs in 1 minute. | Wait for the number of seconds in the `Retry-After` header. Then send the request again. |
| 503 | The queue is not available. | Send the request again after 5 seconds. Do this a maximum of 3 times. |
