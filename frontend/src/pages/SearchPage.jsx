import React, { useState, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'
import SearchBar from '../components/SearchBar'
import FilterSidebar from '../components/FilterSidebar'
import ResultsList from '../components/ResultsList'
import Pagination from '../components/Pagination'
import api from '../services/api'

function SearchPage() {
  const { user, logout } = useAuth()
  const [searchQuery, setSearchQuery] = useState('')
  const [filters, setFilters] = useState({
    dateFrom: '',
    dateTo: '',
    emotion: '',
    conversationId: ''
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
    emotions: [],
    dateRange: { min_date: null, max_date: null },
    conversations: []
  })
  const [showFilters, setShowFilters] = useState(false)

  // Load available filters on mount
  useEffect(() => {
    loadAvailableFilters()
  }, [])

  // Perform search when query or filters change
  useEffect(() => {
    performSearch(1)
  }, [searchQuery, filters])

  const loadAvailableFilters = async () => {
    try {
      const response = await api.get('/api/filters')
      setAvailableFilters(response.data)
    } catch (err) {
      console.error('Failed to load filters:', err)
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
        if (!params[key]) delete params[key]
      })

      const response = await api.get('/api/search', { params })
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

  const handleExport = async (format = 'csv') => {
    try {
      const params = {
        q: searchQuery,
        format,
        ...filters
      }

      Object.keys(params).forEach(key => {
        if (!params[key]) delete params[key]
      })

      const response = await api.get('/api/export', {
        params,
        responseType: 'blob'
      })

      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `qa_export_${Date.now()}.${format}`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (err) {
      alert('Export failed: ' + (err.response?.data?.error || err.message))
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-gray-900">QA Search</h1>
            <div className="flex items-center gap-4">
              <a
                href="/investment-analysis"
                className="text-sm text-primary-600 hover:text-primary-800 font-medium"
              >
                Investment Analysis
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
        {/* Search Bar */}
        <div className="mb-6">
          <SearchBar
            value={searchQuery}
            onChange={setSearchQuery}
            onToggleFilters={() => setShowFilters(!showFilters)}
            showFilters={showFilters}
          />
        </div>

        {/* Filters and Results */}
        <div className="flex gap-6">
          {/* Sidebar Filters */}
          {showFilters && (
            <div className="w-64 flex-shrink-0">
              <FilterSidebar
                filters={filters}
                availableFilters={availableFilters}
                onChange={setFilters}
                onReset={() => setFilters({
                  dateFrom: '',
                  dateTo: '',
                  emotion: '',
                  conversationId: ''
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
                        Found <span className="font-semibold">{pagination.totalResults}</span> results
                        {searchQuery && <span className="text-primary-600 ml-1">for "{searchQuery}"</span>}
                      </>
                    )}
                  </p>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleExport('csv')}
                    disabled={results.length === 0}
                    className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded disabled:opacity-50 disabled:cursor-not-allowed transition"
                  >
                    Export CSV
                  </button>
                  <button
                    onClick={() => handleExport('json')}
                    disabled={results.length === 0}
                    className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 rounded disabled:opacity-50 disabled:cursor-not-allowed transition"
                  >
                    Export JSON
                  </button>
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
                <ResultsList results={results} searchQuery={searchQuery} />

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

export default SearchPage
