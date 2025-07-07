# 🎬 Sistema de Recomendaciones de Películas Avanzado

Sistema completo de recomendaciones usando múltiples algoritmos de Machine Learning optimizados para velocidad y precisión.

## 🚀 Características

### Algoritmos Implementados:
- **SVD (Singular Value Decomposition)**: Para filtrado colaborativo ultra rápido
- **TF-IDF + Similitud Coseno**: Para recomendaciones basadas en contenido
- **Análisis de Tags**: Incorpora etiquetas de usuarios para mayor precisión
- **Sistema Híbrido**: Combina todos los métodos con pesos optimizados

### Funcionalidades:
- ✅ Carga automática de todos los CSVs (movies, ratings, tags, links)
- ✅ Películas aleatorias sin repetir géneros
- ✅ Búsqueda rápida por título
- ✅ Filtrado por género
- ✅ 4 métodos de recomendación diferentes
- ✅ Interfaz web moderna y responsive
- ✅ Sistema optimizado para velocidad

## 📁 Estructura de Datos Requerida

\`\`\`
data/
├── movies.csv      # movieId, title, genres
├── ratings.csv     # userId, movieId, rating, timestamp
├── tags.csv        # userId, movieId, tag, timestamp
└── links.csv       # movieId, imdbId, tmdbId
\`\`\`

## 🔧 Instalación y Uso

1. **Instalar dependencias:**
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

2. **Colocar CSVs en carpeta data/**

3. **Ejecutar la aplicación:**
   \`\`\`bash
   python app.py
   \`\`\`

4. **Abrir en navegador:**
   \`\`\`
   http://localhost:5000
   \`\`\`

## ⚡ Optimizaciones de Velocidad

- **Matrices precomputadas** para similitud
- **Índices de búsqueda rápida** 
- **SVD con 50 componentes** para reducir dimensionalidad
- **Filtrado de usuarios/películas** con pocos ratings
- **Caching de géneros** para acceso O(1)

## 🎯 Métodos de Recomendación

1. **Híbrido**: Combina todos los métodos (40% contenido + 40% colaborativo + 20% tags)
2. **Contenido**: Similitud por géneros usando TF-IDF
3. **Colaborativo**: Usuarios con gustos similares usando SVD
4. **Tags**: Análisis de etiquetas de usuarios

## 📊 Rendimiento

- Carga inicial: ~30-60 segundos (dependiendo del tamaño de datos)
- Recomendaciones: <1 segundo
- Búsquedas: <0.1 segundos
- Memoria: Optimizada con matrices sparse
# SistemaDeRecomendacion
