import React, { useState } from 'react'

function InvestmentResultCard({ result, searchQuery }) {
  const [expanded, setExpanded] = useState(false)

  const analysis = result.analysis || {}
  const leadUp = analysis.lead_up || {}
  const introduction = analysis.investment_introduction || {}
  const reaction = analysis.reaction || {}
  const sentiment = analysis.sentiment || {}

  // Badge colors
  const methodColors = {
    direct: 'bg-blue-100 text-blue-800',
    indirect: 'bg-purple-100 text-purple-800'
  }

  const interestColors = {
    low: 'bg-red-100 text-red-800',
    medium: 'bg-yellow-100 text-yellow-800',
    high: 'bg-green-100 text-green-800'
  }

  const transitionColors = {
    natural: 'bg-green-100 text-green-800',
    forced: 'bg-orange-100 text-orange-800'
  }

  const getEffectivenessColor = (rating) => {
    if (rating >= 8) return 'text-green-600'
    if (rating >= 5) return 'text-yellow-600'
    return 'text-red-600'
  }

  // Highlight search query in text
  const highlightText = (text) => {
    if (!searchQuery || !text) return text
    const regex = new RegExp(`(${searchQuery})`, 'gi')
    const parts = text.split(regex)
    return parts.map((part, i) =>
      regex.test(part) ? (
        <span key={i} className="bg-yellow-200">{part}</span>
      ) : (
        part
      )
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border hover:shadow-md transition">
      {/* Card Header */}
      <div
        className="p-4 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start justify-between">
          <div className="flex-1">
            {/* Metadata */}
            <div className="flex items-center gap-2 mb-2 text-sm text-gray-500">
              <span className="font-medium">{result.file_name}</span>
              <span>•</span>
              <span>{new Date(result.timestamp).toLocaleString()}</span>
              <span>•</span>
              <span>Message #{result.message_index}</span>
            </div>

            {/* Key Metrics */}
            <div className="flex flex-wrap items-center gap-2 mb-3">
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${methodColors[introduction.method]}`}>
                {introduction.method}
              </span>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${interestColors[reaction.interest_level]}`}>
                {reaction.interest_level} interest
              </span>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${transitionColors[leadUp.transition_quality]}`}>
                {leadUp.transition_quality} transition
              </span>
              <span className={`text-sm font-semibold ${getEffectivenessColor(introduction.effectiveness_rating)}`}>
                Effectiveness: {introduction.effectiveness_rating}/10
              </span>
            </div>

            {/* Investment Introduction Preview */}
            <div className="text-gray-700 mb-2">
              <p className="font-medium text-sm text-gray-600 mb-1">Investment Introduction:</p>
              <p className="text-sm line-clamp-2">
                {highlightText(introduction.exact_phrasing)}
              </p>
            </div>

            {/* Techniques */}
            <div className="flex flex-wrap gap-1">
              {introduction.key_techniques_used && introduction.key_techniques_used.map((tech, idx) => (
                <span
                  key={idx}
                  className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs"
                >
                  {tech}
                </span>
              ))}
            </div>
          </div>

          {/* Expand Icon */}
          <div className="ml-4">
            <svg
              className={`w-5 h-5 text-gray-400 transition-transform ${expanded ? 'rotate-180' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </div>
      </div>

      {/* Expanded Content */}
      {expanded && (
        <div className="border-t px-4 py-4 bg-gray-50 space-y-4">
          {/* Lead Up */}
          <div>
            <h4 className="font-semibold text-sm text-gray-900 mb-2">Lead Up Context</h4>
            <div className="bg-white rounded p-3 text-sm">
              <div className="mb-2">
                <span className="font-medium text-gray-700">Previous Topics: </span>
                <span className="text-gray-600">
                  {leadUp.previous_topics && leadUp.previous_topics.join(', ')}
                </span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Trust Building: </span>
                <span className="text-gray-600">
                  {leadUp.trust_building_elements && leadUp.trust_building_elements.join(', ')}
                </span>
              </div>
            </div>
          </div>

          {/* Full Investment Introduction */}
          <div>
            <h4 className="font-semibold text-sm text-gray-900 mb-2">Full Investment Introduction</h4>
            <div className="bg-white rounded p-3">
              <p className="text-sm text-gray-700 italic">
                "{highlightText(introduction.exact_phrasing)}"
              </p>
            </div>
          </div>

          {/* Reaction */}
          <div>
            <h4 className="font-semibold text-sm text-gray-900 mb-2">Reaction</h4>
            <div className="bg-white rounded p-3 text-sm space-y-2">
              <div>
                <span className="font-medium text-gray-700">Immediate Response: </span>
                <p className="text-gray-600 italic mt-1">
                  "{highlightText(reaction.immediate_response)}"
                </p>
              </div>
              {reaction.concerns_raised && reaction.concerns_raised.length > 0 && (
                <div>
                  <span className="font-medium text-gray-700">Concerns: </span>
                  <ul className="list-disc list-inside text-gray-600 mt-1">
                    {reaction.concerns_raised.map((concern, idx) => (
                      <li key={idx}>{concern}</li>
                    ))}
                  </ul>
                </div>
              )}
              {reaction.follow_up_questions && reaction.follow_up_questions.length > 0 && (
                <div>
                  <span className="font-medium text-gray-700">Follow-up Questions: </span>
                  <ul className="list-disc list-inside text-gray-600 mt-1">
                    {reaction.follow_up_questions.map((q, idx) => (
                      <li key={idx}>{q}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>

          {/* Sentiment Analysis */}
          <div>
            <h4 className="font-semibold text-sm text-gray-900 mb-2">Sentiment Analysis</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {/* Before */}
              <div className="bg-white rounded p-3 text-sm">
                <p className="font-medium text-gray-700 mb-1">Before</p>
                <p className="text-gray-600">Tone: <span className="capitalize">{sentiment.before?.tone}</span></p>
                <p className="text-gray-600 text-xs mt-1">
                  {sentiment.before?.key_emotions && sentiment.before.key_emotions.join(', ')}
                </p>
              </div>

              {/* During */}
              <div className="bg-white rounded p-3 text-sm">
                <p className="font-medium text-gray-700 mb-1">During</p>
                <p className="text-gray-600">Tone: <span className="capitalize">{sentiment.during?.tone}</span></p>
                <p className="text-gray-600 text-xs mt-1">
                  {sentiment.during?.key_emotions && sentiment.during.key_emotions.join(', ')}
                </p>
              </div>

              {/* After */}
              <div className="bg-white rounded p-3 text-sm">
                <p className="font-medium text-gray-700 mb-1">After</p>
                <p className="text-gray-600">Tone: <span className="capitalize">{sentiment.after?.tone}</span></p>
                <p className="text-gray-600 text-xs mt-1">
                  {sentiment.after?.key_emotions && sentiment.after.key_emotions.join(', ')}
                </p>
              </div>
            </div>

            {/* Notable Shifts */}
            {sentiment.notable_shifts && sentiment.notable_shifts.length > 0 && (
              <div className="mt-2 bg-white rounded p-3 text-sm">
                <span className="font-medium text-gray-700">Notable Shifts: </span>
                <ul className="list-disc list-inside text-gray-600 mt-1">
                  {sentiment.notable_shifts.map((shift, idx) => (
                    <li key={idx}>{shift}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default InvestmentResultCard
