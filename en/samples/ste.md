# Cache service

A usual cache compares requests by exact text. A small change in wording causes a cache miss. This service compares the meaning of a request with the meaning of cached requests.

If two requests are close in meaning, the service returns the cached answer. You then make fewer model calls. Cost and response time go down.

To set up the cache, open the config file. Change three fields. Obey the security rules of your company.

The server accepts 100 requests each minute for one account. Above this limit, the server rejects the request. The server returns an error. Read the Retry-After header in the response. It gives the exact wait time. Wait for this time. Send the request again.
