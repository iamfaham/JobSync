import json, os
CACHE_FILE = "agent/cache.json"

def load_cache():
    if not os.path.exists(CACHE_FILE):
        return set()
    with open(CACHE_FILE, "r") as f:
        return set(json.load(f))

def save_cache(ids):
    with open(CACHE_FILE, "w") as f:
        json.dump(list(ids), f)
