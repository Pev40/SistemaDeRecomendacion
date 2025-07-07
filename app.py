from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import StandardScaler
from scipy.sparse import csr_matrix
import pickle
import os
import random
from collections import defaultdict
import polars as pl
app = Flask(__name__)

class FastMovieRecommendationSystem:
    def __init__(self, data_folder='data'):
        self.data_folder = data_folder
        self.movies_df = None
        self.ratings_df = None
        self.tags_df = None
        self.links_df = None

        self.content_similarity_matrix = None
        self.user_item_matrix = None
        self.svd_model = None
        self.tfidf_vectorizer = None
        self.genre_similarity_matrix = None

        self.movie_to_idx = {}
        self.idx_to_movie = {}
        self.genre_movies = defaultdict(list)

        self.is_loaded = False
        
    def load_all_data(self):
        print("🎬 Cargando todos los datasets...")
        try:
            self.movies_df = pl.read_csv(os.path.join(self.data_folder, 'movies.csv'))
            self.ratings_df = pl.read_csv(os.path.join(self.data_folder, 'ratings.csv'))
            self.tags_df = pl.read_csv(os.path.join(self.data_folder, 'tags.csv'))
            self.links_df = pl.read_csv(os.path.join(self.data_folder, 'links.csv'))

            print(f"✅ Películas: {self.movies_df.height}")
            print(f"✅ Ratings: {self.ratings_df.height}")
            print(f"✅ Tags: {self.tags_df.height}")
            print(f"✅ Links: {self.links_df.height}")

            self._preprocess_data()
            self._build_fast_models()
            self.is_loaded = True
            print("🚀 Sistema de recomendaciones listo!")
        except Exception as e:
            print(f"❌ Error cargando datos: {e}")
         
    def _preprocess_data(self):
        print("🔧 Preprocesando datos...")

        self.movies_df = self.movies_df.with_columns([
            pl.col('genres').fill_null('Unknown'),
            pl.col('title').str.extract(r'(\d{4})$', 1).cast(pl.Int32).alias('year'),
            pl.col('title').str.replace(r'\s*\(\d{4}\)$', '').alias('clean_title'),
            pl.col('movieId').cast(pl.Utf8)
        ])
        self.ratings_df = self.ratings_df.with_columns(pl.col('movieId').cast(pl.Utf8))
        self.tags_df = self.tags_df.with_columns(pl.col('movieId').cast(pl.Utf8))

        self.movie_to_idx = {row['movieId']: idx for idx, row in enumerate(self.movies_df.iter_rows(named=True))}
        self.idx_to_movie = {idx: row['movieId'] for idx, row in enumerate(self.movies_df.iter_rows(named=True))}

        for row in self.movies_df.iter_rows(named=True):
            genres = row['genres'].split('|')
            for genre in genres:
                if genre != 'Unknown':
                    self.genre_movies[genre].append(row['movieId'])

        existing_movies = set(self.movies_df['movieId'].to_list())
        self.ratings_df = self.ratings_df.filter(pl.col('movieId').is_in(existing_movies))

        print(f"🎯 Géneros únicos: {len(self.genre_movies)}")
        print(f"🎯 Usuarios únicos: {self.ratings_df['userId'].n_unique()}")
   
    def _build_fast_models(self):
        """Construir modelos optimizados para velocidad"""
        print("⚡ Construyendo modelos rápidos...")
        
        # 1. Modelo de similitud por contenido (TF-IDF + Coseno)
        self._build_content_similarity()
        
        # 2. Modelo colaborativo (SVD para factorización de matriz)
        self._build_collaborative_model()
        
        # 3. Modelo híbrido con tags
        self._build_tag_enhanced_model()
        
    def _build_content_similarity(self):
        print("📊 Construyendo similitud de contenido...")
        genres_list = self.movies_df['genres'].to_list()
        self.tfidf_vectorizer = TfidfVectorizer(token_pattern=r'[^|]+')
        tfidf_matrix = self.tfidf_vectorizer.fit_transform(genres_list)
        self.content_similarity_matrix = cosine_similarity(tfidf_matrix)
        print(f"✅ Matriz de similitud: {self.content_similarity_matrix.shape}")

    def _build_collaborative_model(self):
        print("🤝 Construyendo modelo colaborativo...")
        # Polars no tiene pivot_table, así que lo hacemos manualmente
        ratings_pd = self.ratings_df.to_pandas()
        user_movie_ratings = ratings_pd.pivot_table(
            index='userId',
            columns='movieId',
            values='rating',
            fill_value=0
        )
        min_ratings = 10
        user_counts = (user_movie_ratings > 0).sum(axis=1)
        movie_counts = (user_movie_ratings > 0).sum(axis=0)
        active_users = user_counts[user_counts >= min_ratings].index
        popular_movies = movie_counts[movie_counts >= min_ratings].index
        filtered_matrix = user_movie_ratings.loc[active_users, popular_movies]
        self.svd_model = TruncatedSVD(n_components=50, random_state=42)
        self.user_item_matrix = self.svd_model.fit_transform(filtered_matrix)
        self.active_users = list(active_users)
        self.popular_movies = list(popular_movies)
        print(f"✅ Modelo SVD: {self.user_item_matrix.shape}")

       
    def _build_tag_enhanced_model(self):
        print("🏷️ Procesando tags...")
        tags_pd = self.tags_df.to_pandas()
        movie_tags = tags_pd.groupby('movieId')['tag'].apply(lambda x: ' '.join(x.str.lower())).to_dict()
        enhanced_features = []
        for row in self.movies_df.iter_rows(named=True):
            features = row['genres']
            if row['movieId'] in movie_tags:
                features += ' ' + movie_tags[row['movieId']]
            enhanced_features.append(features)
        enhanced_tfidf = TfidfVectorizer(max_features=1000, stop_words='english')
        enhanced_matrix = enhanced_tfidf.fit_transform(enhanced_features)
        self.genre_similarity_matrix = cosine_similarity(enhanced_matrix)
        print("✅ Modelo con tags completado")
        
    def get_random_movies_by_genre(self, limit=20):
        selected_movies = []
        used_genres = set()
        available_genres = list(self.genre_movies.keys())
        random.shuffle(available_genres)
        for genre in available_genres:
            if len(selected_movies) >= limit:
                break
            genre_movies = self.genre_movies[genre]
            if genre_movies:
                random_movie_id = random.choice(genre_movies)
                movie_info = next(row for row in self.movies_df.iter_rows(named=True) if row['movieId'] == random_movie_id)
                movie_genres = set(movie_info['genres'].split('|'))
                if not movie_genres.intersection(used_genres):
                    selected_movies.append({
                        'movieId': movie_info['movieId'],
                        'title': movie_info['title'],
                        'genres': movie_info['genres'],
                        'year': int(movie_info['year']) if movie_info['year'] else None,
                        'clean_title': movie_info['clean_title']
                    })
                    used_genres.update(movie_genres)
        return selected_movies
    
    def get_fast_recommendations(self, movie_id, method='hybrid', n_recommendations=10):
        """Recomendaciones ultra rápidas"""
        try:
            if movie_id not in self.movie_to_idx:
                return []
                
            movie_idx = self.movie_to_idx[movie_id]
            
            if method == 'content':
                return self._content_recommendations(movie_idx, n_recommendations)
            elif method == 'collaborative':
                return self._collaborative_recommendations(movie_id, n_recommendations)
            elif method == 'tags':
                return self._tag_recommendations(movie_idx, n_recommendations)
            else:  # hybrid
                return self._hybrid_recommendations(movie_id, movie_idx, n_recommendations)
                
        except Exception as e:
            print(f"Error en recomendaciones: {e}")
            return []
    
    def _content_recommendations(self, movie_idx, n_recommendations):
        """Recomendaciones por similitud de contenido"""
        similarities = self.content_similarity_matrix[movie_idx]
        similar_indices = similarities.argsort()[::-1][1:n_recommendations+1]
        
        recommendations = []
        for idx in similar_indices:
            movie_id = self.idx_to_movie[idx]
            movie_info = self.movies_df[self.movies_df['movieId'] == movie_id].iloc[0]
            recommendations.append({
                'movieId': movie_id,
                'title': movie_info['title'],
                'genres': movie_info['genres'],
                'year': movie_info['year']
            })
        
        return recommendations
    
    def _collaborative_recommendations(self, movie_id, n_recommendations):
        """Recomendaciones colaborativas usando SVD"""
        if movie_id not in self.popular_movies:
            return []
        
        # Encontrar usuarios que calificaron esta película
        movie_ratings = self.ratings_df[self.ratings_df['movieId'] == movie_id]
        similar_users = movie_ratings['userId'].tolist()
        
        # Obtener películas mejor calificadas por usuarios similares
        similar_user_ratings = self.ratings_df[
            (self.ratings_df['userId'].isin(similar_users)) & 
            (self.ratings_df['movieId'] != movie_id) &
            (self.ratings_df['rating'] >= 4.0)
        ]
        
        # Agrupar por película y calcular promedio
        movie_scores = similar_user_ratings.groupby('movieId').agg({
            'rating': ['mean', 'count']
        }).reset_index()
        
        movie_scores.columns = ['movieId', 'avg_rating', 'rating_count']
        movie_scores = movie_scores[movie_scores['rating_count'] >= 3]
        movie_scores = movie_scores.sort_values('avg_rating', ascending=False)
        
        recommendations = []
        for _, row in movie_scores.head(n_recommendations).iterrows():
            movie_info = self.movies_df[self.movies_df['movieId'] == row['movieId']]
            if not movie_info.empty:
                movie_info = movie_info.iloc[0]
                recommendations.append({
                    'movieId': row['movieId'],
                    'title': movie_info['title'],
                    'genres': movie_info['genres'],
                    'year': movie_info['year']
                })
        
        return recommendations
    
    def _tag_recommendations(self, movie_idx, n_recommendations):
        """Recomendaciones basadas en tags"""
        similarities = self.genre_similarity_matrix[movie_idx]
        similar_indices = similarities.argsort()[::-1][1:n_recommendations+1]
        
        recommendations = []
        for idx in similar_indices:
            movie_id = self.idx_to_movie[idx]
            movie_info = self.movies_df[self.movies_df['movieId'] == movie_id].iloc[0]
            recommendations.append({
                'movieId': movie_id,
                'title': movie_info['title'],
                'genres': movie_info['genres'],
                'year': movie_info['year']
            })
        
        return recommendations
    
    def _hybrid_recommendations(self, movie_id, movie_idx, n_recommendations):
        """Recomendaciones híbridas combinando todos los métodos"""
        # Obtener recomendaciones de cada método
        content_recs = self._content_recommendations(movie_idx, n_recommendations)
        collab_recs = self._collaborative_recommendations(movie_id, n_recommendations)
        tag_recs = self._tag_recommendations(movie_idx, n_recommendations)
        
        # Combinar y puntuar
        all_recommendations = {}
        
        # Puntuar recomendaciones de contenido
        for i, rec in enumerate(content_recs):
            movie_id = rec['movieId']
            score = (n_recommendations - i) * 0.4  # Peso 40%
            all_recommendations[movie_id] = all_recommendations.get(movie_id, 0) + score
        
        # Puntuar recomendaciones colaborativas
        for i, rec in enumerate(collab_recs):
            movie_id = rec['movieId']
            score = (n_recommendations - i) * 0.4  # Peso 40%
            all_recommendations[movie_id] = all_recommendations.get(movie_id, 0) + score
        
        # Puntuar recomendaciones por tags
        for i, rec in enumerate(tag_recs):
            movie_id = rec['movieId']
            score = (n_recommendations - i) * 0.2  # Peso 20%
            all_recommendations[movie_id] = all_recommendations.get(movie_id, 0) + score
        
        # Ordenar por puntuación
        sorted_recommendations = sorted(
            all_recommendations.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:n_recommendations]
        
        # Formatear resultados
        recommendations = []
        for movie_id, score in sorted_recommendations:
            movie_info = self.movies_df[self.movies_df['movieId'] == movie_id].iloc[0]
            recommendations.append({
                'movieId': movie_id,
                'title': movie_info['title'],
                'genres': movie_info['genres'],
                'year': movie_info['year']
            })
        
        return recommendations
    
    def search_movies(self, query, limit=20):
        """Búsqueda rápida de películas"""
        if not query:
            return self.get_random_movies_by_genre(limit)
        
        # Búsqueda por título
        mask = self.movies_df['clean_title'].str.contains(query, case=False, na=False)
        results = self.movies_df[mask].head(limit)
        
        return results[['movieId', 'title', 'genres', 'year', 'clean_title']].to_dict('records')
    
    def get_movies_by_genre(self, genre, limit=20):
        """Obtener películas por género específico"""
        if genre not in self.genre_movies:
            return []
        
        genre_movie_ids = self.genre_movies[genre][:limit]
        movies = []
        
        for movie_id in genre_movie_ids:
            movie_info = self.movies_df[self.movies_df['movieId'] == movie_id].iloc[0]
            movies.append({
                'movieId': movie_id,
                'title': movie_info['title'],
                'genres': movie_info['genres'],
                'year': movie_info['year'],
                'clean_title': movie_info['clean_title']
            })
        
        return movies
    
    def get_available_genres(self):
        """Obtener lista de géneros disponibles"""
        return sorted(list(self.genre_movies.keys()))

# Instancia global del sistema
recommendation_system = FastMovieRecommendationSystem()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/init')
def initialize_system():
    """Inicializar el sistema de recomendaciones"""
    if not recommendation_system.is_loaded:
        recommendation_system.load_all_data()
    
    return jsonify({
        'loaded': recommendation_system.is_loaded,
        'total_movies': len(recommendation_system.movies_df) if recommendation_system.is_loaded else 0,
        'total_ratings': len(recommendation_system.ratings_df) if recommendation_system.is_loaded else 0,
        'total_users': recommendation_system.ratings_df['userId'].nunique() if recommendation_system.is_loaded else 0,
        'genres': recommendation_system.get_available_genres() if recommendation_system.is_loaded else []
    })

@app.route('/api/random-movies')
def get_random_movies():
    """Obtener películas aleatorias sin repetir géneros"""
    limit = int(request.args.get('limit', 20))
    movies = recommendation_system.get_random_movies_by_genre(limit)
    return jsonify(movies)

@app.route('/api/search')
def search_movies():
    """Buscar películas"""
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 20))
    results = recommendation_system.search_movies(query, limit)
    return jsonify(results)

@app.route('/api/genre/<genre>')
def get_movies_by_genre(genre):
    """Obtener películas por género"""
    limit = int(request.args.get('limit', 20))
    movies = recommendation_system.get_movies_by_genre(genre, limit)
    return jsonify(movies)

@app.route('/api/recommendations/<movie_id>')
def get_recommendations(movie_id):
    """Obtener recomendaciones para una película"""
    method = request.args.get('method', 'hybrid')  # content, collaborative, tags, hybrid
    limit = int(request.args.get('limit', 10))
    
    recommendations = recommendation_system.get_fast_recommendations(movie_id, method, limit)
    return jsonify(recommendations)

@app.route('/api/genres')
def get_genres():
    """Obtener lista de géneros disponibles"""
    genres = recommendation_system.get_available_genres()
    return jsonify(genres)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
