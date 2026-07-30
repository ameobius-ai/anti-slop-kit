Write reference documentation for a REST endpoint POST /v1/cache/purge. It takes
a JSON body with a required array of keys and an optional namespace string. It
returns the number of purged keys. It returns 429 when the caller exceeds ten
calls per minute.
