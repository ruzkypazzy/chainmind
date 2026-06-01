"""Caching for repeated queries"""

class CacheManager:
    def __init__(self, ttl: int = 300):
        self.cache = {}
        self.ttl = ttl
        
    def get(self, key: str) -> any:
        return self.cache.get(key)
        
    def set(self, key: str, value: any):
        self.cache[key] = value
