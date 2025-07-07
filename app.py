from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import asyncio
import logging
from datetime import datetime
import time
import numpy as np

# Importar módulos optimizados
from config import Config
from database.mongo_client import mongo_manager
from cache.redis_cache import redis_cache
from models.simple_recommendation_engine import simple_recommendation_engine

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"])

# Variables globales
is_initialized = False
startup_time = None

def run_async_in_sync(async_func, *args, **kwargs):
    """Ejecutar función asíncrona de forma síncrona"""
    try:
        # Intentar obtener el loop actual
        loop = asyncio.get_running_loop()
        # Si hay un loop activo, crear uno nuevo en un hilo separado
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            def run_in_new_loop():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(async_func(*args, **kwargs))
                finally:
                    if not new_loop.is_closed():
                        new_loop.close()
            
            future = executor.submit(run_in_new_loop)
            return future.result()
    except RuntimeError:
        # No hay loop activo, usar asyncio.run
        return asyncio.run(async_func(*args, **kwargs))
    except Exception as e:
        logger.error(f"❌ Error ejecutando función asíncrona: {e}")
        # Fallback: crear un nuevo loop con manejo específico para Motor
        try:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            
            # Para operaciones de MongoDB, asegurar que la conexión esté establecida
            if 'mongo_manager' in str(async_func) or 'async_db' in str(async_func):
                # Re-conectar si es necesario
                if mongo_manager.async_db is None:
                    new_loop.run_until_complete(mongo_manager.async_connect())
            
            result = new_loop.run_until_complete(async_func(*args, **kwargs))
            return result
        except Exception as inner_e:
            logger.error(f"❌ Error en fallback: {inner_e}")
            raise inner_e
        finally:
            if not new_loop.is_closed():
                new_loop.close()

async def _get_stats_async():
    """Función asíncrona para obtener estadísticas"""
    try:
        # Asegurar que la conexión a MongoDB esté establecida
        if mongo_manager.async_db is None:
            await mongo_manager.async_connect()
        
        # Estadísticas de MongoDB
        db_stats = await mongo_manager.async_db.command("dbStats")
        # Estadísticas de cache
        cache_stats = redis_cache.get_cache_stats()
        # Contar documentos
        movies_count = await mongo_manager.async_db.movies.count_documents({})
        ratings_count = await mongo_manager.async_db.ratings.count_documents({})
        users_count = await mongo_manager.async_db.ratings.distinct('userId')
        # Información del motor de recomendaciones
        engine_info = {
            'loaded': simple_recommendation_engine.is_loaded,
            'movies_loaded': len(simple_recommendation_engine.movies_data) if simple_recommendation_engine.movies_data is not None else 0,
            'ratings_loaded': len(simple_recommendation_engine.ratings_data) if simple_recommendation_engine.ratings_data is not None else 0,
            'matrix_shape': simple_recommendation_engine.user_movie_matrix.shape if simple_recommendation_engine.user_movie_matrix is not None else None,
            'available_methods': simple_recommendation_engine.get_available_methods()
        }
        return jsonify({
            'database': {
                'collections': db_stats.get('collections', 0),
                'data_size': db_stats.get('dataSize', 0),
                'storage_size': db_stats.get('storageSize', 0),
                'movies': movies_count,
                'ratings': ratings_count,
                'users': len(users_count)
            },
            'cache': cache_stats,
            'engine': engine_info,
            'system': {
                'initialized': is_initialized,
                'uptime': time.time() - startup_time if startup_time else 0
            }
        })
    except Exception as e:
        import traceback
        logger.error(f"❌ Error obteniendo estadísticas: {e}\n{traceback.format_exc()}")
        return jsonify({'error': f'{e}', 'traceback': traceback.format_exc()}), 500


def initialize_system_sync():
    """Inicializar el sistema de forma síncrona"""
    global is_initialized, startup_time
    
    if not is_initialized:
        startup_time = time.time()
        logger.info("🚀 Inicializando sistema de recomendaciones simple...")
        
        try:
            # Ejecutar inicialización de forma asíncrona
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            success = loop.run_until_complete(simple_recommendation_engine.initialize())
            if success:
                is_initialized = True
                logger.info(f"✅ Sistema inicializado en {time.time() - startup_time:.2f}s")
            else:
                logger.error("❌ Error inicializando sistema")
        except Exception as e:
            logger.error(f"❌ Error en inicialización: {e}")
        finally:
            loop.close()

# Inicializar sistema al importar el módulo
initialize_system_sync()

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/api/methods')
def get_similarity_methods():
    """Obtener métodos de similitud disponibles con explicaciones detalladas"""
    try:
        methods = simple_recommendation_engine.get_available_methods()
        method_details = {}
        
        for method in methods:
            explanation = simple_recommendation_engine.get_similarity_explanation(method)
            
            # Información adicional para cada método
            method_info = {
                'name': method,
                'explanation': explanation,
                'range': '0-1' if method != 'pearson' else '-1 to 1',
                'best_for': {
                    'cosine': 'Datos dispersos, no afectada por magnitud',
                    'euclidean': 'Datos densos, comparaciones directas',
                    'manhattan': 'Datos con ruido, robusta a outliers',
                    'pearson': 'Tendencias lineales, correlaciones'
                }.get(method, 'Uso general'),
                'formula': {
                    'cosine': '1 - cosine(vector1, vector2)',
                    'euclidean': '1 / (1 + euclidean(vector1, vector2))',
                    'manhattan': '1 / (1 + cityblock(vector1, vector2))',
                    'pearson': 'pearsonr(vector1, vector2)[0]'
                }.get(method, 'Fórmula específica')
            }
            
            method_details[method] = method_info
        
        return jsonify({
            'methods': methods,
            'details': method_details,
            'recommendations': {
                'for_movies': 'cosine',
                'for_users': 'pearson',
                'for_comparison': 'euclidean',
                'for_robust': 'manhattan'
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo métodos: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health')
def health_check():
    """Verificar estado del sistema"""
    global is_initialized, startup_time
    
    cache_stats = redis_cache.get_cache_stats()
    
    return jsonify({
        'status': 'healthy' if is_initialized else 'initializing',
        'initialized': is_initialized,
        'uptime': time.time() - startup_time if startup_time else 0,
        'cache': cache_stats,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/init')
def initialize_system_manual():
    """Inicializar sistema manualmente (endpoint síncrono)"""
    global is_initialized
    
    if is_initialized:
        return jsonify({
            'status': 'already_initialized',
            'message': 'Sistema ya inicializado'
        })
    
    # Ejecutar inicialización de forma asíncrona
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        success = loop.run_until_complete(simple_recommendation_engine.initialize())
        if success:
            is_initialized = True
            return jsonify({
                'status': 'success',
                'message': 'Sistema inicializado correctamente'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Error inicializando sistema'
            }), 500
    finally:
        loop.close()

@app.route('/api/movies')
def get_movies():
    """Obtener películas con paginación y filtros"""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 20))
        genre = request.args.get('genre')
        search = request.args.get('search')
        year = request.args.get('year')
        
        skip = (page - 1) * limit
        
        filters = {}
        if genre:
            filters['genre'] = genre
        if search:
            filters['search'] = search
        if year:
            filters['year'] = int(year)
        
        return run_async_in_sync(_get_movies_async, skip, limit, filters)
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo películas: {e}")
        return jsonify({'error': str(e)}), 500

async def _get_movies_async(skip, limit, filters):
    """Función asíncrona para obtener películas"""
    try:
        movies = await mongo_manager.get_movies_batch(skip=skip, limit=limit, filters=filters)
        
        return jsonify({
            'movies': movies,
            'page': (skip // limit) + 1,
            'limit': limit,
            'has_more': len(movies) == limit
        })
    except Exception as e:
        logger.error(f"❌ Error obteniendo películas: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/movies/<movie_id>')
def get_movie(movie_id):
    """Obtener película específica con información detallada"""
    try:
        # Usar operaciones síncronas para evitar problemas con event loops
        # Asegurar conexión síncrona a MongoDB
        if mongo_manager.db is None:
            mongo_manager.connect()
        
        # Obtener película usando operaciones síncronas
        movie = mongo_manager.db.movies.find_one({'movieId': movie_id})
        if not movie:
            return jsonify({'error': 'Película no encontrada'}), 404
        
        # Convertir ObjectId a string para JSON serialization
        movie['_id'] = str(movie['_id'])
        
        # Obtener estadísticas de la película usando operaciones síncronas
        pipeline = [
            {'$match': {'movieId': movie_id}},
            {'$group': {
                '_id': None,
                'avg_rating': {'$avg': '$rating'},
                'total_ratings': {'$sum': 1},
                'min_rating': {'$min': '$rating'},
                'max_rating': {'$max': '$rating'}
            }}
        ]
        
        ratings_stats = list(mongo_manager.db.ratings.aggregate(pipeline))
        
        # Obtener usuarios que calificaron esta película
        users_who_rated = mongo_manager.db.ratings.distinct('userId', {'movieId': movie_id})
        
        # Para las películas similares, usar una aproximación simple
        # ya que el motor de recomendaciones puede requerir operaciones asíncronas
        similar_movies = []
        try:
            # Intentar obtener recomendaciones del motor si está disponible
            if simple_recommendation_engine.is_loaded:
                # Usar una aproximación síncrona simple
                similar_movies = _get_simple_similar_movies(movie_id, movie.get('genres', ''))
        except Exception as e:
            logger.warning(f"⚠️ No se pudieron obtener películas similares: {e}")
        
        movie_info = {
            **movie,
            'stats': ratings_stats[0] if ratings_stats else {
                'avg_rating': 0,
                'total_ratings': 0,
                'min_rating': 0,
                'max_rating': 0
            },
            'similar_movies': similar_movies,
            'users_who_rated': len(users_who_rated)
        }
        
        return jsonify(movie_info)
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo película {movie_id}: {e}")
        return jsonify({'error': str(e)}), 500

def _get_simple_similar_movies(movie_id, genres, limit=5):
    """Obtener películas similares usando una aproximación simple basada en géneros"""
    try:
        if not genres:
            return []
        
        # Buscar películas con géneros similares
        genre_list = genres.split('|')
        query = {
            'movieId': {'$ne': movie_id},
            'genres': {'$regex': '|'.join(genre_list[:2]), '$options': 'i'}
        }
        
        similar_movies = list(mongo_manager.db.movies.find(query).limit(limit))
        
        # Convertir ObjectId a string
        for movie in similar_movies:
            movie['_id'] = str(movie['_id'])
            movie['similarity'] = 0.8  # Similitud estimada
        
        return similar_movies
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo películas similares: {e}")
        return []

@app.route('/api/recommendations/<movie_id>')
def get_recommendations(movie_id):
    """Obtener recomendaciones usando el motor optimizado"""
    try:
        method = request.args.get('method', 'hybrid')
        limit = int(request.args.get('limit', 10))
        
        # Validar método
        available_methods = ['content', 'collaborative', 'popular', 'hybrid']
        if method not in available_methods:
            return jsonify({
                'error': f'Método no válido. Métodos disponibles: {available_methods}'
            }), 400
        
        # Usar operaciones síncronas para evitar problemas con event loops
        # Asegurar conexión síncrona a MongoDB
        if mongo_manager.db is None:
            mongo_manager.connect()
        
        # Verificar si la película existe (convertir a entero si es necesario)
        try:
            movie_id_int = int(movie_id)
        except ValueError:
            return jsonify({'error': 'ID de película debe ser un número'}), 400
        
        movie = mongo_manager.db.movies.find_one({'movieId': movie_id_int})
        if not movie:
            return jsonify({'error': 'Película no encontrada'}), 404
        
        # Obtener recomendaciones usando una aproximación síncrona
        recommendations = _get_sync_recommendations(movie_id, method, limit)
        
        # Obtener explicación del método
        explanations = {
            'content': 'Recomendaciones basadas en similitud de contenido (géneros)',
            'collaborative': 'Recomendaciones basadas en usuarios similares',
            'popular': 'Películas más populares',
            'hybrid': 'Combinación de métodos de contenido y colaborativo'
        }
        
        return jsonify({
            'movie_id': movie_id,
            'method': method,
            'explanation': explanations.get(method, 'Método de recomendación'),
            'recommendations': recommendations,
            'count': len(recommendations)
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo recomendaciones: {e}")
        return jsonify({'error': str(e)}), 500

def _get_sync_recommendations(movie_id, method, limit):
    """Obtener recomendaciones usando operaciones síncronas"""
    try:
        if method == 'content':
            return _get_content_recommendations(movie_id, limit)
        elif method == 'collaborative':
            return _get_collaborative_recommendations(movie_id, limit)
        elif method == 'popular':
            return _get_popular_recommendations(limit)
        else:  # hybrid
            return _get_hybrid_recommendations(movie_id, limit)
    except Exception as e:
        logger.error(f"❌ Error obteniendo recomendaciones síncronas: {e}")
        return []

def _get_content_recommendations(movie_id, limit):
    """Recomendaciones basadas en contenido usando operaciones síncronas"""
    try:
        # Convertir movie_id a entero
        movie_id_int = int(movie_id)
        
        # Obtener la película de referencia
        movie = mongo_manager.db.movies.find_one({'movieId': movie_id_int})
        if not movie:
            return []
        
        genres = movie.get('genres', '')
        if not genres:
            return []
        
        # Buscar películas con géneros similares
        genre_list = genres.split('|')
        query = {
            'movieId': {'$ne': movie_id},
            'genres': {'$regex': '|'.join(genre_list[:2]), '$options': 'i'}
        }
        
        similar_movies = list(mongo_manager.db.movies.find(query).limit(limit * 2))
        
        # Calcular similitud simple basada en géneros compartidos
        recommendations = []
        for similar_movie in similar_movies:
            similar_genres = similar_movie.get('genres', '').split('|')
            shared_genres = set(genre_list) & set(similar_genres)
            similarity = len(shared_genres) / max(len(genre_list), len(similar_genres))
            
            if similarity > 0:
                recommendations.append({
                    'movieId': similar_movie['movieId'],
                    'title': similar_movie['title'],
                    'genres': similar_movie.get('genres', ''),
                    'year': similar_movie.get('year'),
                    'similarity_score': similarity
                })
        
        # Ordenar por similitud y limitar
        recommendations.sort(key=lambda x: x['similarity_score'], reverse=True)
        return recommendations[:limit]
        
    except Exception as e:
        logger.error(f"❌ Error en recomendaciones de contenido: {e}")
        return []

def _get_collaborative_recommendations(movie_id, limit):
    """Recomendaciones colaborativas usando operaciones síncronas"""
    try:
        # Obtener usuarios que calificaron esta película con alta calificación
        pipeline = [
            {'$match': {'movieId': movie_id, 'rating': {'$gte': 4.0}}},
            {'$group': {'_id': '$userId'}}
        ]
        
        high_rating_users = list(mongo_manager.db.ratings.aggregate(pipeline))
        user_ids = [user['_id'] for user in high_rating_users]
        
        if not user_ids:
            return []
        
        # Obtener películas mejor calificadas por usuarios similares
        pipeline = [
            {
                '$match': {
                    'userId': {'$in': user_ids},
                    'movieId': {'$ne': movie_id},
                    'rating': {'$gte': 4.0}
                }
            },
            {
                '$group': {
                    '_id': '$movieId',
                    'avg_rating': {'$avg': '$rating'},
                    'count': {'$sum': 1}
                }
            },
            {
                '$match': {
                    'count': {'$gte': 2}
                }
            },
            {
                '$sort': {'avg_rating': -1}
            },
            {
                '$limit': limit
            }
        ]
        
        results = list(mongo_manager.db.ratings.aggregate(pipeline))
        
        # Obtener información de películas
        recommendations = []
        for result in results:
            movie = mongo_manager.db.movies.find_one({'movieId': result['_id']})
            if movie:
                recommendations.append({
                    'movieId': movie['movieId'],
                    'title': movie['title'],
                    'genres': movie.get('genres', ''),
                    'year': movie.get('year'),
                    'avg_rating': float(result['avg_rating']),
                    'rating_count': result['count']
                })
        
        return recommendations
        
    except Exception as e:
        logger.error(f"❌ Error en recomendaciones colaborativas: {e}")
        return []

def _get_popular_recommendations(limit):
    """Recomendaciones basadas en popularidad usando operaciones síncronas"""
    try:
        # Obtener películas más populares
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
                    'count': {'$gte': 10}
                }
            },
            {
                '$sort': {'avg_rating': -1}
            },
            {
                '$limit': limit
            }
        ]
        
        popular_movies = list(mongo_manager.db.ratings.aggregate(pipeline))
        
        # Obtener información de películas
        recommendations = []
        for popular in popular_movies:
            movie = mongo_manager.db.movies.find_one({'movieId': popular['_id']})
            if movie:
                recommendations.append({
                    'movieId': movie['movieId'],
                    'title': movie['title'],
                    'genres': movie.get('genres', ''),
                    'year': movie.get('year'),
                    'avg_rating': float(popular['avg_rating']),
                    'rating_count': popular['count']
                })
        
        return recommendations
        
    except Exception as e:
        logger.error(f"❌ Error en recomendaciones populares: {e}")
        return []

def _get_hybrid_recommendations(movie_id, limit):
    """Recomendaciones híbridas usando operaciones síncronas"""
    try:
        # Obtener recomendaciones de diferentes métodos
        content_recs = _get_content_recommendations(movie_id, limit)
        collab_recs = _get_collaborative_recommendations(movie_id, limit)
        popular_recs = _get_popular_recommendations(limit)
        
        # Combinar y puntuar
        all_recommendations = {}
        
        # Puntuar recomendaciones de contenido (40%)
        for i, rec in enumerate(content_recs):
            movie_id = rec['movieId']
            score = (limit - i) * 0.4
            all_recommendations[movie_id] = all_recommendations.get(movie_id, 0) + score
        
        # Puntuar recomendaciones colaborativas (40%)
        for i, rec in enumerate(collab_recs):
            movie_id = rec['movieId']
            score = (limit - i) * 0.4
            all_recommendations[movie_id] = all_recommendations.get(movie_id, 0) + score
        
        # Puntuar recomendaciones populares (20%)
        for i, rec in enumerate(popular_recs):
            movie_id = rec['movieId']
            score = (limit - i) * 0.2
            all_recommendations[movie_id] = all_recommendations.get(movie_id, 0) + score
        
        # Ordenar por puntuación
        sorted_recs = sorted(all_recommendations.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        # Formatear resultados
        recommendations = []
        for movie_id, score in sorted_recs:
            movie = mongo_manager.db.movies.find_one({'movieId': movie_id})
            if movie:
                recommendations.append({
                    'movieId': movie['movieId'],
                    'title': movie['title'],
                    'genres': movie.get('genres', ''),
                    'year': movie.get('year'),
                    'hybrid_score': float(score)
                })
        
        return recommendations
        
    except Exception as e:
        logger.error(f"❌ Error en recomendaciones híbridas: {e}")
        return []

def _get_popular_movies_with_ratings(limit):
    """Obtener películas populares con información de rating usando operaciones síncronas"""
    try:
        # Obtener películas más populares con rating
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
                    'count': {'$gte': 10}  # Al menos 10 calificaciones
                }
            },
            {
                '$sort': {'avg_rating': -1}
            },
            {
                '$limit': limit
            }
        ]
        
        popular_movies = list(mongo_manager.db.ratings.aggregate(pipeline))
        
        # Obtener información completa de películas
        enriched_movies = []
        for popular in popular_movies:
            movie = mongo_manager.db.movies.find_one({'movieId': popular['_id']})
            if movie:
                enriched_movie = {
                    'movieId': movie['movieId'],
                    'title': movie['title'],
                    'genres': movie.get('genres', ''),
                    'year': movie.get('year'),
                    '_id': str(movie['_id']),
                    'avg_rating': float(popular['avg_rating']),
                    'total_ratings': popular['count'],
                    'rating_count': popular['count'],
                    'similarity_score': 1.0,  # Máxima similitud para películas populares
                    'min_rating': 0,  # Placeholder
                    'max_rating': 5.0  # Placeholder
                }
                enriched_movies.append(enriched_movie)
        
        return enriched_movies
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo películas populares con rating: {e}")
        return []

@app.route('/api/user-recommendations/<user_id>')
def get_user_recommendations(user_id):
    """Obtener recomendaciones basadas en usuario"""
    try:
        method = request.args.get('method', 'cosine')
        limit = int(request.args.get('limit', 10))
        
        if not is_initialized:
            return jsonify({'error': 'Sistema no inicializado'}), 503
        
        # Usar run_async_in_sync para manejar operaciones asíncronas
        try:
            recommendations = run_async_in_sync(simple_recommendation_engine.get_user_based_recommendations,
                user_id, method, limit
            )
            
            return jsonify({
                'user_id': user_id,
                'method': method,
                'recommendations': recommendations,
                'count': len(recommendations)
            })
        except Exception as e:
            logger.error(f"❌ Error obteniendo recomendaciones de usuario: {e}")
            return jsonify({'error': str(e)}), 500
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo recomendaciones de usuario: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/similarity/<movie_id1>/<movie_id2>')
def get_similarity(movie_id1, movie_id2):
    """Calcular similitud entre dos películas específicas"""
    try:
        method = request.args.get('method', 'cosine')
        
        if not is_initialized:
            return jsonify({'error': 'Sistema no inicializado'}), 503
        
        # Validar método
        available_methods = simple_recommendation_engine.get_available_methods()
        if method not in available_methods:
            return jsonify({
                'error': f'Método no válido. Métodos disponibles: {available_methods}'
            }), 400
        
        # Usar run_async_in_sync para manejar operaciones asíncronas
        try:
            # Obtener información de ambas películas
            movie1 = run_async_in_sync(mongo_manager.get_movie_by_id, movie_id1)
            movie2 = run_async_in_sync(mongo_manager.get_movie_by_id, movie_id2)
            
            if not movie1 or not movie2:
                return jsonify({'error': 'Una o ambas películas no encontradas'}), 404
            
            similarity = simple_recommendation_engine.get_movie_similarity(movie_id1, movie_id2, method)
            explanation = simple_recommendation_engine.get_similarity_explanation(method)
            
            # Calcular similitud con todos los métodos para comparación
            all_methods_similarity = {}
            for method_name in available_methods:
                all_methods_similarity[method_name] = simple_recommendation_engine.get_movie_similarity(
                    movie_id1, movie_id2, method_name
                )
            
            return jsonify({
                'movie1': movie1,
                'movie2': movie2,
                'selected_method': method,
                'similarity': similarity,
                'explanation': explanation,
                'all_methods': all_methods_similarity,
                'comparison': {
                    'genres_match': bool(set(movie1['genres'].split('|')) & set(movie2['genres'].split('|'))),
                    'year_diff': abs(movie1.get('year', 0) - movie2.get('year', 0))
                }
            })
        except Exception as e:
            logger.error(f"❌ Error calculando similitud: {e}")
            return jsonify({'error': str(e)}), 500
        
    except Exception as e:
        logger.error(f"❌ Error calculando similitud: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/search')
def search_movies():
    """Buscar películas"""
    try:
        query = request.args.get('q', '')
        limit = int(request.args.get('limit', 20))
        genre = request.args.get('genre')
        year = request.args.get('year')
        rating = request.args.get('rating')
        
        # Usar run_async_in_sync para manejar operaciones asíncronas
        try:
            if not query and not genre and not year and not rating:
                # Si no hay filtros, devolver películas populares con información de rating
                popular_movies = _get_popular_movies_with_ratings(limit)
                return jsonify(popular_movies)
            
            # Construir filtros
            filters = {}
            if query:
                filters['search'] = query
            if genre:
                filters['genre'] = genre
            if year:
                filters['year'] = int(year)
            if rating:
                filters['rating'] = float(rating)
            
            # Verificar cache para búsquedas simples
            if query and not genre and not year and not rating:
                cached_results = redis_cache.get_cached_search_results(query)
                if cached_results:
                    return jsonify(cached_results[:limit])
            
            # Búsqueda en MongoDB
            results = run_async_in_sync(mongo_manager.get_movies_batch, limit=limit, filters=filters)
            
            # Guardar en cache para búsquedas simples
            if query and results and not genre and not year and not rating:
                redis_cache.cache_search_results(query, results)
            
            return jsonify(results)
        except Exception as e:
            logger.error(f"❌ Error en búsqueda: {e}")
            return jsonify({'error': str(e)}), 500
        
    except Exception as e:
        logger.error(f"❌ Error en búsqueda: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/genres')
def get_genres():
    """Obtener géneros disponibles"""
    try:
        # Usar operaciones síncronas para evitar problemas con event loops
        # Asegurar conexión síncrona a MongoDB
        if mongo_manager.db is None:
            mongo_manager.connect()
        
        # Pipeline de agregación para obtener géneros únicos
        pipeline = [
            {
                '$project': {
                    'genres': {
                        '$split': ['$genres', '|']
                    }
                }
            },
            {
                '$unwind': '$genres'
            },
            {
                '$group': {
                    '_id': '$genres',
                    'count': {'$sum': 1}
                }
            },
            {
                '$sort': {'count': -1}
            }
        ]
        
        # Usar operaciones síncronas
        genres = list(mongo_manager.db.movies.aggregate(pipeline))
        
        return jsonify([{
            'genre': genre['_id'],
            'count': genre['count']
        } for genre in genres if genre['_id'] != 'Unknown'])
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo géneros: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/genres/<genre>')
def get_movies_by_genre(genre):
    """Obtener películas por género con información de rating y similitud"""
    try:
        limit = int(request.args.get('limit', 20))
        
        # Verificar cache
        cached_movies = redis_cache.get_cached_genre_movies(genre)
        if cached_movies:
            return jsonify(cached_movies[:limit])
        
        # Usar operaciones síncronas para evitar problemas con event loops
        # Asegurar conexión síncrona a MongoDB
        if mongo_manager.db is None:
            mongo_manager.connect()
        
        # Obtener películas del género usando operaciones síncronas
        query = {'genres': {'$regex': genre, '$options': 'i'}}
        movies = list(mongo_manager.db.movies.find(query).limit(limit))
        
        # Enriquecer películas con información de rating y similitud
        enriched_movies = []
        for movie in movies:
            movie_id = movie['movieId']
            
            # Obtener estadísticas de rating para esta película
            rating_pipeline = [
                {'$match': {'movieId': movie_id}},
                {'$group': {
                    '_id': None,
                    'avg_rating': {'$avg': '$rating'},
                    'total_ratings': {'$sum': 1},
                    'min_rating': {'$min': '$rating'},
                    'max_rating': {'$max': '$rating'}
                }}
            ]
            
            rating_stats = list(mongo_manager.db.ratings.aggregate(rating_pipeline))
            
            # Calcular similitud basada en géneros compartidos
            movie_genres = movie.get('genres', '').split('|')
            genre_similarity = len([g for g in movie_genres if g.lower() == genre.lower()]) / len(movie_genres) if movie_genres else 0
            
            # Crear película enriquecida
            enriched_movie = {
                'movieId': movie['movieId'],
                'title': movie['title'],
                'genres': movie.get('genres', ''),
                'year': movie.get('year'),
                '_id': str(movie['_id']),
                'avg_rating': float(rating_stats[0]['avg_rating']) if rating_stats else 0,
                'total_ratings': rating_stats[0]['total_ratings'] if rating_stats else 0,
                'min_rating': float(rating_stats[0]['min_rating']) if rating_stats else 0,
                'max_rating': float(rating_stats[0]['max_rating']) if rating_stats else 0,
                'similarity_score': genre_similarity,
                'rating_count': rating_stats[0]['total_ratings'] if rating_stats else 0
            }
            
            enriched_movies.append(enriched_movie)
        
        # Ordenar por rating promedio (descendente)
        enriched_movies.sort(key=lambda x: x['avg_rating'], reverse=True)
        
        # Guardar en cache
        if enriched_movies:
            redis_cache.cache_genre_movies(genre, enriched_movies)
        
        return jsonify(enriched_movies)
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo películas por género: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/genre-recommendations')
def get_genre_recommendations():
    """Obtener recomendaciones basadas en múltiples géneros seleccionados"""
    try:
        genres = request.args.get('genres', '').split(',')
        limit = int(request.args.get('limit', 20))
        method = request.args.get('method', 'hybrid')
        
        if not genres or genres[0] == '':
            return jsonify({'error': 'Debe especificar al menos un género'}), 400
        
        # Validar método - incluir algoritmos de similitud
        available_methods = ['content', 'collaborative', 'popular', 'hybrid', 'cosine', 'pearson', 'euclidean', 'manhattan']
        if method not in available_methods:
            return jsonify({
                'error': f'Método no válido. Métodos disponibles: {available_methods}'
            }), 400
        
        # Usar operaciones síncronas para evitar problemas con event loops
        # Asegurar conexión síncrona a MongoDB
        if mongo_manager.db is None:
            mongo_manager.connect()
        
        # Obtener recomendaciones basadas en múltiples géneros
        recommendations = _get_multi_genre_recommendations(genres, method, limit)
        
        # Obtener explicación del método
        explanations = {
            'content': 'Recomendaciones basadas en similitud de contenido (géneros)',
            'collaborative': 'Recomendaciones basadas en usuarios similares',
            'popular': 'Películas más populares',
            'hybrid': 'Combinación de métodos de contenido y colaborativo'
        }
        
        return jsonify({
            'genres': genres,
            'method': method,
            'explanation': explanations.get(method, 'Método de recomendación'),
            'recommendations': recommendations,
            'count': len(recommendations)
        })
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo recomendaciones por géneros: {e}")
        return jsonify({'error': str(e)}), 500

def _get_multi_genre_recommendations(genres, method, limit):
    """Obtener recomendaciones basadas en múltiples géneros o similitud KNN"""
    try:
        # Construir query para múltiples géneros
        genre_queries = []
        for genre in genres:
            if genre.strip():
                genre_queries.append({'genres': {'$regex': genre.strip(), '$options': 'i'}})
        if not genre_queries:
            return []
        # Buscar películas que contengan al menos uno de los géneros seleccionados
        query = {'$or': genre_queries}
        movies = list(mongo_manager.db.movies.find(query).limit(limit * 5))  # Obtener más para filtrar
        # Si el método es de similitud, aplicar KNN
        similarity_methods = ['cosine', 'pearson', 'euclidean', 'manhattan']
        if method in similarity_methods and len(movies) > 1:
            # Calcular la similitud promedio de cada película respecto a las demás
            movie_ids = [m['movieId'] for m in movies]
            sim_scores = {}
            for i, movie in enumerate(movies):
                sims = []
                for j, other in enumerate(movies):
                    if i != j:
                        sim = simple_recommendation_engine.get_movie_similarity(movie['movieId'], other['movieId'], method)
                        sims.append(sim)
                sim_scores[movie['movieId']] = float(np.mean(sims)) if sims else 0.0
            # Enriquecer películas con información de rating y similitud
            enriched_movies = []
            for movie in movies:
                movie_id = movie['movieId']
                rating_pipeline = [
                    {'$match': {'movieId': movie_id}},
                    {'$group': {
                        '_id': None,
                        'avg_rating': {'$avg': '$rating'},
                        'total_ratings': {'$sum': 1},
                        'min_rating': {'$min': '$rating'},
                        'max_rating': {'$max': '$rating'}
                    }}
                ]
                rating_stats = list(mongo_manager.db.ratings.aggregate(rating_pipeline))
                enriched_movie = {
                    'movieId': movie['movieId'],
                    'title': movie['title'],
                    'genres': movie.get('genres', ''),
                    'year': movie.get('year'),
                    '_id': str(movie['_id']),
                    'avg_rating': float(rating_stats[0]['avg_rating']) if rating_stats else 0,
                    'total_ratings': rating_stats[0]['total_ratings'] if rating_stats else 0,
                    'min_rating': float(rating_stats[0]['min_rating']) if rating_stats else 0,
                    'max_rating': float(rating_stats[0]['max_rating']) if rating_stats else 0,
                    'similarity_score': sim_scores.get(movie_id, 0.0),
                    'rating_count': rating_stats[0]['total_ratings'] if rating_stats else 0
                }
                enriched_movies.append(enriched_movie)
            # Ordenar por similitud y rating
            enriched_movies.sort(key=lambda x: (x['similarity_score'], x['avg_rating']), reverse=True)
            return enriched_movies[:limit]
        else:
            # --- Modo clásico: similitud de géneros ---
            enriched_movies = []
            for movie in movies:
                movie_id = movie['movieId']
                rating_pipeline = [
                    {'$match': {'movieId': movie_id}},
                    {'$group': {
                        '_id': None,
                        'avg_rating': {'$avg': '$rating'},
                        'total_ratings': {'$sum': 1},
                        'min_rating': {'$min': '$rating'},
                        'max_rating': {'$max': '$rating'}
                    }}
                ]
                rating_stats = list(mongo_manager.db.ratings.aggregate(rating_pipeline))
                movie_genres = movie.get('genres', '').split('|')
                shared_genres = set(movie_genres) & set(genres)
                genre_similarity = len(shared_genres) / max(len(movie_genres), len(genres)) if movie_genres else 0
                enriched_movie = {
                    'movieId': movie['movieId'],
                    'title': movie['title'],
                    'genres': movie.get('genres', ''),
                    'year': movie.get('year'),
                    '_id': str(movie['_id']),
                    'avg_rating': float(rating_stats[0]['avg_rating']) if rating_stats else 0,
                    'total_ratings': rating_stats[0]['total_ratings'] if rating_stats else 0,
                    'min_rating': float(rating_stats[0]['min_rating']) if rating_stats else 0,
                    'max_rating': float(rating_stats[0]['max_rating']) if rating_stats else 0,
                    'similarity_score': genre_similarity,
                    'rating_count': rating_stats[0]['total_ratings'] if rating_stats else 0
                }
                enriched_movies.append(enriched_movie)
            enriched_movies.sort(key=lambda x: (x['similarity_score'], x['avg_rating']), reverse=True)
            return enriched_movies[:limit]
    except Exception as e:
        logger.error(f"❌ Error obteniendo recomendaciones multi-género: {e}")
        return []

@app.route('/api/stats')
def get_stats():
    """Obtener estadísticas del sistema"""
    try:
        # Usar operaciones síncronas para evitar problemas con event loops
        # Asegurar conexión síncrona a MongoDB
        if mongo_manager.db is None:
            mongo_manager.connect()
        
        # Estadísticas de MongoDB usando operaciones síncronas
        db_stats = mongo_manager.db.command("dbStats")
        
        # Estadísticas de cache
        cache_stats = redis_cache.get_cache_stats()
        
        # Contar documentos usando operaciones síncronas
        movies_count = mongo_manager.db.movies.count_documents({})
        ratings_count = mongo_manager.db.ratings.count_documents({})
        users_count = mongo_manager.db.ratings.distinct('userId')
        
        # Información del motor de recomendaciones
        engine_info = {
            'loaded': simple_recommendation_engine.is_loaded,
            'movies_loaded': len(simple_recommendation_engine.movies_data) if simple_recommendation_engine.movies_data is not None else 0,
            'ratings_loaded': len(simple_recommendation_engine.ratings_data) if simple_recommendation_engine.ratings_data is not None else 0,
            'matrix_shape': simple_recommendation_engine.user_movie_matrix.shape if simple_recommendation_engine.user_movie_matrix is not None else None,
            'available_methods': simple_recommendation_engine.get_available_methods()
        }
        
        return jsonify({
            'database': {
                'collections': db_stats.get('collections', 0),
                'data_size': db_stats.get('dataSize', 0),
                'storage_size': db_stats.get('storageSize', 0),
                'movies': movies_count,
                'ratings': ratings_count,
                'users': len(users_count)
            },
            'cache': cache_stats,
            'engine': engine_info,
            'system': {
                'initialized': is_initialized,
                'uptime': time.time() - startup_time if startup_time else 0
            }
        })
        
    except Exception as e:
        import traceback
        logger.error(f"❌ Error obteniendo estadísticas: {e}\n{traceback.format_exc()}")
        return jsonify({'error': f'{e}', 'traceback': traceback.format_exc()}), 500

@app.route('/api/cache/clear')
def clear_cache():
    """Limpiar cache"""
    try:
        redis_cache.clear_pattern('*')
        return jsonify({
            'status': 'success',
            'message': 'Cache limpiado correctamente'
        })
    except Exception as e:
        logger.error(f"❌ Error limpiando cache: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint no encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Error interno del servidor'}), 500

if __name__ == '__main__':
    app.run(
        debug=Config.DEBUG,
        host='0.0.0.0',
        port=5000,
        threaded=True
    ) 