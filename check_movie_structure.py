#!/usr/bin/env python3
"""
Script para verificar la estructura de datos de películas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.mongo_client import mongo_manager

def check_movie_structure():
    """Verificar estructura de datos de películas"""
    print("🔍 Verificando estructura de datos de películas...")
    
    try:
        # Conectar a MongoDB
        if mongo_manager.db is None:
            mongo_manager.connect()
        
        # Obtener una película de ejemplo
        sample_movie = mongo_manager.db.movies.find_one()
        
        if sample_movie:
            print("📋 Estructura de una película:")
            for key, value in sample_movie.items():
                print(f"  {key}: {value} (tipo: {type(value).__name__})")
            
            # Verificar si existe el campo movieId
            movie_id = sample_movie.get('movieId')
            if movie_id is not None:
                print(f"\n✅ Campo 'movieId' encontrado: {movie_id}")
            else:
                print("\n❌ Campo 'movieId' no encontrado")
                
            # Buscar por diferentes campos posibles
            print("\n🔍 Buscando película con ID 1 usando diferentes campos:")
            
            # Intentar con movieId
            movie1 = mongo_manager.db.movies.find_one({'movieId': 1})
            if movie1:
                print("  ✅ Encontrada con 'movieId': 1")
            else:
                print("  ❌ No encontrada con 'movieId': 1")
            
            # Intentar con _id
            movie1_id = mongo_manager.db.movies.find_one({'_id': 1})
            if movie1_id:
                print("  ✅ Encontrada con '_id': 1")
            else:
                print("  ❌ No encontrada con '_id': 1")
            
            # Intentar con id
            movie1_id_alt = mongo_manager.db.movies.find_one({'id': 1})
            if movie1_id_alt:
                print("  ✅ Encontrada con 'id': 1")
            else:
                print("  ❌ No encontrada con 'id': 1")
            
            # Listar todos los campos únicos
            print("\n📊 Campos únicos en la colección movies:")
            pipeline = [
                {'$sample': {'size': 1000}},
                {'$project': {'arrayofkeyvalue': {'$objectToArray': '$$ROOT'}}},
                {'$unwind': '$arrayofkeyvalue'},
                {'$group': {'_id': '$arrayofkeyvalue.k'}},
                {'$sort': {'_id': 1}}
            ]
            
            fields = list(mongo_manager.db.movies.aggregate(pipeline))
            for field in fields:
                print(f"  - {field['_id']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_movie_structure() 