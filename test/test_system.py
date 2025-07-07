#!/usr/bin/env python3
"""
Script de prueba para verificar el sistema completo
"""

import requests
import time
import json
from datetime import datetime

# Configuración
BASE_URL = "http://localhost:5000/api"
FRONTEND_URL = "http://localhost:3000"

def test_backend_health():
    """Probar salud del backend"""
    print("🔍 Probando salud del backend...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend saludable: {data.get('status', 'OK')}")
            return True
        else:
            print(f"❌ Backend no responde: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error conectando al backend: {e}")
        return False

def test_frontend_health():
    """Probar salud del frontend"""
    print("🎨 Probando salud del frontend...")
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print("✅ Frontend saludable")
            return True
        else:
            print(f"❌ Frontend no responde: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error conectando al frontend: {e}")
        return False

def test_api_endpoints():
    """Probar endpoints de la API"""
    print("🔧 Probando endpoints de la API...")
    
    endpoints = [
        ("/stats", "Estadísticas del sistema"),
        ("/methods", "Métodos de similitud"),
        ("/genres", "Géneros disponibles"),
        ("/movies?limit=5", "Películas (limit=5)"),
        ("/search?limit=3", "Búsqueda (limit=3)"),
    ]
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {description}: {len(data) if isinstance(data, list) else 'OK'}")
            else:
                print(f"❌ {description}: {response.status_code}")
        except Exception as e:
            print(f"❌ Error en {description}: {e}")

def test_recommendations():
    """Probar sistema de recomendaciones"""
    print("🎯 Probando sistema de recomendaciones...")
    
    # Métodos de similitud
    methods = ["cosine", "euclidean", "manhattan", "pearson"]
    
    for method in methods:
        try:
            # Usar una película conocida (Toy Story)
            response = requests.get(
                f"{BASE_URL}/recommendations/1?method={method}&limit=3",
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                recommendations = data.get('recommendations', [])
                print(f"✅ {method.upper()}: {len(recommendations)} recomendaciones")
                
                # Mostrar primera recomendación
                if recommendations:
                    first_rec = recommendations[0]
                    print(f"   📽️ {first_rec.get('title', 'N/A')} (sim: {first_rec.get('similarity', 'N/A'):.3f})")
            else:
                print(f"❌ {method.upper()}: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error en {method}: {e}")

def test_similarity_comparison():
    """Probar comparación de similitud"""
    print("🔍 Probando comparación de similitud...")
    
    try:
        # Comparar Toy Story (1) con Jumanji (2)
        response = requests.get(
            f"{BASE_URL}/similarity/1/2?method=cosine",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            similarity = data.get('similarity', 0)
            print(f"✅ Similitud Toy Story vs Jumanji: {similarity:.3f}")
        else:
            print(f"❌ Comparación de similitud: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error en comparación: {e}")

def test_genre_recommendations():
    """Probar recomendaciones por género"""
    print("🏷️ Probando recomendaciones por género...")
    
    try:
        # Probar con género "Action"
        response = requests.get(
            f"{BASE_URL}/genres/Action?limit=3",
            timeout=10
        )
        
        if response.status_code == 200:
            movies = response.json()
            print(f"✅ Películas de Action: {len(movies)} encontradas")
            
            if movies:
                first_movie = movies[0]
                print(f"   📽️ {first_movie.get('title', 'N/A')}")
        else:
            print(f"❌ Recomendaciones por género: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error en recomendaciones por género: {e}")

def test_user_recommendations():
    """Probar recomendaciones por usuario"""
    print("👤 Probando recomendaciones por usuario...")
    
    try:
        # Usar usuario 1
        response = requests.get(
            f"{BASE_URL}/user-recommendations/1?method=cosine&limit=3",
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            recommendations = data.get('recommendations', [])
            print(f"✅ Recomendaciones para usuario 1: {len(recommendations)} encontradas")
            
            if recommendations:
                first_rec = recommendations[0]
                print(f"   📽️ {first_rec.get('title', 'N/A')} (sim: {first_rec.get('similarity', 'N/A'):.3f})")
        else:
            print(f"❌ Recomendaciones por usuario: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error en recomendaciones por usuario: {e}")

def test_performance():
    """Probar rendimiento del sistema"""
    print("⚡ Probando rendimiento...")
    
    # Probar tiempo de respuesta para recomendaciones
    methods = ["cosine", "euclidean", "manhattan", "pearson"]
    
    for method in methods:
        try:
            start_time = time.time()
            response = requests.get(
                f"{BASE_URL}/recommendations/1?method={method}&limit=10",
                timeout=30
            )
            end_time = time.time()
            
            if response.status_code == 200:
                duration = end_time - start_time
                print(f"✅ {method.upper()}: {duration:.3f}s")
            else:
                print(f"❌ {method.upper()}: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error en rendimiento {method}: {e}")

def generate_report():
    """Generar reporte de pruebas"""
    print("\n" + "="*60)
    print("📊 REPORTE DE PRUEBAS DEL SISTEMA")
    print("="*60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Backend: {BASE_URL}")
    print(f"Frontend: {FRONTEND_URL}")
    print("-"*60)

def main():
    """Función principal de pruebas"""
    generate_report()
    
    # Ejecutar todas las pruebas
    tests = [
        test_backend_health,
        test_frontend_health,
        test_api_endpoints,
        test_recommendations,
        test_similarity_comparison,
        test_genre_recommendations,
        test_user_recommendations,
        test_performance,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Error en prueba: {e}")
    
    print("\n" + "="*60)
    print(f"📈 RESULTADOS: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Sistema funcionando correctamente!")
    elif passed >= total * 0.8:
        print("⚠️ Sistema funcionando con algunos problemas menores")
    else:
        print("❌ Sistema con problemas significativos")
    
    print("="*60)

if __name__ == "__main__":
    main() 