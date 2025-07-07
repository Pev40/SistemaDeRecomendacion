#!/usr/bin/env python3
"""
Script de prueba para endpoint de recomendaciones
"""

import requests
import json

def test_recommendations_endpoint():
    """Probar endpoint de recomendaciones"""
    base_url = "http://localhost:5000"
    
    print("🧪 Probando endpoint de recomendaciones...")
    
    # Probar con diferentes métodos y películas
    test_cases = [
        {'movie_id': 1, 'method': 'content', 'limit': 5},
        {'movie_id': 2, 'method': 'collaborative', 'limit': 5},
        {'movie_id': 3, 'method': 'popular', 'limit': 5},
        {'movie_id': 1299, 'method': 'hybrid', 'limit': 10},
        {'movie_id': 100, 'method': 'content', 'limit': 5},
    ]
    
    for test_case in test_cases:
        movie_id = test_case['movie_id']
        method = test_case['method']
        limit = test_case['limit']
        
        print(f"\n🎬 Probando GET /api/recommendations/{movie_id}?method={method}&limit={limit}...")
        try:
            response = requests.get(f"{base_url}/api/recommendations/{movie_id}", 
                                 params={'method': method, 'limit': limit})
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Recomendaciones obtenidas: {data['count']} películas")
                print(f"   Método: {data['method']}")
                print(f"   Explicación: {data['explanation']}")
                
                if data['recommendations']:
                    print("   Primeras 3 recomendaciones:")
                    for i, rec in enumerate(data['recommendations'][:3]):
                        print(f"     {i+1}. {rec.get('title', 'Sin título')} ({rec.get('year', 'N/A')})")
                        if 'similarity_score' in rec:
                            print(f"        Similitud: {rec['similarity_score']:.3f}")
                        elif 'avg_rating' in rec:
                            print(f"        Rating promedio: {rec['avg_rating']:.2f}")
                        elif 'hybrid_score' in rec:
                            print(f"        Puntuación híbrida: {rec['hybrid_score']:.2f}")
                else:
                    print("   ⚠️ No se encontraron recomendaciones")
            elif response.status_code == 404:
                print(f"⚠️ Película {movie_id} no encontrada")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error conectando al servidor: {e}")
    
    print("\n🏁 Pruebas completadas!")

if __name__ == "__main__":
    test_recommendations_endpoint() 