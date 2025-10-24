import React, { useState } from 'react'

function ResultCard({ result, searchQuery }) {
  const [expanded, setExpanded] = useState(false)

  const highlightText = (text, query) => {
    if (!query || !text) return text

    const parts = text.split(new RegExp(`(${query})`, 'gi'))
    return parts.map((part, i) =>
      part.toLowerCase() === query.toLowerCase() ? (
        <mark key={i} className="bg-yellow-200 px-1 rounded">{part}</mark>
      ) : (
        part
      )
    )
  }

  const getEmotionColor = (emotion) => {
    const colors = {
      positive: 'bg-green-100 text-green-800',
      negative: 'bg-red-100 text-red-800',
      mixed: 'bg-yellow-100 text-yellow-800',
      neutral: 'bg-gray-100 text-gray-800'
    }
    return colors[emotion] || 'bg-gray-100 text-gray-800'
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border hover:shadow-md transition">
      <div className="p-4">
        {/* Header with metadata */}
        <div className="flex justify-between items-start mb-3">
          <div className="flex items-center gap-2 text-xs text-gray-500">
            {result.date && (
              <span className="inline-flex items-center">
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                {result.date}
              </span>
            )}
            {result.emotion_tone && (
              <span className={`px-2 py-1 rounded text-xs font-medium ${getEmotionColor(result.emotion_tone)}`}>
                {result.emotion_tone}
              </span>
            )}
            {result.potential_scam && (
              <span className="px-2 py-1 rounded text-xs font-medium bg-red-100 text-red-800">
                ⚠️ Potential Scam
              </span>
            )}
          </div>
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-primary-600 hover:text-primary-800 text-sm font-medium"
          >
            {expanded ? 'Show less' : 'Show more'}
          </button>
        </div>

        {/* Question and Answer - Split View */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Portuguese Column */}
          <div className="space-y-3">
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase mb-1">Question (PT)</h4>
              <p className="text-sm text-gray-900">
                {highlightText(result.question_pt, searchQuery)}
              </p>
            </div>
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase mb-1">Answer (PT)</h4>
              <p className="text-sm text-gray-900">
                {highlightText(result.answer_pt, searchQuery)}
              </p>
            </div>
          </div>

          {/* English Column */}
          <div className="space-y-3 bg-gray-50 p-3 rounded">
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase mb-1">Question (EN)</h4>
              <p className="text-sm text-gray-700">
                {highlightText(result.question_en, searchQuery)}
              </p>
            </div>
            <div>
              <h4 className="text-xs font-semibold text-gray-500 uppercase mb-1">Answer (EN)</h4>
              <p className="text-sm text-gray-700">
                {highlightText(result.answer_en, searchQuery)}
              </p>
            </div>
          </div>
        </div>

        {/* Context */}
        {result.context && (
          <div className="mt-3 pt-3 border-t">
            <p className="text-xs text-gray-600">
              <span className="font-medium">Context:</span> {result.context}
            </p>
          </div>
        )}

        {/* Expanded Details */}
        {expanded && (
          <div className="mt-4 pt-4 border-t space-y-2">
            <div className="text-xs">
              <span className="font-medium text-gray-700">File:</span>
              <span className="ml-2 text-gray-600">{result.file_name}</span>
            </div>
            {result.overall_tone && (
              <div className="text-xs">
                <span className="font-medium text-gray-700">Overall Tone:</span>
                <span className="ml-2 text-gray-600">{result.overall_tone}</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default ResultCard
