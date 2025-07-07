#!/usr/bin/env python3
"""
Script de prueba para endpoint de películas específicas
"""

import requests
import json

def test_movie_endpoint():
    """Probar endpoint de películas específicas"""
    base_url = "http://localhost:5000"
    
    print("🧪 Probando endpoint de películas específicas...")
    
    # Probar con diferentes IDs de películas
    test_movie_ids = [1, 2, 3, 278752, 100]
    
    for movie_id in test_movie_ids:
        print(f"\n🎬 Probando GET /api/movies/{movie_id}...")
        try:
            response = requests.get(f"{base_url}/api/movies/{movie_id}")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                movie = response.json()
                print(f"✅ Película obtenida: {movie.get('title', 'Sin título')}")
                print(f"   Año: {movie.get('year', 'N/A')}")
                print(f"   Géneros: {movie.get('genres', 'N/A')}")
                print(f"   Estadísticas: {movie.get('stats', {})}")
                print(f"   Películas similares: {len(movie.get('similar_movies', []))}")
                print(f"   Usuarios que calificaron: {movie.get('users_who_rated', 0)}")
            elif response.status_code == 404:
                print(f"⚠️ Película {movie_id} no encontrada")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error conectando al servidor: {e}")
    
    print("\n🏁 Pruebas completadas!")

if __name__ == "__main__":
    test_movie_endpoint() 