#!/usr/bin/env python3
"""
Script de prueba para endpoints de géneros
"""

import requests
import json

def test_genres_endpoints():
    """Probar endpoints de géneros"""
    base_url = "http://localhost:5000"
    
    print("🧪 Probando endpoints de géneros...")
    
    # Probar /api/genres
    print("\n📋 Probando GET /api/genres...")
    try:
        response = requests.get(f"{base_url}/api/genres")
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            genres = response.json()
            print(f"✅ Géneros obtenidos: {len(genres)} géneros")
            print("Primeros 5 géneros:")
            for i, genre in enumerate(genres[:5]):
                print(f"  {i+1}. {genre['genre']}: {genre['count']} películas")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error conectando al servidor: {e}")
    
    # Probar /api/genres/Action
    print("\n🎬 Probando GET /api/genres/Action...")
    try:
        response = requests.get(f"{base_url}/api/genres/Action")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            movies = response.json()
            print(f"✅ Películas de Action obtenidas: {len(movies)} películas")
            print("Primeras 3 películas:")
            for i, movie in enumerate(movies[:3]):
                print(f"  {i+1}. {movie.get('title', 'Sin título')} ({movie.get('year', 'N/A')})")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error conectando al servidor: {e}")
    
    # Probar /api/genres/Comedy
    print("\n😄 Probando GET /api/genres/Comedy...")
    try:
        response = requests.get(f"{base_url}/api/genres/Comedy")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            movies = response.json()
            print(f"✅ Películas de Comedy obtenidas: {len(movies)} películas")
            print("Primeras 3 películas:")
            for i, movie in enumerate(movies[:3]):
                print(f"  {i+1}. {movie.get('title', 'Sin título')} ({movie.get('year', 'N/A')})")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error conectando al servidor: {e}")
    
    print("\n🏁 Pruebas completadas!")

if __name__ == "__main__":
    test_genres_endpoints() 