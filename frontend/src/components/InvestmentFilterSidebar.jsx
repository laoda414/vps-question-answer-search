import React from 'react'

function InvestmentFilterSidebar({ filters, availableFilters, onChange, onReset }) {
  const handleChange = (key, value) => {
    onChange({ ...filters, [key]: value })
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border p-4 sticky top-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Filters</h3>
        <button
          onClick={onReset}
          className="text-sm text-primary-600 hover:text-primary-800 font-medium"
        >
          Reset
        </button>
      </div>

      <div className="space-y-4">
        {/* Method Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Method
          </label>
          <select
            value={filters.method}
            onChange={(e) => handleChange('method', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500 text-sm"
          >
            <option value="">All Methods</option>
            {availableFilters.methods.map(method => (
              <option key={method} value={method}>
                {method.charAt(0).toUpperCase() + method.slice(1)}
              </option>
            ))}
          </select>
        </div>

        {/* Interest Level Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Interest Level
          </label>
          <select
            value={filters.interest_level}
            onChange={(e) => handleChange('interest_level', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500 text-sm"
          >
            <option value="">All Levels</option>
            {availableFilters.interest_levels.map(level => (
              <option key={level} value={level}>
                {level.charAt(0).toUpperCase() + level.slice(1)}
              </option>
            ))}
          </select>
        </div>

        {/* Effectiveness Rating Range */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Effectiveness Rating
          </label>
          <div className="flex gap-2">
            <input
              type="number"
              placeholder="Min"
              min={availableFilters.effectiveness_range.min}
              max={availableFilters.effectiveness_range.max}
              value={filters.min_effectiveness}
              onChange={(e) => handleChange('min_effectiveness', e.target.value)}
              className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500 text-sm"
            />
            <input
              type="number"
              placeholder="Max"
              min={availableFilters.effectiveness_range.min}
              max={availableFilters.effectiveness_range.max}
              value={filters.max_effectiveness}
              onChange={(e) => handleChange('max_effectiveness', e.target.value)}
              className="w-1/2 px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500 text-sm"
            />
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Range: {availableFilters.effectiveness_range.min} - {availableFilters.effectiveness_range.max}
          </p>
        </div>

        {/* Transition Quality Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Transition Quality
          </label>
          <select
            value={filters.transition_quality}
            onChange={(e) => handleChange('transition_quality', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500 text-sm"
          >
            <option value="">All Qualities</option>
            {availableFilters.transition_qualities.map(quality => (
              <option key={quality} value={quality}>
                {quality.charAt(0).toUpperCase() + quality.slice(1)}
              </option>
            ))}
          </select>
        </div>

        {/* Technique Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Technique
          </label>
          <select
            value={filters.technique}
            onChange={(e) => handleChange('technique', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500 text-sm"
          >
            <option value="">All Techniques</option>
            {availableFilters.techniques.slice(0, 20).map(technique => (
              <option key={technique} value={technique}>
                {technique}
              </option>
            ))}
          </select>
          {availableFilters.techniques.length > 20 && (
            <p className="text-xs text-gray-500 mt-1">
              Showing top 20 of {availableFilters.techniques.length} techniques
            </p>
          )}
        </div>
      </div>
    </div>
  )
}

export default InvestmentFilterSidebar
