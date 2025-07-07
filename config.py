import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # MongoDB
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    MONGO_DB = os.getenv('MONGO_DB', 'movie_recommendations')
    
    # Redis
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # Procesamiento
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', '1000'))
    CACHE_TTL = int(os.getenv('CACHE_TTL', '3600'))  # 1 hora
    
    # Modelos
    MODEL_CACHE_DIR = os.getenv('MODEL_CACHE_DIR', './models')
    SVD_COMPONENTS = int(os.getenv('SVD_COMPONENTS', '50'))
    
    # API
    RATE_LIMIT = os.getenv('RATE_LIMIT', '100/minute')
    MAX_RECOMMENDATIONS = int(os.getenv('MAX_RECOMMENDATIONS', '50')) 