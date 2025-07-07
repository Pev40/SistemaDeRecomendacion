#!/usr/bin/env python3
"""
Script de prueba para endpoint de recomendaciones multi-género
"""

import requests
import json

def test_multi_genre_recommendations():
    """Probar endpoint de recomendaciones multi-género"""
    base_url = "http://localhost:5000"
    
    print("🧪 Probando endpoint de recomendaciones multi-género...")
    
    # Probar con diferentes combinaciones de géneros
    test_cases = [
        {'genres': ['Action', 'Adventure'], 'method': 'content', 'limit': 5},
        {'genres': ['Comedy', 'Romance'], 'method': 'hybrid', 'limit': 5},
        {'genres': ['Drama', 'Thriller', 'Mystery'], 'method': 'popular', 'limit': 5},
        {'genres': ['Sci-Fi', 'Fantasy'], 'method': 'collaborative', 'limit': 5},
    ]
    
    for test_case in test_cases:
        genres = ','.join(test_case['genres'])
        method = test_case['method']
        limit = test_case['limit']
        
        print(f"\n🎬 Probando GET /api/genre-recommendations?genres={genres}&method={method}&limit={limit}...")
        try:
            response = requests.get(f"{base_url}/api/genre-recommendations", 
                                 params={'genres': genres, 'method': method, 'limit': limit})
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Recomendaciones obtenidas: {data['count']} películas")
                print(f"   Géneros: {data['genres']}")
                print(f"   Método: {data['method']}")
                print(f"   Explicación: {data['explanation']}")
                
                if data['recommendations']:
                    print("   Primeras 3 recomendaciones:")
                    for i, rec in enumerate(data['recommendations'][:3]):
                        print(f"     {i+1}. {rec.get('title', 'Sin título')} ({rec.get('year', 'N/A')})")
                        print(f"        Rating: {rec.get('avg_rating', 'N/A'):.2f} ⭐ ({rec.get('total_ratings', 0)} calificaciones)")
                        print(f"        Similitud: {rec.get('similarity_score', 'N/A'):.2f}")
                        print(f"        Géneros: {rec.get('genres', 'N/A')}")
                else:
                    print("   ⚠️ No se encontraron recomendaciones")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error conectando al servidor: {e}")
    
    print("\n🏁 Pruebas completadas!")

if __name__ == "__main__":
    test_multi_genre_recommendations() 