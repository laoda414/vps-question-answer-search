import React, { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import InvestmentSearchBar from '../components/InvestmentSearchBar'
import InvestmentFilterSidebar from '../components/InvestmentFilterSidebar'
import InvestmentResultsList from '../components/InvestmentResultsList'
import InvestmentStats from '../components/InvestmentStats'
import Pagination from '../components/Pagination'
import api from '../services/api'

function InvestmentAnalysisPage() {
  const { user, logout } = useAuth()
  const [searchQuery, setSearchQuery] = useState('')
  const [filters, setFilters] = useState({
    method: '',
    interest_level: '',
    min_effectiveness: '',
    max_effectiveness: '',
    transition_quality: '',
    technique: ''
  })
  const [results, setResults] = useState([])
  const [pagination, setPagination] = useState({
    page: 1,
    perPage: 20,
    totalResults: 0,
    totalPages: 0
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [availableFilters, setAvailableFilters] = useState({
    methods: [],
    interest_levels: [],
    transition_qualities: [],
    techniques: [],
    effectiveness_range: { min: 0, max: 10 }
  })
  const [stats, setStats] = useState(null)
  const [showFilters, setShowFilters] = useState(false)
  const [showStats, setShowStats] = useState(true)

  // Load available filters and stats on mount
  useEffect(() => {
    loadAvailableFilters()
    loadStats()
  }, [])

  // Perform search when query or filters change
  useEffect(() => {
    performSearch(1)
  }, [searchQuery, filters])

  const loadAvailableFilters = async () => {
    try {
      const response = await api.get('/api/investment-analysis/filters')
      setAvailableFilters(response.data)
    } catch (err) {
      console.error('Failed to load filters:', err)
    }
  }

  const loadStats = async () => {
    try {
      const response = await api.get('/api/investment-analysis/stats')
      setStats(response.data)
    } catch (err) {
      console.error('Failed to load stats:', err)
    }
  }

  const performSearch = async (page = 1) => {
    setLoading(true)
    setError('')

    try {
      const params = {
        q: searchQuery,
        page,
        per_page: pagination.perPage,
        ...filters
      }

      // Remove empty filters
      Object.keys(params).forEach(key => {
        if (!params[key] && params[key] !== 0) delete params[key]
      })

      const response = await api.get('/api/investment-analysis', { params })
      setResults(response.data.results)
      setPagination(response.data.pagination)
    } catch (err) {
      setError(err.response?.data?.error || 'Search failed')
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  const handlePageChange = (newPage) => {
    performSearch(newPage)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900">Investment Analysis</h1>
            <div className="flex items-center gap-4">
              <a
                href="/search"
                className="text-sm text-primary-600 hover:text-primary-800 font-medium"
              >
                QA Search
              </a>
              <span className="text-sm text-gray-600">
                Welcome, <span className="font-medium">{user?.username}</span>
              </span>
              <button
                onClick={logout}
                className="text-sm text-red-600 hover:text-red-800 font-medium"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Dashboard */}
        {showStats && stats && (
          <div className="mb-6">
            <InvestmentStats stats={stats} onClose={() => setShowStats(false)} />
          </div>
        )}

        {/* Search Bar */}
        <div className="mb-6">
          <InvestmentSearchBar
            value={searchQuery}
            onChange={setSearchQuery}
            onToggleFilters={() => setShowFilters(!showFilters)}
            onToggleStats={() => setShowStats(!showStats)}
            showFilters={showFilters}
            showStats={showStats}
          />
        </div>

        {/* Filters and Results */}
        <div className="flex gap-6">
          {/* Sidebar Filters */}
          {showFilters && (
            <div className="w-64 flex-shrink-0">
              <InvestmentFilterSidebar
                filters={filters}
                availableFilters={availableFilters}
                onChange={setFilters}
                onReset={() => setFilters({
                  method: '',
                  interest_level: '',
                  min_effectiveness: '',
                  max_effectiveness: '',
                  transition_quality: '',
                  technique: ''
                })}
              />
            </div>
          )}

          {/* Results */}
          <div className="flex-1">
            {/* Results Header */}
            <div className="bg-white rounded-lg shadow-sm border p-4 mb-4">
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-sm text-gray-600">
                    {loading ? (
                      'Searching...'
                    ) : (
                      <>
                        Found <span className="font-semibold">{pagination.totalResults}</span> investment instances
                        {searchQuery && <span className="text-primary-600 ml-1">for "{searchQuery}"</span>}
                      </>
                    )}
                  </p>
                </div>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
                {error}
              </div>
            )}

            {/* Loading State */}
            {loading && (
              <div className="flex justify-center items-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
              </div>
            )}

            {/* Results List */}
            {!loading && !error && (
              <>
                <InvestmentResultsList results={results} searchQuery={searchQuery} />

                {/* Pagination */}
                {pagination.totalPages > 1 && (
                  <div className="mt-6">
                    <Pagination
                      currentPage={pagination.page}
                      totalPages={pagination.totalPages}
                      onPageChange={handlePageChange}
                    />
                  </div>
                )}

                {/* Empty State */}
                {results.length === 0 && (
                  <div className="bg-white rounded-lg shadow-sm border p-12 text-center">
                    <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                    <h3 className="mt-2 text-lg font-medium text-gray-900">No results found</h3>
                    <p className="mt-1 text-sm text-gray-500">
                      Try adjusting your search query or filters
                    </p>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default InvestmentAnalysisPage
