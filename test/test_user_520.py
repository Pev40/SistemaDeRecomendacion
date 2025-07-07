#!/usr/bin/env python3
"""
Script específico para probar el usuario 520
"""

import requests
import json

# Configuración
BASE_URL = "http://localhost:5000/api"

def test_user_520():
    """Probar específicamente el usuario 520"""
    print("👤 Probando usuario 520...")
    
    # Probar con diferentes métodos
    methods = ['cosine', 'euclidean', 'pearson', 'manhattan']
    
    for method in methods:
        print(f"\n📋 Probando método: {method}")
        
        try:
            url = f"{BASE_URL}/user-recommendations/520"
            params = {
                'method': method,
                'limit': 10
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                recommendations = data.get('recommendations', [])
                
                print(f"   ✅ Éxito")
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
    
    print("\n🎉 Prueba completada!")

if __name__ == "__main__":
    print("🚀 Iniciando prueba específica del usuario 520...")
    
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
    
    # Ejecutar prueba
    test_user_520()
    
    print("\n👤 Prueba completada!") 