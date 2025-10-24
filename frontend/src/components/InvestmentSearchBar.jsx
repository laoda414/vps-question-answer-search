import React from 'react'

function InvestmentSearchBar({ value, onChange, onToggleFilters, onToggleStats, showFilters, showStats }) {
  return (
    <div className="bg-white rounded-lg shadow-sm border p-4">
      <div className="flex gap-2">
        <div className="flex-1 relative">
          <input
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder="Search investment instances, techniques, responses..."
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
          <svg
            className="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        <button
          onClick={onToggleStats}
          className={`px-4 py-2 rounded-lg font-medium transition ${
            showStats
              ? 'bg-primary-600 text-white hover:bg-primary-700'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          {showStats ? 'Hide Stats' : 'Show Stats'}
        </button>
        <button
          onClick={onToggleFilters}
          className={`px-4 py-2 rounded-lg font-medium transition ${
            showFilters
              ? 'bg-primary-600 text-white hover:bg-primary-700'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          {showFilters ? 'Hide Filters' : 'Show Filters'}
        </button>
      </div>
    </div>
  )
}

export default InvestmentSearchBar
