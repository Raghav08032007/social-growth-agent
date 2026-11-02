"""Redis server-time token bucket: one atomic script per account + action."""

import hashlib

SCRIPT = """
local t = redis.call('TIME')
local now = tonumber(t[1]) + tonumber(t[2]) / 1000000
local capacity = tonumber(ARGV[1])
local rate = tonumber(ARGV[2])
local old = redis.call('HMGET', KEYS[1], 'tokens', 'time')
local tokens = tonumber(old[1]) or capacity
local prior = tonumber(old[2]) or now
tokens = math.min(capacity, tokens + math.max(0, now-prior) * rate)
local allowed = 0
if tokens >= 1 then tokens = tokens - 1; allowed = 1 end
redis.call('HSET', KEYS[1], 'tokens', tokens, 'time', now)
redis.call('EXPIRE', KEYS[1], math.ceil(capacity / rate) + 1)
return allowed
"""


def acquire(redis, workspace, account, endpoint, capacity=10, refill_per_second=1):
    if capacity < 1 or refill_per_second <= 0:
        raise ValueError("Positive rate and capacity required")
    identity = "\0".join([workspace, account, endpoint]).encode()
    key = "rate:" + hashlib.sha256(identity).hexdigest()
    return bool(redis.eval(SCRIPT, 1, key, capacity, refill_per_second))
