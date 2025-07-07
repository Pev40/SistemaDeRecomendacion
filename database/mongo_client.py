import asyncio
import pandas as pd
import polars as pl
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import os
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoDBManager:
    def __init__(self):
        self.client = None
        self.db = None
        self.async_client = None
        self.async_db = None
        
    def connect(self):
        """Conexión síncrona para migración de datos"""
        try:
            self.client = MongoClient(Config.MONGO_URI)
            self.db = self.client[Config.MONGO_DB]
            logger.info("✅ Conexión a MongoDB establecida")
            return True
        except Exception as e:
            logger.error(f"❌ Error conectando a MongoDB: {e}")
            return False
    
    async def async_connect(self):
        """Conexión asíncrona para operaciones en tiempo real"""
        try:
            self.async_client = AsyncIOMotorClient(Config.MONGO_URI)
            self.async_db = self.async_client[Config.MONGO_DB]
            logger.info("✅ Conexión asíncrona a MongoDB establecida")
            return True
        except Exception as e:
            logger.error(f"❌ Error conectando a MongoDB async: {e}")
            return False
    
    def create_indexes(self):
        """Crear índices optimizados para consultas rápidas"""
        try:
            # Índices para películas
            self.db.movies.create_index([("movieId", 1)], unique=True)
            self.db.movies.create_index([("title", "text")])
            self.db.movies.create_index([("genres", 1)])
            self.db.movies.create_index([("year", 1)])
            
            # Índices para ratings
            self.db.ratings.create_index([("userId", 1), ("movieId", 1)])
            self.db.ratings.create_index([("movieId", 1), ("rating", -1)])
            self.db.ratings.create_index([("userId", 1), ("rating", -1)])
            
            # Índices para tags
            self.db.tags.create_index([("movieId", 1)])
            self.db.tags.create_index([("tag", 1)])
            
            logger.info("✅ Índices creados exitosamente")
        except Exception as e:
            logger.error(f"❌ Error creando índices: {e}")
    
    def migrate_csv_to_mongodb(self, data_folder='data'):
        """Migrar datos CSV a MongoDB"""
        try:
            logger.info("🔄 Iniciando migración de datos...")
            
            # Migrar películas
            movies_df = pl.read_csv(os.path.join(data_folder, 'movies.csv'))
            movies_data = movies_df.to_dicts()
            
            # Procesar películas en lotes
            batch_size = Config.BATCH_SIZE
            for i in range(0, len(movies_data), batch_size):
                batch = movies_data[i:i + batch_size]
                try:
                    self.db.movies.insert_many(batch, ordered=False)
                except DuplicateKeyError:
                    # Si hay duplicados, insertar uno por uno
                    for movie in batch:
                        try:
                            self.db.movies.insert_one(movie)
                        except DuplicateKeyError:
                            continue
            
            logger.info(f"✅ Películas migradas: {len(movies_data)}")
            
            # Migrar ratings
            ratings_df = pl.read_csv(os.path.join(data_folder, 'ratings.csv'))
            ratings_data = ratings_df.to_dicts()
            
            for i in range(0, len(ratings_data), batch_size):
                batch = ratings_data[i:i + batch_size]
                self.db.ratings.insert_many(batch, ordered=False)
            
            logger.info(f"✅ Ratings migrados: {len(ratings_data)}")
            
            # Migrar tags
            tags_df = pl.read_csv(os.path.join(data_folder, 'tags.csv'))
            tags_data = tags_df.to_dicts()
            
            for i in range(0, len(tags_data), batch_size):
                batch = tags_data[i:i + batch_size]
                self.db.tags.insert_many(batch, ordered=False)
            
            logger.info(f"✅ Tags migrados: {len(tags_data)}")
            
            # Migrar links
            links_df = pl.read_csv(os.path.join(data_folder, 'links.csv'))
            links_data = links_df.to_dicts()
            
            for i in range(0, len(links_data), batch_size):
                batch = links_data[i:i + batch_size]
                self.db.links.insert_many(batch, ordered=False)
            
            logger.info(f"✅ Links migrados: {len(links_data)}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en migración: {e}")
            return False
    
    async def get_movies_batch(self, skip=0, limit=100, filters=None):
        """Obtener películas en lotes con filtros"""
        query = {}
        if filters:
            if filters.get('genre'):
                query['genres'] = {'$regex': filters['genre'], '$options': 'i'}
            if filters.get('year'):
                query['year'] = filters['year']
            if filters.get('search'):
                query['$text'] = {'$search': filters['search']}
        
        cursor = self.async_db.movies.find(query).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_movie_by_id(self, movie_id):
        """Obtener película por ID"""
        return await self.async_db.movies.find_one({'movieId': movie_id})
    
    async def get_ratings_by_movie(self, movie_id, limit=100):
        """Obtener ratings de una película"""
        cursor = self.async_db.ratings.find({'movieId': movie_id}).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_user_ratings(self, user_id, limit=100):
        """Obtener ratings de un usuario"""
        cursor = self.async_db.ratings.find({'userId': user_id}).limit(limit)
        return await cursor.to_list(length=limit)
    
    async def get_popular_movies(self, limit=50, min_ratings=10):
        """Obtener películas populares"""
        pipeline = [
            {
                '$group': {
                    '_id': '$movieId',
                    'avg_rating': {'$avg': '$rating'},
                    'count': {'$sum': 1}
                }
            },
            {
                '$match': {
                    'count': {'$gte': min_ratings}
                }
            },
            {
                '$sort': {'avg_rating': -1}
            },
            {
                '$limit': limit
            }
        ]
        
        cursor = self.async_db.ratings.aggregate(pipeline)
        return await cursor.to_list(length=limit)
    
    def close(self):
        """Cerrar conexiones"""
        if self.client:
            self.client.close()
        if self.async_client:
            self.async_client.close()

# Instancia global
mongo_manager = MongoDBManager() 