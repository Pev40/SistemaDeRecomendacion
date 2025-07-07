#!/usr/bin/env python3
"""
Script para probar el endpoint /api/stats
"""

import requests
import json
import sys

def test_stats_endpoint():
    """Probar el endpoint /api/stats"""
    try:
        # Probar el endpoint
        response = requests.get('http://localhost:5000/api/stats')
        
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ Endpoint /api/stats funciona correctamente")
            print("\n📊 Estadísticas del sistema:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se puede conectar al servidor")
        print("Asegúrate de que el servidor Flask esté corriendo en http://localhost:5000")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

def test_health_endpoint():
    """Probar el endpoint /api/health"""
    try:
        response = requests.get('http://localhost:5000/api/health')
        print(f"\n🏥 Health Check:")
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Estado: {data.get('status', 'unknown')}")
            print(f"Inicializado: {data.get('initialized', False)}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error en health check: {e}")

if __name__ == "__main__":
    print("🧪 Probando endpoint /api/stats...")
    test_stats_endpoint()
    test_health_endpoint() 