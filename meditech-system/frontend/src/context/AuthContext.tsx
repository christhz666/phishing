import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import axios from 'axios'

interface User {
  id: string
  username: string
  email: string
  primer_nombre: string
  apellidos: string
  rol_id: string
  branch_id: string | null
  activo: boolean
}

interface AuthContextType {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const API_URL = import.meta.env.VITE_API_URL || '/api/v1'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(localStorage.getItem('access_token'))
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('access_token')
      if (storedToken) {
        try {
          const response = await axios.get(`${API_URL}/auth/me`, {
            headers: { Authorization: `Bearer ${storedToken}` }
          })
          setUser(response.data)
          setToken(storedToken)
          axios.defaults.headers.common['Authorization'] = `Bearer ${storedToken}`
        } catch (error) {
          // Token inválido o expirado
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          setToken(null)
          setUser(null)
        }
      }
      setIsLoading(false)
    }

    initAuth()
  }, [])

  const login = async (username: string, password: string) => {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)

    const response = await axios.post(`${API_URL}/auth/login`, formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })

    const { access_token, refresh_token } = response.data

    localStorage.setItem('access_token', access_token)
    localStorage.setItem('refresh_token', refresh_token)
    setToken(access_token)
    axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`

    // Obtener información del usuario
    const userResponse = await axios.get(`${API_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${access_token}` }
    })
    setUser(userResponse.data)
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setToken(null)
    setUser(null)
    delete axios.defaults.headers.common['Authorization']
  }

  const refreshToken = async () => {
    const refresh_token = localStorage.getItem('refresh_token')
    if (!refresh_token) {
      logout()
      return
    }

    try {
      const response = await axios.post(`${API_URL}/auth/refresh`, { refresh_token })
      const { access_token, refresh_token: newRefreshToken } = response.data

      localStorage.setItem('access_token', access_token)
      localStorage.setItem('refresh_token', newRefreshToken)
      setToken(access_token)
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`

      const userResponse = await axios.get(`${API_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${access_token}` }
      })
      setUser(userResponse.data)
    } catch (error) {
      logout()
    }
  }

  return (
    <AuthContext.Provider value={{
      user,
      token,
      isAuthenticated: !!token && !!user,
      isLoading,
      login,
      logout,
      refreshToken
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// Axios interceptor para refresh automático de tokens
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const refresh_token = localStorage.getItem('refresh_token')
      if (refresh_token) {
        try {
          const response = await axios.post(`${API_URL}/auth/refresh`, { refresh_token })
          const { access_token, refresh_token: newRefreshToken } = response.data

          localStorage.setItem('access_token', access_token)
          localStorage.setItem('refresh_token', newRefreshToken)
          axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
          originalRequest.headers.Authorization = `Bearer ${access_token}`

          return axios(originalRequest)
        } catch (refreshError) {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
          return Promise.reject(refreshError)
        }
      }
    }

    return Promise.reject(error)
  }
)
