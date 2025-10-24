import React, { createContext, useState, useContext, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

const AuthContext = createContext()

export function useAuth() {
  return useContext(AuthContext)
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    // Check if user is already logged in
    const token = sessionStorage.getItem('token')
    const username = sessionStorage.getItem('username')

    if (token && username) {
      // Verify token is still valid
      api.get('/auth/verify')
        .then(() => {
          setUser({ username, token })
          setLoading(false)
        })
        .catch(() => {
          // Token is invalid
          sessionStorage.removeItem('token')
          sessionStorage.removeItem('username')
          setUser(null)
          setLoading(false)
        })
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (username, password) => {
    try {
      const response = await api.post('/auth/login', { username, password })
      const { access_token, username: returnedUsername } = response.data

      sessionStorage.setItem('token', access_token)
      sessionStorage.setItem('username', returnedUsername)

      setUser({ username: returnedUsername, token: access_token })
      navigate('/search')

      return { success: true }
    } catch (error) {
      return {
        success: false,
        error: error.response?.data?.error || 'Login failed'
      }
    }
  }

  const logout = () => {
    sessionStorage.removeItem('token')
    sessionStorage.removeItem('username')
    setUser(null)
    navigate('/login')
  }

  const value = {
    user,
    login,
    logout,
    isAuthenticated: !!user,
    loading
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
