#!/usr/bin/env python3
"""
Script para verificar películas disponibles en la base de datos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.mongo_client import mongo_manager

def check_movies():
    """Verificar películas disponibles"""
    print("🔍 Verificando películas disponibles en la base de datos...")
    
    try:
        # Conectar a MongoDB
        if mongo_manager.db is None:
            mongo_manager.connect()
        
        # Contar total de películas
        total_movies = mongo_manager.db.movies.count_documents({})
        print(f"📊 Total de películas en la base de datos: {total_movies}")
        
        # Obtener algunas películas de ejemplo
        sample_movies = list(mongo_manager.db.movies.find().limit(10))
        
        print("\n🎬 Películas de ejemplo:")
        for i, movie in enumerate(sample_movies, 1):
            print(f"  {i}. ID: {movie.get('movieId')} - {movie.get('title', 'Sin título')} ({movie.get('year', 'N/A')})")
        
        # Verificar si existen películas con IDs específicos
        test_ids = [1, 2, 3, 195619, 278752, 100, 500, 1000]
        print(f"\n🔍 Verificando IDs específicos:")
        for movie_id in test_ids:
            movie = mongo_manager.db.movies.find_one({'movieId': movie_id})
            if movie:
                print(f"  ✅ ID {movie_id}: {movie.get('title', 'Sin título')}")
            else:
                print(f"  ❌ ID {movie_id}: No encontrada")
        
        # Obtener rango de IDs disponibles
        pipeline = [
            {'$group': {
                '_id': None,
                'min_id': {'$min': '$movieId'},
                'max_id': {'$max': '$movieId'},
                'avg_id': {'$avg': '$movieId'}
            }}
        ]
        
        stats = list(mongo_manager.db.movies.aggregate(pipeline))
        if stats:
            stats = stats[0]
            print(f"\n📈 Estadísticas de IDs:")
            print(f"  ID mínimo: {stats.get('min_id')}")
            print(f"  ID máximo: {stats.get('max_id')}")
            print(f"  ID promedio: {stats.get('avg_id'):.0f}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_movies() 