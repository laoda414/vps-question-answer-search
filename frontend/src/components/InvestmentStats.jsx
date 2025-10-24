import React from 'react'

function InvestmentStats({ stats, onClose }) {
  if (!stats) return null

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xl font-bold text-gray-900">Statistics Dashboard</h2>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        {/* Total Files */}
        <div className="bg-blue-50 rounded-lg p-4">
          <p className="text-sm text-blue-600 font-medium">Total Files</p>
          <p className="text-2xl font-bold text-blue-900">{stats.total_files}</p>
        </div>

        {/* Total Instances */}
        <div className="bg-green-50 rounded-lg p-4">
          <p className="text-sm text-green-600 font-medium">Total Instances</p>
          <p className="text-2xl font-bold text-green-900">{stats.total_instances}</p>
        </div>

        {/* Average Effectiveness */}
        <div className="bg-purple-50 rounded-lg p-4">
          <p className="text-sm text-purple-600 font-medium">Avg Effectiveness</p>
          <p className="text-2xl font-bold text-purple-900">{stats.average_effectiveness}/10</p>
        </div>

        {/* Method Distribution */}
        <div className="bg-orange-50 rounded-lg p-4">
          <p className="text-sm text-orange-600 font-medium">Direct/Indirect</p>
          <p className="text-2xl font-bold text-orange-900">
            {stats.method_distribution.direct}/{stats.method_distribution.indirect}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Interest Level Distribution */}
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Interest Level Distribution</h3>
          <div className="space-y-2">
            {Object.entries(stats.interest_level_distribution).map(([level, count]) => {
              const total = stats.total_instances
              const percentage = ((count / total) * 100).toFixed(1)
              const colors = {
                low: 'bg-red-500',
                medium: 'bg-yellow-500',
                high: 'bg-green-500'
              }
              return (
                <div key={level}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="capitalize text-gray-700">{level}</span>
                    <span className="text-gray-600">{count} ({percentage}%)</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`${colors[level]} h-2 rounded-full transition-all`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Top Techniques */}
        <div>
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Top Techniques Used</h3>
          <div className="space-y-2">
            {stats.top_techniques.slice(0, 5).map((item, idx) => {
              const maxCount = stats.top_techniques[0].count
              const percentage = ((item.count / maxCount) * 100).toFixed(1)
              return (
                <div key={idx}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-700 truncate">{item.technique}</span>
                    <span className="text-gray-600">{item.count}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-primary-500 h-2 rounded-full transition-all"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}

export default InvestmentStats
