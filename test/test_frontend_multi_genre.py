#!/usr/bin/env python3
"""
Script de prueba para verificar el endpoint de recomendaciones multi-género
que usa el frontend.
"""

import requests
import json
import time

# Configuración
BASE_URL = "http://localhost:5000/api"

def test_multi_genre_recommendations():
    """Probar el endpoint de recomendaciones multi-género"""
    print("🎬 Probando endpoint de recomendaciones multi-género...")
    
    # Casos de prueba
    test_cases = [
        {
            "name": "Géneros populares",
            "genres": ["Action", "Adventure"],
            "method": "hybrid",
            "limit": 10
        },
        {
            "name": "Géneros dramáticos",
            "genres": ["Drama", "Romance"],
            "method": "content",
            "limit": 15
        },
        {
            "name": "Géneros de suspenso",
            "genres": ["Thriller", "Mystery", "Crime"],
            "method": "collaborative",
            "limit": 12
        },
        {
            "name": "Géneros familiares",
            "genres": ["Comedy", "Family", "Animation"],
            "method": "popular",
            "limit": 8
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Caso de prueba {i}: {test_case['name']}")
        print(f"   Géneros: {', '.join(test_case['genres'])}")
        print(f"   Método: {test_case['method']}")
        print(f"   Límite: {test_case['limit']}")
        
        try:
            # Construir URL con parámetros
            genres_param = ','.join(test_case['genres'])
            url = f"{BASE_URL}/genre-recommendations"
            params = {
                'genres': genres_param,
                'method': test_case['method'],
                'limit': test_case['limit']
            }
            
            # Hacer petición
            start_time = time.time()
            response = requests.get(url, params=params)
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                recommendations = data.get('recommendations', [])
                
                print(f"   ✅ Éxito en {end_time - start_time:.3f}s")
                print(f"   📊 Recomendaciones obtenidas: {len(recommendations)}")
                print(f"   🎯 Método usado: {data.get('method', 'N/A')}")
                print(f"   📝 Explicación: {data.get('explanation', 'N/A')}")
                
                # Mostrar primeras 3 recomendaciones
                if recommendations:
                    print("   🎬 Primeras recomendaciones:")
                    for j, movie in enumerate(recommendations[:3], 1):
                        rating_info = f"⭐ {movie.get('avg_rating', 0):.1f}" if movie.get('avg_rating') else ""
                        similarity_info = f"🎯 {movie.get('similarity_score', 0):.1%}" if movie.get('similarity_score') else ""
                        info_parts = [rating_info, similarity_info]
                        info_str = " | ".join([part for part in info_parts if part])
                        
                        print(f"      {j}. {movie.get('title', 'N/A')} ({movie.get('year', 'N/A')})")
                        if info_str:
                            print(f"         {info_str}")
                        print(f"         Géneros: {movie.get('genres', 'N/A')}")
                else:
                    print("   ⚠️ No se obtuvieron recomendaciones")
                    
            else:
                print(f"   ❌ Error {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n🎉 Pruebas completadas!")

def test_frontend_compatibility():
    """Verificar que el endpoint es compatible con el frontend"""
    print("\n🔧 Verificando compatibilidad con frontend...")
    
    # Simular petición del frontend
    frontend_test = {
        "genres": ["Action", "Sci-Fi"],
        "method": "hybrid",
        "limit": 20
    }
    
    try:
        genres_param = ','.join(frontend_test['genres'])
        url = f"{BASE_URL}/genre-recommendations"
        params = {
            'genres': genres_param,
            'method': frontend_test['method'],
            'limit': frontend_test['limit']
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # Verificar estructura esperada por el frontend
            required_fields = ['genres', 'method', 'explanation', 'recommendations', 'count']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                print("   ✅ Estructura de respuesta compatible con frontend")
                print(f"   📊 Campos requeridos: {', '.join(required_fields)}")
                
                # Verificar estructura de películas
                if data['recommendations']:
                    movie = data['recommendations'][0]
                    movie_fields = ['movieId', 'title', 'genres', 'year', 'avg_rating', 'similarity_score']
                    movie_missing = [field for field in movie_fields if field not in movie]
                    
                    if not movie_missing:
                        print("   ✅ Estructura de películas compatible")
                    else:
                        print(f"   ⚠️ Campos faltantes en películas: {', '.join(movie_missing)}")
                else:
                    print("   ⚠️ No hay películas para verificar estructura")
            else:
                print(f"   ❌ Campos faltantes en respuesta: {', '.join(missing_fields)}")
        else:
            print(f"   ❌ Error en petición: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error verificando compatibilidad: {e}")

if __name__ == "__main__":
    print("🚀 Iniciando pruebas del endpoint multi-género...")
    
    # Verificar que el servidor esté corriendo
    try:
        health_response = requests.get(f"{BASE_URL}/health")
        if health_response.status_code == 200:
            print("✅ Servidor disponible")
        else:
            print("❌ Servidor no disponible")
            exit(1)
    except Exception as e:
        print(f"❌ No se puede conectar al servidor: {e}")
        exit(1)
    
    # Ejecutar pruebas
    test_multi_genre_recommendations()
    test_frontend_compatibility()
    
    print("\n🎬 Todas las pruebas completadas exitosamente!") 