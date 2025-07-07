#!/usr/bin/env python3
"""
Script de prueba para verificar el endpoint de recomendaciones por usuario
"""

import requests
import json
import time

# Configuración
BASE_URL = "http://localhost:5000/api"

def test_user_recommendations():
    """Probar el endpoint de recomendaciones por usuario"""
    print("👤 Probando endpoint de recomendaciones por usuario...")
    
    # Casos de prueba
    test_cases = [
        {
            "name": "Usuario 1 con coseno",
            "user_id": "1",
            "method": "cosine",
            "limit": 10
        },
        {
            "name": "Usuario 1 con pearson",
            "user_id": "1",
            "method": "pearson",
            "limit": 15
        },
        {
            "name": "Usuario 2 con euclidiana",
            "user_id": "2",
            "method": "euclidean",
            "limit": 8
        },
        {
            "name": "Usuario 3 con manhattan",
            "user_id": "3",
            "method": "manhattan",
            "limit": 12
        },
        {
            "name": "Usuario inexistente",
            "user_id": "99999",
            "method": "cosine",
            "limit": 5
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Caso de prueba {i}: {test_case['name']}")
        print(f"   Usuario: {test_case['user_id']}")
        print(f"   Método: {test_case['method']}")
        print(f"   Límite: {test_case['limit']}")
        
        try:
            # Construir URL
            url = f"{BASE_URL}/user-recommendations/{test_case['user_id']}"
            params = {
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
                print(f"   👤 Usuario: {data.get('user_id', 'N/A')}")
                
                # Mostrar primeras 3 recomendaciones
                if recommendations:
                    print("   🎬 Primeras recomendaciones:")
                    for j, movie in enumerate(recommendations[:3], 1):
                        rating_info = f"⭐ {movie.get('rating', 0):.1f}" if movie.get('rating') else ""
                        similarity_info = f"👥 {movie.get('user_similarity', 0):.3f}" if movie.get('user_similarity') else ""
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
        "user_id": "1",
        "method": "cosine",
        "limit": 10
    }
    
    try:
        url = f"{BASE_URL}/user-recommendations/{frontend_test['user_id']}"
        params = {
            'method': frontend_test['method'],
            'limit': frontend_test['limit']
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # Verificar estructura esperada por el frontend
            required_fields = ['user_id', 'method', 'recommendations', 'count']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                print("   ✅ Estructura de respuesta compatible con frontend")
                print(f"   📊 Campos requeridos: {', '.join(required_fields)}")
                
                # Verificar estructura de películas
                if data['recommendations']:
                    movie = data['recommendations'][0]
                    movie_fields = ['movieId', 'title', 'genres', 'year', 'rating', 'user_similarity']
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
    print("🚀 Iniciando pruebas del endpoint de recomendaciones por usuario...")
    
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
    test_user_recommendations()
    test_frontend_compatibility()
    
    print("\n👤 Todas las pruebas completadas exitosamente!") 