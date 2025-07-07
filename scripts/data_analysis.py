import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
import requests
import io

def load_data():
    """Cargar los datos desde las URLs proporcionadas"""
    print("Cargando datos...")
    
    # Cargar movies.csv localmente
    movies_df = pd.read_csv("datasets/movies.csv")
    
    # Cargar links.csv localmente
    links_df = pd.read_csv("datasets/links.csv")
    
    # Cargar ratings.csv localmente
    #ratings_df = pd.read_csv("datasets/ratings.csv")
    
    print(f"Películas cargadas: {len(movies_df)}")
    print(f"Enlaces cargados: {len(links_df)}")
    
    return movies_df, links_df

def preprocess_data(movies_df):
    """Preprocesar los datos para el análisis"""
    print("Preprocesando datos...")
    
    # Limpiar y procesar géneros
    movies_df['genres'] = movies_df['genres'].fillna('Unknown')
    movies_df['year'] = movies_df['title'].str.extract(r'$$(\d{4})$$').astype(float)
    movies_df['clean_title'] = movies_df['title'].str.replace(r'\s*$$\d{4}$$', '', regex=True)
    
    # Crear matriz de géneros
    genres_expanded = movies_df['genres'].str.get_dummies(sep='|')
    
    return movies_df, genres_expanded

def create_genre_clusters(movies_df, genres_expanded, n_clusters=10):
    """Crear clusters basados en géneros usando K-means"""
    print(f"Creando {n_clusters} clusters de géneros...")
    
    # Aplicar K-means
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    movies_df['genre_cluster'] = kmeans.fit_predict(genres_expanded)
    
    # Analizar clusters
    cluster_analysis = []
    for i in range(n_clusters):
        cluster_movies = movies_df[movies_df['genre_cluster'] == i]
        top_genres = genres_expanded[movies_df['genre_cluster'] == i].sum().sort_values(ascending=False).head(3)
        
        cluster_info = {
            'cluster_id': i,
            'movie_count': len(cluster_movies),
            'top_genres': list(top_genres.index),
            'sample_movies': list(cluster_movies['clean_title'].head(5))
        }
        cluster_analysis.append(cluster_info)
    
    return movies_df, kmeans, cluster_analysis

def content_based_similarity(movies_df):
    """Crear matriz de similitud basada en contenido"""
    print("Calculando similitud basada en contenido...")
    
    # Vectorizar géneros usando TF-IDF
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(movies_df['genres'])
    
    # Calcular similitud coseno
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    
    return cosine_sim, tfidf

def analyze_data():
    """Función principal de análisis"""
    # Cargar datos
    movies_df, links_df = load_data()
    
    # Preprocesar
    movies_df, genres_expanded = preprocess_data(movies_df)
    
    # Crear clusters
    movies_df, kmeans_model, cluster_analysis = create_genre_clusters(movies_df, genres_expanded)
    
    # Calcular similitud
    cosine_sim, tfidf_model = content_based_similarity(movies_df)
    
    # Mostrar análisis de clusters
    print("\n=== ANÁLISIS DE CLUSTERS ===")
    for cluster in cluster_analysis:
        print(f"\nCluster {cluster['cluster_id']}:")
        print(f"  Películas: {cluster['movie_count']}")
        print(f"  Géneros principales: {', '.join(cluster['top_genres'])}")
        print(f"  Ejemplos: {', '.join(cluster['sample_movies'])}")
    
    # Estadísticas generales
    print(f"\n=== ESTADÍSTICAS GENERALES ===")
    print(f"Total de películas: {len(movies_df)}")
    print(f"Géneros únicos: {len(movies_df['genres'].str.split('|').explode().unique())}")
    print(f"Rango de años: {movies_df['year'].min():.0f} - {movies_df['year'].max():.0f}")
    
    return {
        'movies_df': movies_df,
        'links_df': links_df,
        'genres_expanded': genres_expanded,
        'kmeans_model': kmeans_model,
        'cluster_analysis': cluster_analysis,
        'cosine_sim': cosine_sim,
        'tfidf_model': tfidf_model
    }

if __name__ == "__main__":
    results = analyze_data()
