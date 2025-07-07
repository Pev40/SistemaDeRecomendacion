#!/usr/bin/env python3
"""
Script para migrar datos CSV a MongoDB
Uso: python scripts/migrate_data.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.mongo_client import mongo_manager
from config import Config
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Función principal de migración"""
    try:
        logger.info("🚀 Iniciando migración de datos a MongoDB...")
        
        # Conectar a MongoDB
        if not mongo_manager.connect():
            logger.error("❌ No se pudo conectar a MongoDB")
            return False
        
        # Crear índices
        logger.info("📊 Creando índices optimizados...")
        mongo_manager.create_indexes()
        
        # Migrar datos
        logger.info("📦 Migrando datos CSV a MongoDB...")
        success = mongo_manager.migrate_csv_to_mongodb('data')
        
        if success:
            logger.info("✅ Migración completada exitosamente!")
            
            # Mostrar estadísticas
            stats = mongo_manager.db.command("dbStats")
            logger.info(f"📈 Estadísticas de la base de datos:")
            logger.info(f"   - Colecciones: {stats.get('collections', 0)}")
            logger.info(f"   - Tamaño de datos: {stats.get('dataSize', 0)} bytes")
            logger.info(f"   - Tamaño de almacenamiento: {stats.get('storageSize', 0)} bytes")
            
            return True
        else:
            logger.error("❌ Error durante la migración")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error en migración: {e}")
        return False
    finally:
        mongo_manager.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 