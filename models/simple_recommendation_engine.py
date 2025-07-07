import numpy as np
import pandas as pd
from scipy.spatial.distance import cosine, euclidean, cityblock
from scipy.stats import pearsonr
import logging
from database.mongo_client import mongo_manager
from cache.redis_cache import redis_cache

logger = logging.getLogger(__name__)

class SimpleRecommendationEngine:
    def __init__(self):
        self.is_loaded = False
        self.movies_data = None
        self.ratings_data = None
        self.user_movie_matrix = None
        self.movie_similarity_cache = {}
        
    async def initialize(self):
        """Inicializar el motor de recomendaciones simple"""
        try:
            # Conectar a MongoDB
            await mongo_manager.async_connect()
            
            # Cargar datos necesarios
            await self._load_data()
            
            self.is_loaded = True
            logger.info("✅ Motor de recomendaciones simple inicializado")
            return True
        except Exception as e:
            logger.error(f"❌ Error inicializando motor: {e}")
            return False
    
    async def _load_data(self):
        """Cargar datos de MongoDB"""
        try:
            # Cargar películas
            movies = await mongo_manager.get_movies_batch(limit=10000)
            self.movies_data = pd.DataFrame(movies)
            
            # Cargar ratings
            ratings = await mongo_manager.async_db.ratings.find().limit(100000).to_list(length=100000)
            self.ratings_data = pd.DataFrame(ratings)
            
            # Crear matriz usuario-película
            self._create_user_movie_matrix()
            
            logger.info(f"✅ Datos cargados: {len(self.movies_data)} películas, {len(self.ratings_data)} ratings")
            
        except Exception as e:
            logger.error(f"❌ Error cargando datos: {e}")
    
    def _create_user_movie_matrix(self):
        """Crear matriz usuario-película para cálculos de similitud"""
        try:
            # Crear matriz pivote
            self.user_movie_matrix = self.ratings_data.pivot_table(
                index='userId',
                columns='movieId',
                values='rating',
                fill_value=0
            )
            logger.info(f"✅ Matriz usuario-película creada: {self.user_movie_matrix.shape}")
        except Exception as e:
            logger.error(f"❌ Error creando matriz: {e}")
    
    def calculate_similarity(self, vector1, vector2, method='cosine'):
        """Calcular similitud entre dos vectores usando diferentes métricas"""
        try:
            # Eliminar valores nulos
            mask = ~(np.isnan(vector1) | np.isnan(vector2))
            v1 = vector1[mask]
            v2 = vector2[mask]
            
            if len(v1) == 0:
                return 0.0
            
            if method == 'cosine':
                # Similitud de coseno
                return 1 - cosine(v1, v2) if np.any(v1) and np.any(v2) else 0.0
                
            elif method == 'euclidean':
                # Distancia euclidiana (convertir a similitud)
                distance = euclidean(v1, v2)
                return 1 / (1 + distance) if distance > 0 else 1.0
                
            elif method == 'manhattan':
                # Distancia Manhattan (convertir a similitud)
                distance = cityblock(v1, v2)
                return 1 / (1 + distance) if distance > 0 else 1.0
                
            elif method == 'pearson':
                # Correlación de Pearson
                if len(v1) < 2:
                    return 0.0
                correlation, _ = pearsonr(v1, v2)
                return correlation if not np.isnan(correlation) else 0.0
                
            else:
                raise ValueError(f"Método de similitud no válido: {method}")
                
        except Exception as e:
            logger.error(f"❌ Error calculando similitud {method}: {e}")
            return 0.0
    
    def get_movie_similarity(self, movie_id1, movie_id2, method='cosine'):
        """Calcular similitud entre dos películas"""
        try:
            # Verificar cache
            cache_key = f"{movie_id1}_{movie_id2}_{method}"
            if cache_key in self.movie_similarity_cache:
                return self.movie_similarity_cache[cache_key]
            
            # Obtener vectores de ratings para ambas películas
            if movie_id1 in self.user_movie_matrix.columns and movie_id2 in self.user_movie_matrix.columns:
                vector1 = self.user_movie_matrix[movie_id1].values
                vector2 = self.user_movie_matrix[movie_id2].values
                
                similarity = self.calculate_similarity(vector1, vector2, method)
                
                # Guardar en cache
                self.movie_similarity_cache[cache_key] = similarity
                
                return similarity
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"❌ Error calculando similitud entre películas: {e}")
            return 0.0
    
    def get_user_similarity(self, user_id1, user_id2, method='cosine'):
        """Calcular similitud entre dos usuarios"""
        try:
            if user_id1 in self.user_movie_matrix.index and user_id2 in self.user_movie_matrix.index:
                vector1 = self.user_movie_matrix.loc[user_id1].values
                vector2 = self.user_movie_matrix.loc[user_id2].values
                
                return self.calculate_similarity(vector1, vector2, method)
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"❌ Error calculando similitud entre usuarios: {e}")
            return 0.0
    
    async def get_recommendations(self, movie_id, method='cosine', limit=10):
        """Obtener recomendaciones usando métricas de similitud básicas"""
        try:
            # Verificar cache
            cached_recs = redis_cache.get_cached_recommendations(movie_id, method)
            if cached_recs:
                logger.info(f"✅ Recomendaciones obtenidas de cache para {movie_id}")
                return cached_recs[:limit]
            
            # Obtener película de referencia
            movie = await mongo_manager.get_movie_by_id(movie_id)
            if not movie:
                return []
            
            # Calcular similitud con todas las películas
            similarities = []
            seen_movies = set()  # Para evitar duplicados
            for _, row in self.movies_data.iterrows():
                other_movie_id = row['movieId']
                if other_movie_id != movie_id and other_movie_id not in seen_movies:
                    similarity = self.get_movie_similarity(movie_id, other_movie_id, method)
                    similarities.append({
                        'movieId': other_movie_id,
                        'title': row['title'],
                        'genres': row.get('genres', ''),
                        'year': row.get('year'),
                        'similarity': similarity
                    })
                    seen_movies.add(other_movie_id)
            
            # Ordenar por similitud
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            # Filtrar solo películas con similitud > 0
            recommendations = [rec for rec in similarities[:limit] if rec['similarity'] > 0]
            
            # Guardar en cache
            if recommendations:
                redis_cache.cache_movie_recommendations(movie_id, method, recommendations)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo recomendaciones: {e}")
            return []
    
    async def get_user_based_recommendations(self, user_id, method='cosine', limit=10):
        """Recomendaciones basadas en usuarios similares"""
        try:
            # Convertir user_id a entero para comparación correcta
            user_id_int = int(user_id)
            
            if user_id_int not in self.user_movie_matrix.index:
                logger.warning(f"⚠️ Usuario {user_id} no encontrado en la matriz")
                # Fallback: devolver películas populares
                return await self.get_popular_movies(limit)
            
            # Encontrar usuarios similares
            user_similarities = []
            for other_user_id in self.user_movie_matrix.index:
                if other_user_id != user_id_int:
                    similarity = self.get_user_similarity(user_id_int, other_user_id, method)
                    # Reducir umbral para incluir más usuarios
                    if similarity >= 0:
                        user_similarities.append({
                            'userId': other_user_id,
                            'similarity': similarity
                        })
            
            # Ordenar por similitud
            user_similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            logger.info(f"📊 Encontrados {len(user_similarities)} usuarios similares para usuario {user_id}")
            
            # Obtener películas mejor calificadas por usuarios similares
            recommendations = []
            seen_movies = set()  # Para evitar duplicados
            user_movies = set(self.user_movie_matrix.columns[self.user_movie_matrix.loc[user_id_int] > 0])
            
            for similar_user in user_similarities[:50]:  # Aumentar a top 50 usuarios similares
                similar_user_id = similar_user['userId']
                similar_user_ratings = self.user_movie_matrix.loc[similar_user_id]
                
                # Reducir umbral de rating de 4.0 a 3.0
                high_rated_movies = similar_user_ratings[
                    (similar_user_ratings >= 3.0) & 
                    (~similar_user_ratings.index.isin(user_movies))
                ]
                
                for movie_id, rating in high_rated_movies.items():
                    # Evitar duplicados
                    if movie_id not in seen_movies:
                        movie_info = self.movies_data[self.movies_data['movieId'] == movie_id]
                        if not movie_info.empty:
                            movie_info = movie_info.iloc[0]
                            recommendations.append({
                                'movieId': movie_id,
                                'title': movie_info['title'],
                                'genres': movie_info.get('genres', ''),
                                'year': movie_info.get('year'),
                                'rating': rating,
                                'user_similarity': similar_user['similarity']
                            })
                            seen_movies.add(movie_id)
            
            # Ordenar por rating y similitud
            recommendations.sort(key=lambda x: (x['rating'], x['user_similarity']), reverse=True)
            
            logger.info(f"📊 Generadas {len(recommendations)} recomendaciones para usuario {user_id}")
            
            # Si no hay recomendaciones específicas, usar películas populares como fallback
            if not recommendations:
                logger.info(f"⚠️ No se encontraron recomendaciones específicas para usuario {user_id}, usando películas populares")
                return await self.get_popular_movies(limit)
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"❌ Error en recomendaciones basadas en usuario: {e}")
            # Fallback: devolver películas populares
            return await self.get_popular_movies(limit)
    
    async def get_popular_movies(self, limit=10):
        """Obtener películas populares basadas en ratings promedio"""
        try:
            # Verificar cache
            cached_popular = redis_cache.get_cached_popular_movies()
            if cached_popular:
                return cached_popular[:limit]
            
            # Calcular ratings promedio por película
            movie_stats = self.ratings_data.groupby('movieId').agg({
                'rating': ['mean', 'count']
            }).reset_index()
            
            movie_stats.columns = ['movieId', 'avg_rating', 'rating_count']
            
            # Filtrar películas con suficientes ratings
            popular_movies = movie_stats[
                (movie_stats['rating_count'] >= 10) & 
                (movie_stats['avg_rating'] >= 3.5)
            ].sort_values('avg_rating', ascending=False)
            
            # Obtener información de películas
            recommendations = []
            seen_movies = set()  # Para evitar duplicados
            for _, row in popular_movies.head(limit * 2).iterrows():  # Obtener más para compensar duplicados
                movie_id = row['movieId']
                if movie_id not in seen_movies:
                    movie_info = self.movies_data[self.movies_data['movieId'] == movie_id]
                    if not movie_info.empty:
                        movie_info = movie_info.iloc[0]
                        recommendations.append({
                            'movieId': movie_id,
                            'title': movie_info['title'],
                            'genres': movie_info.get('genres', ''),
                            'year': movie_info.get('year'),
                            'avg_rating': float(row['avg_rating']),
                            'rating_count': int(row['rating_count'])
                        })
                        seen_movies.add(movie_id)
                        if len(recommendations) >= limit:
                            break
            
            # Guardar en cache
            if recommendations:
                redis_cache.cache_popular_movies(recommendations)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo películas populares: {e}")
            return []
    
    def get_available_methods(self):
        """Obtener métodos de similitud disponibles"""
        return ['cosine', 'euclidean', 'manhattan', 'pearson']
    
    def get_similarity_explanation(self, method):
        """Obtener explicación de cada método de similitud"""
        explanations = {
            'cosine': 'Similitud de coseno: Mide el ángulo entre vectores de ratings',
            'euclidean': 'Distancia euclidiana: Mide la distancia directa entre vectores',
            'manhattan': 'Distancia Manhattan: Mide la suma de diferencias absolutas',
            'pearson': 'Correlación de Pearson: Mide la correlación lineal entre vectores'
        }
        return explanations.get(method, 'Método no reconocido')

# Instancia global
simple_recommendation_engine = SimpleRecommendationEngine() 