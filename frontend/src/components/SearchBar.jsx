import React from 'react'

function SearchBar({ value, onChange, onToggleFilters, showFilters }) {
  return (
    <div className="bg-white rounded-lg shadow-sm border p-4">
      <div className="flex gap-3">
        <div className="flex-1">
          <input
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder="Search questions, answers, or context... (supports Portuguese and English)"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none transition"
          />
        </div>
        <button
          onClick={onToggleFilters}
          className={`px-4 py-2 rounded-lg font-medium transition ${
            showFilters
              ? 'bg-primary-600 text-white'
              : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
          }`}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
          </svg>
        </button>
      </div>
      <p className="text-xs text-gray-500 mt-2">
        💡 Tip: Search works in both Portuguese and English. Use filters to narrow down results.
      </p>
    </div>
  )
}

export default SearchBar
