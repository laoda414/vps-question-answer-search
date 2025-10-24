import React from 'react'

function FilterSidebar({ filters, availableFilters, onChange, onReset }) {
  const handleFilterChange = (key, value) => {
    onChange({ ...filters, [key]: value })
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border p-4 sticky top-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-semibold text-gray-900">Filters</h3>
        <button
          onClick={onReset}
          className="text-xs text-primary-600 hover:text-primary-800 font-medium"
        >
          Reset
        </button>
      </div>

      <div className="space-y-4">
        {/* Date Range */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Date Range
          </label>
          <div className="space-y-2">
            <input
              type="date"
              value={filters.dateFrom}
              onChange={(e) => handleFilterChange('dateFrom', e.target.value)}
              min={availableFilters.dateRange.min_date}
              max={availableFilters.dateRange.max_date}
              className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
              placeholder="From"
            />
            <input
              type="date"
              value={filters.dateTo}
              onChange={(e) => handleFilterChange('dateTo', e.target.value)}
              min={availableFilters.dateRange.min_date}
              max={availableFilters.dateRange.max_date}
              className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
              placeholder="To"
            />
          </div>
          {availableFilters.dateRange.min_date && (
            <p className="text-xs text-gray-500 mt-1">
              Range: {availableFilters.dateRange.min_date} to {availableFilters.dateRange.max_date}
            </p>
          )}
        </div>

        {/* Emotion Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Emotion Tone
          </label>
          <select
            value={filters.emotion}
            onChange={(e) => handleFilterChange('emotion', e.target.value)}
            className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
          >
            <option value="">All emotions</option>
            {availableFilters.emotions.map((emotion) => (
              <option key={emotion} value={emotion}>
                {emotion}
              </option>
            ))}
          </select>
        </div>

        {/* Conversation Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Conversation
          </label>
          <select
            value={filters.conversationId}
            onChange={(e) => handleFilterChange('conversationId', e.target.value)}
            className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-primary-500 focus:border-transparent outline-none"
          >
            <option value="">All conversations</option>
            {availableFilters.conversations.map((conv) => (
              <option key={conv.id} value={conv.id}>
                {conv.file_name.replace('analysis_', '').replace('_result.json', '')}
                {' '}({conv.qa_count} QA pairs)
              </option>
            ))}
          </select>
        </div>

        {/* Active Filters Summary */}
        {(filters.dateFrom || filters.dateTo || filters.emotion || filters.conversationId) && (
          <div className="pt-4 border-t">
            <p className="text-xs font-medium text-gray-700 mb-2">Active Filters:</p>
            <div className="space-y-1">
              {filters.dateFrom && (
                <div className="text-xs text-gray-600">
                  📅 From: {filters.dateFrom}
                </div>
              )}
              {filters.dateTo && (
                <div className="text-xs text-gray-600">
                  📅 To: {filters.dateTo}
                </div>
              )}
              {filters.emotion && (
                <div className="text-xs text-gray-600">
                  😊 Emotion: {filters.emotion}
                </div>
              )}
              {filters.conversationId && (
                <div className="text-xs text-gray-600">
                  💬 Specific conversation
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default FilterSidebar
