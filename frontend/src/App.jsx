import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import SearchPage from './pages/SearchPage'
import InvestmentAnalysisPage from './pages/InvestmentAnalysisPage'
import { AuthProvider, useAuth } from './contexts/AuthContext'

function PrivateRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return isAuthenticated ? children : <Navigate to="/login" />
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/search"
            element={
              <PrivateRoute>
                <SearchPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/investment-analysis"
            element={
              <PrivateRoute>
                <InvestmentAnalysisPage />
              </PrivateRoute>
            }
          />
          <Route path="/" element={<Navigate to="/search" />} />
        </Routes>
      </AuthProvider>
    </Router>
  )
}

export default App
