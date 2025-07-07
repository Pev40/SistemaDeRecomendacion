"use client"

import { useState, useEffect } from "react"
import {
  Clock,
  Zap,
  Settings,
  Film,
  Tag,
  Search,
  Coffee,
  Smile,
  Brain,
  CloudLightningIcon as Lightning,
  Bed,
  Eye,
  BookOpen,
  BarChart3,
  Loader2,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Slider } from "@/components/ui/slider"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

// Configuración de la API
const API_BASE_URL = "http://localhost:5000/api"

interface Movie {
  movieId: string
  title: string
  genres: string
  year?: number
  clean_title?: string
  similarity?: number
  similarity_score?: number
  avg_rating?: number
  rating_count?: number
  total_ratings?: number
}

interface SystemStats {
  loaded: boolean
  total_movies: number
  total_ratings: number
  total_users: number
  genres: string[]
}

interface RecommendationResponse {
  movie_id: string
  method: string
  explanation: string
  recommendations: Movie[]
  count: number
}

const similarityAlgorithms = [
  { id: "manhattan", name: "Distancia de Manhattan", color: "bg-red-500" },
  { id: "euclidean", name: "Distancia Euclidiana", color: "bg-blue-500" },
  { id: "pearson", name: "Correlación de Pearson", color: "bg-green-500" },
  { id: "cosine", name: "Similitud del Coseno", color: "bg-purple-500" },
]

const recommendationMethods = [
  { id: "content", name: "Basado en Contenido", color: "bg-blue-500" },
  { id: "collaborative", name: "Colaborativo", color: "bg-green-500" },
  { id: "popular", name: "Popularidad", color: "bg-orange-500" },
  { id: "hybrid", name: "Híbrido", color: "bg-purple-500" },
]

const moods = [
  { id: "cualquiera", name: "Cualquiera", icon: Coffee, color: "bg-purple-500" },
  { id: "alegre", name: "Alegre", icon: Smile, color: "bg-yellow-500" },
  { id: "reflexivo", name: "Reflexivo", icon: Brain, color: "bg-blue-500" },
  { id: "emocionante", name: "Emocionante", icon: Lightning, color: "bg-orange-500" },
  { id: "relajado", name: "Relajado", icon: Bed, color: "bg-green-500" },
  { id: "suspenso", name: "Suspenso", icon: Eye, color: "bg-red-500" },
  { id: "intelectual", name: "Intelectual", icon: BookOpen, color: "bg-indigo-500" },
]

// Mapeo de géneros a moods
const genreToMoodMap: { [key: string]: string[] } = {
  Comedy: ["alegre"],
  Romance: ["alegre", "relajado"],
  Animation: ["alegre", "relajado"],
  Family: ["alegre", "relajado"],
  Musical: ["alegre"],
  Drama: ["reflexivo", "intelectual"],
  War: ["reflexivo", "intelectual"],
  Documentary: ["intelectual", "reflexivo"],
  Biography: ["intelectual", "reflexivo"],
  History: ["intelectual", "reflexivo"],
  Action: ["emocionante"],
  Adventure: ["emocionante", "alegre"],
  "Sci-Fi": ["emocionante", "intelectual"],
  Fantasy: ["emocionante", "alegre"],
  Thriller: ["suspenso", "emocionante"],
  Mystery: ["suspenso", "intelectual"],
  Crime: ["suspenso", "reflexivo"],
  Horror: ["suspenso"],
  Western: ["emocionante", "reflexivo"],
  "Film-Noir": ["reflexivo", "intelectual"],
}

const decades = ["1940s", "1950s", "1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]

const allGenreAlgorithms = [
  ...recommendationMethods,
  ...similarityAlgorithms
];

export default function Component() {
  // System state
  const [systemLoaded, setSystemLoaded] = useState(false)
  const [systemStats, setSystemStats] = useState<SystemStats>({
    loaded: false,
    total_movies: 0,
    total_ratings: 0,
    total_users: 0,
    genres: [],
  })
  const [isInitializing, setIsInitializing] = useState(true)

  // Movie state
  const [randomMovies, setRandomMovies] = useState<Movie[]>([])
  const [selectedMovies, setSelectedMovies] = useState<string[]>([])
  const [selectedGenres, setSelectedGenres] = useState<string[]>([])
  const [selectedMood, setSelectedMood] = useState("cualquiera")

  // UI state
  const [mode, setMode] = useState<"movies" | "genre" | "mood" | null>(null)
  const [selectedAlgorithm, setSelectedAlgorithm] = useState("hybrid")
  const [allRecommendations, setAllRecommendations] = useState<Movie[]>([])
  const [filteredRecommendations, setFilteredRecommendations] = useState<Movie[]>([])
  const [kMeansValue, setKMeansValue] = useState([10])
  const [isCalculating, setIsCalculating] = useState(false)
  const [processingTime, setProcessingTime] = useState("")
  const [showRecommendations, setShowRecommendations] = useState(false)

  // Search and filters
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedGenreFilter, setSelectedGenreFilter] = useState("")
  const [selectedDecade, setSelectedDecade] = useState("")
  const [selectedRating, setSelectedRating] = useState("")

  // User state
  const [userIdInput, setUserIdInput] = useState("");
  const [selectedUserAlgorithm, setSelectedUserAlgorithm] = useState("cosine");
  const [userRecommendations, setUserRecommendations] = useState<Movie[]>([]);
  const [userNValue, setUserNValue] = useState([10]);
  const [isUserCalculating, setIsUserCalculating] = useState(false);
  const [showUserRecommendations, setShowUserRecommendations] = useState(false);
  const [userProcessingTime, setUserProcessingTime] = useState("");

  // Initialize system on component mount
  useEffect(() => {
    initializeSystem()
  }, [])

  const initializeSystem = async () => {
    setIsInitializing(true)
    try {
      // Verificar estado del sistema
      const healthResponse = await fetch(`${API_BASE_URL}/health`)
      const healthData = await healthResponse.json()

      if (!healthData.initialized) {
        // Inicializar sistema si no está inicializado
        const initResponse = await fetch(`${API_BASE_URL}/init`)
        const initData = await initResponse.json()
        console.log("Sistema inicializado:", initData)
      }

      // Obtener estadísticas del sistema
      const statsResponse = await fetch(`${API_BASE_URL}/stats`)
      const statsData = await statsResponse.json()

      // Obtener géneros disponibles
      const genresResponse = await fetch(`${API_BASE_URL}/genres`)
      const genresData = await genresResponse.json()

      setSystemStats({
        loaded: true,
        total_movies: statsData.database?.movies || 0,
        total_ratings: statsData.database?.ratings || 0,
        total_users: statsData.database?.users || 0,
        genres: genresData.map((g: any) => g.genre),
      })
      setSystemLoaded(true)
    } catch (error) {
      console.error("Error inicializando sistema:", error)
    } finally {
      setIsInitializing(false)
    }
  }

  const loadRandomMovies = async (limit = 10) => {
    try {
      // Obtener películas aleatorias desde la API
      const response = await fetch(`${API_BASE_URL}/search?limit=${limit}`)
      const movies = await response.json()

      setRandomMovies(movies)
      setSelectedMovies([])
      setAllRecommendations([])
      setFilteredRecommendations([])
      setShowRecommendations(false)
    } catch (error) {
      console.error("Error cargando películas aleatorias:", error)
    }
  }

  const getMoviesByMood = async () => {
    if (selectedMood === "cualquiera") {
      await loadRandomMovies(10)
      return
    }

    // Filtrar géneros que coincidan con el mood seleccionado
    const moodGenres = Object.entries(genreToMoodMap)
      .filter(([genre, moods]) => moods.includes(selectedMood))
      .map(([genre]) => genre)

    if (moodGenres.length === 0) {
      await loadRandomMovies(10)
      return
    }

    // Obtener películas por género del mood
    try {
      const genre = moodGenres[0] // Usar el primer género del mood
      const response = await fetch(`${API_BASE_URL}/genres/${encodeURIComponent(genre)}?limit=10`)
      const movies = await response.json()

      setRandomMovies(movies)
      setSelectedMovies([])
      setAllRecommendations([])
      setFilteredRecommendations([])
      setShowRecommendations(false)
    } catch (error) {
      console.error("Error obteniendo películas por mood:", error)
      await loadRandomMovies(10)
    }
  }

  const [selectedMovieDetails, setSelectedMovieDetails] = useState<any>(null)
  const [showMovieDetails, setShowMovieDetails] = useState(false)

  const toggleMovieSelection = (movieId: string) => {
    setSelectedMovies((prev) => (prev.includes(movieId) ? prev.filter((id) => id !== movieId) : [...prev, movieId]))
  }

  const showMovieInfo = async (movieId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/movies/${movieId}`)
      if (response.ok) {
        const movieDetails = await response.json()
        setSelectedMovieDetails(movieDetails)
        setShowMovieDetails(true)
      }
    } catch (error) {
      console.error("Error obteniendo detalles de la película:", error)
    }
  }

  const toggleGenreSelection = (genre: string) => {
    setSelectedGenres((prev) => (prev.includes(genre) ? prev.filter((g) => g !== genre) : [...prev, genre]))
  }

  const calculateRecommendations = async () => {
    setIsCalculating(true)
    setAllRecommendations([])
    setFilteredRecommendations([])

    const startTime = performance.now()

    try {
      let recommendedMovies: Movie[] = []

      if ((mode === "movies" || mode === "mood") && selectedMovies.length > 0) {
        // Obtener recomendaciones para la película seleccionada
        const movieId = selectedMovies[0]
        const response = await fetch(
          `${API_BASE_URL}/recommendations/${movieId}?method=${selectedAlgorithm}&limit=20`
        )
        const data: RecommendationResponse = await response.json()
        recommendedMovies = data.recommendations
        
        // Mostrar información del método usado
        console.log(`Método usado: ${data.method}`)
        console.log(`Explicación: ${data.explanation}`)
      } else if (mode === "genre" && selectedGenres.length > 0) {
        // Obtener recomendaciones basadas en múltiples géneros seleccionados
        const genresParam = selectedGenres.join(',')
        const response = await fetch(
          `${API_BASE_URL}/genre-recommendations?genres=${encodeURIComponent(genresParam)}&method=${selectedAlgorithm}&limit=20`
        )
        const data = await response.json()
        recommendedMovies = data.recommendations
        
        // Mostrar información del método usado
        console.log(`Método usado: ${data.method}`)
        console.log(`Explicación: ${data.explanation}`)
        console.log(`Géneros seleccionados: ${data.genres}`)
      }

      const endTime = performance.now()
      const calculatedTime = ((endTime - startTime) / 1000).toFixed(3)

      setAllRecommendations(recommendedMovies)
      setFilteredRecommendations(recommendedMovies.slice(0, kMeansValue[0]))
      setProcessingTime(`${calculatedTime}s`)
      setShowRecommendations(true)
    } catch (error) {
      console.error("Error calculando recomendaciones:", error)
    } finally {
      setIsCalculating(false)
    }
  }

  const handleKMeansChange = (value: number[]) => {
    setKMeansValue(value)
    if (allRecommendations.length > 0) {
      setFilteredRecommendations(allRecommendations.slice(0, value[0]))
    }
  }

  const resetSelection = () => {
    setMode(null)
    setSelectedMovies([])
    setSelectedGenres([])
    setSelectedMood("cualquiera")
    setAllRecommendations([])
    setFilteredRecommendations([])
    setRandomMovies([])
    setProcessingTime("")
    setShowRecommendations(false)
    setKMeansValue([10])
    setSearchQuery("")
    setSelectedGenreFilter("")
    setSelectedDecade("")
    setSelectedRating("")
  }

  const getGenreColor = (genre: string) => {
    const colors: { [key: string]: string } = {
      Action: "bg-red-100 text-red-700",
      Comedy: "bg-yellow-100 text-yellow-700",
      Horror: "bg-purple-100 text-purple-700",
      Romance: "bg-pink-100 text-pink-700",
      "Sci-Fi": "bg-blue-100 text-blue-700",
      Fantasy: "bg-indigo-100 text-indigo-700",
      Thriller: "bg-orange-100 text-orange-700",
      Drama: "bg-gray-100 text-gray-700",
      Animation: "bg-green-100 text-green-700",
      Adventure: "bg-teal-100 text-teal-700",
      Crime: "bg-slate-100 text-slate-700",
      Mystery: "bg-violet-100 text-violet-700",
      War: "bg-red-200 text-red-800",
      Western: "bg-amber-100 text-amber-700",
      Musical: "bg-cyan-100 text-cyan-700",
      Documentary: "bg-emerald-100 text-emerald-700",
      Children: "bg-pink-100 text-pink-700",
      "Film-Noir": "bg-gray-200 text-gray-800",
    }
    return colors[genre] || "bg-gray-100 text-gray-600"
  }

  // Función para obtener recomendaciones de usuario
  const getUserRecommendations = async () => {
    if (!userIdInput) return;
    setIsUserCalculating(true);
    setUserRecommendations([]);
    setShowUserRecommendations(false);
    setUserProcessingTime("");
    
    const startTime = performance.now();
    
    try {
      const response = await fetch(
        `${API_BASE_URL}/user-recommendations/${userIdInput}?method=${selectedUserAlgorithm}&limit=${userNValue[0]}`
      );
      const data = await response.json();
      setUserRecommendations(data.recommendations || []);
      setShowUserRecommendations(true);
      
      const endTime = performance.now();
      const calculatedTime = ((endTime - startTime) / 1000).toFixed(3);
      setUserProcessingTime(`${calculatedTime}s`);
    } catch (error) {
      setUserRecommendations([]);
      setShowUserRecommendations(false);
      setUserProcessingTime("");
    } finally {
      setIsUserCalculating(false);
    }
  };

  if (isInitializing) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50 flex items-center justify-center">
        <Card className="p-8 text-center">
          <CardContent>
            <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4 text-purple-600" />
            <h2 className="text-2xl font-bold mb-2">Inicializando Sistema</h2>
            <p className="text-gray-600">Conectando con el servidor de recomendaciones...</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header estilo MovieLens con estadísticas REALES */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="bg-purple-600 p-3 rounded-lg">
                <Film className="w-8 h-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">MovieLens Recommender</h1>
                <p className="text-gray-600">Sistema de Recomendación con Métricas Básicas</p>
              </div>
            </div>

            {/* Estadísticas REALES del dataset */}
            <div className="flex items-center gap-8">
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">{systemStats.total_movies.toLocaleString()}</div>
                <div className="text-sm text-gray-600">Películas</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{systemStats.total_ratings.toLocaleString()}</div>
                <div className="text-sm text-gray-600">Calificaciones</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{systemStats.total_users.toLocaleString()}</div>
                <div className="text-sm text-gray-600">Usuarios</div>
              </div>
              <Button variant="outline" className="flex items-center gap-2 bg-transparent">
                <Settings className="w-4 h-4" />
                Preferencias
              </Button>
            </div>
          </div>
        </div>

        {/* Mode Selection - SIN películas por defecto */}
        {!mode && randomMovies.length === 0 && (
          <div className="text-center py-20">
            <div className="text-8xl mb-6">🎬</div>
            <h3 className="text-3xl font-bold text-gray-700 mb-4">¡Bienvenido al Sistema de Recomendaciones!</h3>
            <p className="text-gray-500 mb-8 text-lg max-w-2xl mx-auto">
              Selecciona una opción para comenzar a descubrir películas increíbles personalizadas para ti
            </p>
          </div>
        )}

        {/* Mode Selection */}
        {!mode && (
          <div className="space-y-8">
            {/* Mood Selection */}
            <Card className="shadow-xl">
              <CardContent className="p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">¿Cómo te sientes hoy?</h2>
                <p className="text-gray-600 mb-6">
                  Selecciona tu estado de ánimo para obtener recomendaciones personalizadas
                </p>

                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4 mb-6">
                  {moods.map((mood) => {
                    const IconComponent = mood.icon
                    return (
                      <Button
                        key={mood.id}
                        onClick={() => setSelectedMood(mood.id)}
                        variant={selectedMood === mood.id ? "default" : "outline"}
                        className={`h-20 flex flex-col gap-2 ${
                          selectedMood === mood.id ? `${mood.color} text-white` : ""
                        }`}
                      >
                        <IconComponent className="w-6 h-6" />
                        <span className="text-sm">{mood.name}</span>
                      </Button>
                    )
                  })}
                </div>

                <Button
                  onClick={() => {
                    setMode("mood")
                    getMoviesByMood()
                  }}
                  className="w-full bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white py-4 text-lg font-bold"
                >
                  Obtener Recomendaciones por Estado de Ánimo
                </Button>
              </CardContent>
            </Card>

            {/* Advanced Search */}
            <Card className="shadow-xl">
              <CardContent className="p-8">
                <h3 className="text-xl font-bold text-gray-900 mb-6">Búsqueda Avanzada</h3>

                <div className="grid md:grid-cols-4 gap-4 mb-6">
                  <div className="relative">
                    <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
                    <Input
                      placeholder="Buscar películas..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10"
                    />
                  </div>

                  <Select value={selectedGenreFilter} onValueChange={setSelectedGenreFilter}>
                    <SelectTrigger>
                      <SelectValue placeholder="Todos los géneros" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Todos los géneros</SelectItem>
                      {systemStats.genres.map((genre) => (
                        <SelectItem key={genre} value={genre}>
                          {genre}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  <Select value={selectedDecade} onValueChange={setSelectedDecade}>
                    <SelectTrigger>
                      <SelectValue placeholder="Todas las décadas" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Todas las décadas</SelectItem>
                      {decades.map((decade) => (
                        <SelectItem key={decade} value={decade}>
                          {decade}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  <Select value={selectedRating} onValueChange={setSelectedRating}>
                    <SelectTrigger>
                      <SelectValue placeholder="Calificación" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Todas</SelectItem>
                      <SelectItem value="9+">9.0+ ⭐⭐⭐⭐⭐</SelectItem>
                      <SelectItem value="8+">8.0+ ⭐⭐⭐⭐</SelectItem>
                      <SelectItem value="7+">7.0+ ⭐⭐⭐</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>

            {/* Original Mode Selection - AQUÍ es donde se cargan las películas */}
            <div className="flex justify-center gap-8">
              <Button
                onClick={() => {
                  setMode("movies")
                  loadRandomMovies(10) // SOLO aquí se cargan las películas
                }}
                size="lg"
                className="bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600 text-white px-12 py-6 text-xl font-bold rounded-xl shadow-lg transform hover:scale-105 transition-all duration-300"
              >
                <Film className="w-8 h-8 mr-3" />
                PELÍCULAS ALEATORIAS
              </Button>
              <Button
                onClick={() => setMode("genre")}
                size="lg"
                className="bg-gradient-to-r from-green-500 to-teal-500 hover:from-green-600 hover:to-teal-600 text-white px-12 py-6 text-xl font-bold rounded-xl shadow-lg transform hover:scale-105 transition-all duration-300"
              >
                <Tag className="w-8 h-8 mr-3" />
                POR GÉNERO
              </Button>
            </div>
          </div>
        )}

        {/* User Recommendations Section */}
        {!mode && (
          <Card className="shadow-xl mt-8">
            <CardContent className="p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">👤 Recomendaciones por Usuario</h2>
              <div className="grid md:grid-cols-4 gap-4 mb-6">
                <div>
                  <label className="block text-sm font-medium mb-1">ID de Usuario</label>
                  <Input
                    placeholder="Ej: 1"
                    value={userIdInput}
                    onChange={e => setUserIdInput(e.target.value)}
                    type="number"
                    min={1}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Algoritmo</label>
                  <Select value={selectedUserAlgorithm} onValueChange={setSelectedUserAlgorithm}>
                    <SelectTrigger>
                      <SelectValue placeholder="Algoritmo" />
                    </SelectTrigger>
                    <SelectContent>
                      {similarityAlgorithms.map((alg) => (
                        <SelectItem key={alg.id} value={alg.id}>{alg.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">N° de recomendaciones</label>
                  <Slider
                    value={userNValue}
                    onValueChange={setUserNValue}
                    max={20}
                    min={1}
                    step={1}
                    className="mt-2"
                  />
                  <div className="text-xs text-gray-600 mt-1">N = {userNValue[0]}</div>
                </div>
                <div className="flex items-end">
                  <Button
                    onClick={getUserRecommendations}
                    disabled={isUserCalculating || !userIdInput}
                    className="w-full bg-gradient-to-r from-pink-500 to-purple-500 text-white font-bold"
                  >
                    {isUserCalculating ? (
                      <>
                        <Settings className="w-5 h-5 mr-2 animate-spin" />
                        Calculando...
                      </>
                    ) : (
                      <>
                        <Zap className="w-5 h-5 mr-2" />
                        Obtener Recomendaciones
                      </>
                    )}
                  </Button>
                </div>
              </div>
              {showUserRecommendations && (
                <div className="mt-6">
                  <h3 className="text-lg font-bold mb-4">Películas recomendadas para el usuario {userIdInput}</h3>
                  {userRecommendations.length === 0 ? (
                    <div className="text-gray-500">No se encontraron recomendaciones para este usuario.</div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                        {userRecommendations.map((movie, index) => (
                    <Card key={`${movie.movieId}-${index}`} className="hover:shadow-lg transition-shadow duration-300">
                          <CardContent className="p-6">
                            <div className="flex items-center justify-between mb-3">
                              <Badge variant="default" className="bg-pink-500">
                                #{index + 1}
                              </Badge>
                              <Badge variant="secondary">ID: {movie.movieId}</Badge>
                            </div>
                            <h3 className="font-bold text-xl mb-2">{movie.clean_title || movie.title}</h3>
                            <p className="text-gray-600 mb-3">({movie.year || "N/A"})</p>
                            <div className="flex flex-wrap gap-1 mb-3">
                              {movie.genres.split("|").map((genre) => (
                                <Badge key={genre} variant="outline" className={`text-xs ${getGenreColor(genre)}`}>
                                  {genre}
                                </Badge>
                              ))}
                            </div>
                            {movie.avg_rating && (
                              <div className="p-2 bg-green-50 rounded mt-2">
                                <p className="text-sm text-green-700">
                                  ⭐ Rating: {movie.avg_rating.toFixed(1)} ({movie.total_ratings || movie.rating_count} calificaciones)
                                </p>
                              </div>
                            )}
                            {movie.similarity && (
                              <div className="p-2 bg-purple-50 rounded mt-2">
                                <p className="text-sm text-purple-700">
                                  📊 Similitud: {(movie.similarity * 100).toFixed(1)}%
                                </p>
                              </div>
                            )}
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Movies Mode */}
        {(mode === "movies" || mode === "mood") && (
          <div className="space-y-8">
            <Card className="shadow-xl">
              <CardContent className="p-8">
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-bold text-gray-900">
                    {mode === "mood"
                      ? `🎭 Películas para estado: ${moods.find((m) => m.id === selectedMood)?.name} (${selectedMovies.length}/${randomMovies.length})`
                      : `🎲 Selecciona tus películas favoritas (${selectedMovies.length}/${randomMovies.length})`}
                  </h2>
                  <div className="flex gap-2">
                    <Button onClick={() => loadRandomMovies(10)} variant="outline">
                      <Zap className="w-4 h-4 mr-2" />
                      10 películas
                    </Button>
                    <Button onClick={() => loadRandomMovies(20)} variant="outline">
                      <Zap className="w-4 h-4 mr-2" />
                      20 películas
                    </Button>
                    <Button onClick={() => loadRandomMovies(50)} variant="outline">
                      <Zap className="w-4 h-4 mr-2" />
                      50 películas
                    </Button>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                  {randomMovies.map((movie) => (
                    <Card
                      key={movie.movieId}
                      className={`cursor-pointer transition-all duration-300 hover:scale-105 ${
                        selectedMovies.includes(movie.movieId) ? "ring-2 ring-blue-500 bg-blue-50" : "hover:shadow-lg"
                      }`}
                      onClick={() => toggleMovieSelection(movie.movieId)}
                    >
                      <CardContent className="p-4 text-center">
                        <h3 className="font-bold text-lg mb-2">{movie.clean_title || movie.title}</h3>
                        <p className="text-gray-600 mb-2">({movie.year || "N/A"})</p>
                        <Badge variant="secondary" className="mb-2">
                          ID: {movie.movieId}
                        </Badge>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={() => showMovieInfo(movie.movieId)}
                          className="mt-2"
                        >
                          📊 Ver Detalles
                        </Button>
                        <div className="flex flex-wrap gap-1 justify-center">
                          {movie.genres
                            .split("|")
                            .slice(0, 3)
                            .map((genre) => (
                              <Badge key={genre} variant="outline" className={`text-xs ${getGenreColor(genre)}`}>
                                {genre}
                              </Badge>
                            ))}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>

            {selectedMovies.length > 0 && (
              <Card className="shadow-xl">
                <CardContent className="p-8">
                  <h3 className="text-xl font-bold mb-6">🧠 Selecciona el Algoritmo</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                    {similarityAlgorithms.map((algorithm) => (
                      <Card
                        key={algorithm.id}
                        className={`cursor-pointer transition-all duration-300 hover:scale-105 ${
                          selectedAlgorithm === algorithm.id ? "ring-2 ring-purple-500 bg-purple-50" : ""
                        }`}
                        onClick={() => setSelectedAlgorithm(algorithm.id)}
                      >
                        <CardContent className="p-4 text-center">
                          <div className={`w-4 h-4 ${algorithm.color} rounded-full mx-auto mb-2`}></div>
                          <h4 className="font-semibold text-sm">{algorithm.name}</h4>
                        </CardContent>
                      </Card>
                    ))}
                  </div>

                  <Button
                    onClick={calculateRecommendations}
                    disabled={isCalculating}
                    className="w-full bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white py-4 text-lg font-bold"
                  >
                    {isCalculating ? (
                      <>
                        <Settings className="w-5 h-5 mr-2 animate-spin" />
                        Calculando recomendaciones...
                      </>
                    ) : (
                      <>
                        <Zap className="w-5 h-5 mr-2" />
                        {showRecommendations ? "Recalcular Recomendaciones" : "Generar Recomendaciones"}
                      </>
                    )}
                  </Button>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Genre Mode - TODOS LOS GÉNEROS DEL DATASET */}
        {mode === "genre" && (
          <div className="space-y-8">
            <Card className="shadow-xl">
              <CardContent className="p-8">
                <h2 className="text-2xl font-bold text-gray-900 mb-6">
                  🏷️ Selecciona tus géneros favoritos ({selectedGenres.length}/{systemStats.genres.length})
                </h2>

                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 mb-8">
                  {systemStats.genres.map((genre) => (
                    <Button
                      key={genre}
                      onClick={() => toggleGenreSelection(genre)}
                      variant={selectedGenres.includes(genre) ? "default" : "outline"}
                      className={`${
                        selectedGenres.includes(genre) ? "bg-gradient-to-r from-green-500 to-teal-500 text-white" : ""
                      }`}
                    >
                      {genre}
                    </Button>
                  ))}
                </div>

                {selectedGenres.length > 0 && (
                  <>
                    <h3 className="text-xl font-bold mb-4">🧠 Selecciona el Algoritmo</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                      {allGenreAlgorithms.map((algorithm) => (
                        <Card
                          key={algorithm.id}
                          className={`cursor-pointer transition-all duration-300 hover:scale-105 ${
                            selectedAlgorithm === algorithm.id ? "ring-2 ring-purple-500 bg-purple-50" : ""
                          }`}
                          onClick={() => setSelectedAlgorithm(algorithm.id)}
                        >
                          <CardContent className="p-4 text-center">
                            <div className={`w-4 h-4 ${algorithm.color} rounded-full mx-auto mb-2`}></div>
                            <h4 className="font-semibold text-sm">{algorithm.name}</h4>
                          </CardContent>
                        </Card>
                      ))}
                    </div>

                    <Button
                      onClick={calculateRecommendations}
                      disabled={isCalculating}
                      className="w-full bg-gradient-to-r from-green-500 to-teal-500 hover:from-green-600 hover:to-teal-600 text-white py-4 text-lg font-bold"
                    >
                      {isCalculating ? (
                        <>
                          <Settings className="w-5 h-5 mr-2 animate-spin" />
                          Calculando recomendaciones...
                        </>
                      ) : (
                        <>
                          <Zap className="w-5 h-5 mr-2" />
                          {showRecommendations ? "Recalcular Recomendaciones" : "Generar Recomendaciones"}
                        </>
                      )}
                    </Button>
                  </>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Processing Time Display */}
        {processingTime && showRecommendations && (
          <Card className="shadow-xl bg-gradient-to-r from-yellow-50 to-orange-50 border-yellow-200">
            <CardContent className="p-6 text-center">
              <h3 className="text-lg font-bold text-orange-800 mb-2">⚡ Tiempo de Procesamiento Real</h3>
              <Badge variant="secondary" className="text-lg px-4 py-2 bg-orange-100 text-orange-800">
                <Clock className="w-4 h-4 mr-2" />
                {processingTime}
              </Badge>
              <p className="text-sm text-orange-600 mt-2">
                Algoritmo: {mode === "genre" 
                  ? recommendationMethods.find((a) => a.id === selectedAlgorithm)?.name
                  : similarityAlgorithms.find((a) => a.id === selectedAlgorithm)?.name}
              </p>
            </CardContent>
          </Card>
        )}

        {/* Recommendations Display with K-means */}
        {showRecommendations && allRecommendations.length > 0 && (
          <div className="space-y-8">
            {/* K-means Control */}
            <Card className="shadow-xl bg-gradient-to-r from-indigo-50 to-purple-50 border-indigo-200">
              <CardContent className="p-8">
                <h3 className="text-2xl font-bold text-indigo-800 mb-6 text-center">📊 K-means Clustering</h3>
                <div className="bg-white rounded-lg p-6">
                  <div className="flex items-center gap-4 mb-4">
                    <span className="text-sm font-medium">1</span>
                    <Slider
                      value={kMeansValue}
                      onValueChange={handleKMeansChange}
                      max={Math.min(allRecommendations.length, 20)}
                      min={1}
                      step={1}
                      className="flex-1"
                    />
                    <span className="text-sm font-medium">{Math.min(allRecommendations.length, 20)}</span>
                  </div>
                  <div className="text-center">
                    <Badge variant="default" className="text-xl px-6 py-3 bg-indigo-500">
                      K = {kMeansValue[0]} clusters
                    </Badge>
                    <p className="text-sm text-gray-600 mt-2">
                      Mostrando {filteredRecommendations.length} de {allRecommendations.length} recomendaciones
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Filtered Recommendations */}
            <Card className="shadow-xl">
              <CardContent className="p-8">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900">
                      ✨ Recomendaciones ({filteredRecommendations.length})
                    </h2>
                    {mode === "genre" && selectedGenres.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        <span className="text-sm text-gray-600">Géneros seleccionados:</span>
                        {selectedGenres.map((genre) => (
                          <Badge key={genre} variant="outline" className={`text-xs ${getGenreColor(genre)}`}>
                            {genre}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <Badge variant="secondary" className="flex items-center gap-1">
                      <BarChart3 className="w-3 h-3" />
                      {mode === "mood"
                        ? `Estado: ${moods.find((m) => m.id === selectedMood)?.name}`
                        : mode === "movies"
                          ? "Basado en películas"
                          : "Basado en géneros"}
                    </Badge>
                    <Button onClick={resetSelection} variant="outline">
                      🔄 Reiniciar
                    </Button>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {filteredRecommendations.map((movie, index) => (
                    <Card key={`${movie.movieId}-${index}`} className="hover:shadow-lg transition-shadow duration-300">
                      <CardContent className="p-6">
                        <div className="flex items-center justify-between mb-3">
                          <Badge variant="default" className="bg-purple-500">
                            #{index + 1}
                          </Badge>
                          <Badge variant="secondary">ID: {movie.movieId}</Badge>
                        </div>

                        <h3 className="font-bold text-xl mb-2">{movie.clean_title || movie.title}</h3>
                        <p className="text-gray-600 mb-3">({movie.year || "N/A"})</p>

                        <div className="flex flex-wrap gap-1 mb-3">
                          {movie.genres.split("|").map((genre) => (
                            <Badge key={genre} variant="outline" className={`text-xs ${getGenreColor(genre)}`}>
                              {genre}
                            </Badge>
                          ))}
                        </div>

                        {/* Mostrar información de rating y similitud si está disponible */}
                        {(movie.avg_rating || movie.similarity_score) && (
                          <div className="mt-3 space-y-2">
                            {movie.avg_rating && (
                              <div className="p-2 bg-green-50 rounded">
                                <p className="text-sm text-green-700">
                                  ⭐ Rating: {movie.avg_rating.toFixed(1)} ({movie.total_ratings || movie.rating_count} calificaciones)
                                </p>
                              </div>
                            )}
                            {movie.similarity_score && (
                              <div className="p-2 bg-blue-50 rounded">
                                <p className="text-sm text-blue-700">
                                  🎯 Similitud: {(movie.similarity_score * 100).toFixed(1)}%
                                </p>
                              </div>
                            )}
                            {movie.similarity && (
                              <div className="p-2 bg-purple-50 rounded">
                                <p className="text-sm text-purple-700">
                                  📊 Similitud: {(movie.similarity * 100).toFixed(1)}%
                                </p>
                              </div>
                            )}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Back Button */}
        {mode && (
          <div className="text-center">
            <Button onClick={resetSelection} size="lg" variant="outline" className="px-8 py-3 bg-transparent">
              ← Volver al inicio
            </Button>
          </div>
        )}

        {/* Modal de Detalles de Película */}
        {showMovieDetails && selectedMovieDetails && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <Card className="max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
              <CardContent className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <h2 className="text-2xl font-bold">{selectedMovieDetails.title}</h2>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => setShowMovieDetails(false)}
                  >
                    ✕
                  </Button>
                </div>

                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="text-lg font-semibold mb-3">📊 Estadísticas</h3>
                    {selectedMovieDetails.stats && (
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span>Calificación Promedio:</span>
                          <Badge variant="default">
                            {selectedMovieDetails.stats.avg_rating?.toFixed(2) || 'N/A'} ⭐
                          </Badge>
                        </div>
                        <div className="flex justify-between">
                          <span>Total de Calificaciones:</span>
                          <Badge variant="secondary">
                            {selectedMovieDetails.stats.total_ratings?.toLocaleString() || 'N/A'}
                          </Badge>
                        </div>
                        <div className="flex justify-between">
                          <span>Usuarios que Calificaron:</span>
                          <Badge variant="outline">
                            {selectedMovieDetails.users_who_rated?.toLocaleString() || 'N/A'}
                          </Badge>
                        </div>
                      </div>
                    )}
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold mb-3">🏷️ Información</h3>
                    <div className="space-y-2">
                      <div><strong>Año:</strong> {selectedMovieDetails.year || 'N/A'}</div>
                      <div><strong>ID:</strong> {selectedMovieDetails.movieId}</div>
                      <div className="flex flex-wrap gap-1">
                        <strong>Géneros:</strong>
                        {selectedMovieDetails.genres?.split('|').map((genre: string) => (
                          <Badge key={genre} variant="outline" className={`text-xs ${getGenreColor(genre)}`}>
                            {genre}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {selectedMovieDetails.similar_movies && selectedMovieDetails.similar_movies.length > 0 && (
                  <div className="mt-6">
                    <h3 className="text-lg font-semibold mb-3">🎯 Películas Similares</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {selectedMovieDetails.similar_movies.slice(0, 4).map((movie: any, index: number) => (
                        <Card key={movie.movieId} className="p-3">
                          <div className="flex justify-between items-start">
                            <div>
                              <h4 className="font-semibold text-sm">{movie.title}</h4>
                              <p className="text-xs text-gray-600">({movie.year})</p>
                              {movie.similarity && (
                                <p className="text-xs text-blue-600">
                                  Similitud: {(movie.similarity * 100).toFixed(1)}%
                                </p>
                              )}
                            </div>
                            <Badge variant="outline" className="text-xs">
                              #{index + 1}
                            </Badge>
                          </div>
                        </Card>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}
