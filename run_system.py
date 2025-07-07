#!/usr/bin/env python3
"""
Script para ejecutar el sistema completo de recomendaciones
"""

import subprocess
import sys
import time
import requests
import os

def check_dependencies():
    """Verificar que las dependencias estén instaladas"""
    try:
        import flask
        import pymongo
        import redis
        import pandas
        import numpy
        import scipy
        print("✅ Todas las dependencias están instaladas")
        return True
    except ImportError as e:
        print(f"❌ Dependencia faltante: {e}")
        print("Ejecuta: pip install -r requirements.txt")
        return False

def check_mongodb():
    """Verificar que MongoDB esté corriendo"""
    try:
        import pymongo
        client = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=5000)
        client.server_info()
        print("✅ MongoDB está corriendo")
        return True
    except Exception as e:
        print(f"❌ MongoDB no está disponible: {e}")
        print("Asegúrate de que MongoDB esté corriendo en localhost:27017")
        return False

def check_redis():
    """Verificar que Redis esté disponible (opcional)"""
    try:
        import redis
        r = redis.from_url("redis://localhost:6379/0")
        r.ping()
        print("✅ Redis está disponible")
        return True
    except Exception as e:
        print(f"⚠️ Redis no está disponible (opcional): {e}")
        print("El sistema funcionará sin Redis, pero con menos optimización")
        return True

def migrate_data():
    """Migrar datos si es necesario"""
    try:
        print("🔄 Verificando datos en MongoDB...")
        import pymongo
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        db = client["movie_recommendations"]
        
        # Verificar si ya hay datos
        movies_count = db.movies.count_documents({})
        if movies_count > 0:
            print(f"✅ Datos ya migrados: {movies_count} películas")
            return True
        
        print("📦 Migrando datos a MongoDB...")
        result = subprocess.run([sys.executable, "scripts/migrate_data.py"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Migración completada")
            return True
        else:
            print(f"❌ Error en migración: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error verificando migración: {e}")
        return False

def start_backend():
    """Iniciar el servidor backend"""
    print("🚀 Iniciando servidor backend...")
    try:
        # Ejecutar el servidor Flask
        process = subprocess.Popen([
            sys.executable, "app_simple.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Esperar a que el servidor esté listo
        for i in range(30):  # 30 segundos máximo
            try:
                response = requests.get("http://localhost:5000/api/health", timeout=2)
                if response.status_code == 200:
                    print("✅ Servidor backend iniciado en http://localhost:5000")
                    return process
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
        
        print("❌ Timeout esperando servidor backend")
        process.terminate()
        return None
        
    except Exception as e:
        print(f"❌ Error iniciando backend: {e}")
        return None

def start_frontend():
    """Iniciar el frontend (Next.js)"""
    print("🎨 Iniciando frontend...")
    try:
        # Verificar si Next.js está instalado
        if not os.path.exists("node_modules"):
            print("📦 Instalando dependencias de Next.js...")
            subprocess.run(["npm", "install"], check=True)
        
        # Iniciar servidor de desarrollo
        process = subprocess.Popen([
            "npm", "run", "dev"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Esperar a que el frontend esté listo
        for i in range(30):  # 30 segundos máximo
            try:
                response = requests.get("http://localhost:3000", timeout=2)
                if response.status_code == 200:
                    print("✅ Frontend iniciado en http://localhost:3000")
                    return process
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
        
        print("❌ Timeout esperando frontend")
        process.terminate()
        return None
        
    except Exception as e:
        print(f"❌ Error iniciando frontend: {e}")
        return None

def main():
    """Función principal"""
    print("🎬 Sistema de Recomendaciones de Películas")
    print("=" * 50)
    
    # Verificar dependencias
    if not check_dependencies():
        return
    
    # Verificar servicios
    if not check_mongodb():
        return
    
    check_redis()
    
    # Migrar datos si es necesario
    if not migrate_data():
        return
    
    # Iniciar backend
    backend_process = start_backend()
    if not backend_process:
        return
    
    # Iniciar frontend
    frontend_process = start_frontend()
    if not frontend_process:
        backend_process.terminate()
        return
    
    print("\n🎉 Sistema iniciado correctamente!")
    print("📱 Frontend: http://localhost:3000")
    print("🔧 Backend: http://localhost:5000")
    print("📊 API Docs: http://localhost:5000/api/health")
    print("\nPresiona Ctrl+C para detener el sistema")
    
    try:
        # Mantener los procesos corriendo
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo sistema...")
        backend_process.terminate()
        frontend_process.terminate()
        print("✅ Sistema detenido")

if __name__ == "__main__":
    main() 