import redis
import json
import pickle
import hashlib
from datetime import datetime, timedelta
from config import Config
import logging

logger = logging.getLogger(__name__)

class RedisCache:
    def __init__(self):
        self.redis_client = None
        self.connect()
    
    def connect(self):
        """Conectar a Redis"""
        try:
            self.redis_client = redis.from_url(Config.REDIS_URL)
            # Test connection
            self.redis_client.ping()
            logger.info("✅ Conexión a Redis establecida")
        except Exception as e:
            logger.error(f"❌ Error conectando a Redis: {e}")
            self.redis_client = None
    
    def _generate_key(self, prefix, *args):
        """Generar clave única para cache"""
        key_parts = [prefix] + [str(arg) for arg in args]
        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def set_cache(self, key, data, ttl=None):
        """Guardar datos en cache"""
        if not self.redis_client:
            return False
        
        try:
            if isinstance(data, (dict, list)):
                serialized_data = json.dumps(data, default=str)
            else:
                serialized_data = pickle.dumps(data)
            
            ttl = ttl or Config.CACHE_TTL
            self.redis_client.setex(key, ttl, serialized_data)
            return True
        except Exception as e:
            logger.error(f"❌ Error guardando en cache: {e}")
            return False
    
    def get_cache(self, key, as_json=True):
        """Obtener datos del cache"""
        if not self.redis_client:
            return None
        
        try:
            data = self.redis_client.get(key)
            if data:
                if as_json:
                    return json.loads(data)
                else:
                    return pickle.loads(data)
            return None
        except Exception as e:
            logger.error(f"❌ Error obteniendo de cache: {e}")
            return None
    
    def delete_cache(self, key):
        """Eliminar clave del cache"""
        if self.redis_client:
            self.redis_client.delete(key)
    
    def clear_pattern(self, pattern):
        """Eliminar todas las claves que coincidan con un patrón"""
        if self.redis_client:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
    
    # Métodos específicos para recomendaciones
    def cache_movie_recommendations(self, movie_id, method, recommendations):
        """Cache de recomendaciones de películas"""
        key = self._generate_key("rec", movie_id, method)
        return self.set_cache(key, recommendations, ttl=1800)  # 30 minutos
    
    def get_cached_recommendations(self, movie_id, method):
        """Obtener recomendaciones cacheadas"""
        key = self._generate_key("rec", movie_id, method)
        return self.get_cache(key)
    
    def cache_popular_movies(self, movies):
        """Cache de películas populares"""
        key = "popular_movies"
        return self.set_cache(key, movies, ttl=3600)  # 1 hora
    
    def get_cached_popular_movies(self):
        """Obtener películas populares cacheadas"""
        return self.get_cache("popular_movies")
    
    def cache_search_results(self, query, results):
        """Cache de resultados de búsqueda"""
        key = self._generate_key("search", query)
        return self.set_cache(key, results, ttl=900)  # 15 minutos
    
    def get_cached_search_results(self, query):
        """Obtener resultados de búsqueda cacheados"""
        key = self._generate_key("search", query)
        return self.get_cache(key)
    
    def cache_genre_movies(self, genre, movies):
        """Cache de películas por género"""
        key = self._generate_key("genre", genre)
        return self.set_cache(key, movies, ttl=1800)  # 30 minutos
    
    def get_cached_genre_movies(self, genre):
        """Obtener películas por género cacheadas"""
        key = self._generate_key("genre", genre)
        return self.get_cache(key)
    
    def invalidate_recommendations(self, movie_id=None):
        """Invalidar cache de recomendaciones"""
        if movie_id:
            pattern = f"rec:{movie_id}:*"
        else:
            pattern = "rec:*"
        self.clear_pattern(pattern)
    
    def get_cache_stats(self):
        """Obtener estadísticas del cache"""
        if not self.redis_client:
            return {}
        
        try:
            info = self.redis_client.info()
            return {
                'connected_clients': info.get('connected_clients', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'total_commands_processed': info.get('total_commands_processed', 0)
            }
        except Exception as e:
            logger.error(f"❌ Error obteniendo stats de Redis: {e}")
            return {}

# Instancia global
redis_cache = RedisCache() 