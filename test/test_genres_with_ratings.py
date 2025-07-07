#!/usr/bin/env python3
"""
Script de prueba para endpoint de géneros con información de rating
"""

import requests
import json

def test_genres_with_ratings():
    """Probar endpoint de géneros con información de rating"""
    base_url = "http://localhost:5000"
    
    print("🧪 Probando endpoint de géneros con información de rating...")
    
    # Probar con diferentes géneros
    test_genres = ['Action', 'Comedy', 'Drama', 'Horror', 'Romance']
    
    for genre in test_genres:
        print(f"\n🎬 Probando GET /api/genres/{genre}...")
        try:
            response = requests.get(f"{base_url}/api/genres/{genre}?limit=5")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                movies = response.json()
                print(f"✅ Películas de {genre} obtenidas: {len(movies)} películas")
                print("Primeras 3 películas:")
                for i, movie in enumerate(movies[:3]):
                    print(f"  {i+1}. {movie.get('title', 'Sin título')} ({movie.get('year', 'N/A')})")
                    print(f"     Rating: {movie.get('avg_rating', 'N/A'):.2f} ⭐ ({movie.get('total_ratings', 0)} calificaciones)")
                    print(f"     Similitud: {movie.get('similarity_score', 'N/A'):.2f}")
                    print(f"     Géneros: {movie.get('genres', 'N/A')}")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error conectando al servidor: {e}")
    
    print("\n🏁 Pruebas completadas!")

if __name__ == "__main__":
    test_genres_with_ratings() 