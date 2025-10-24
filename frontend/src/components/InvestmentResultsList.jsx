import React from 'react'
import InvestmentResultCard from './InvestmentResultCard'

function InvestmentResultsList({ results, searchQuery }) {
  if (results.length === 0) {
    return null
  }

  return (
    <div className="space-y-4">
      {results.map((result, index) => (
        <InvestmentResultCard
          key={`${result.file_name}-${result.message_index}-${index}`}
          result={result}
          searchQuery={searchQuery}
        />
      ))}
    </div>
  )
}

export default InvestmentResultsList
