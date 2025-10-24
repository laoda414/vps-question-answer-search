import React from 'react'
import ResultCard from './ResultCard'

function ResultsList({ results, searchQuery }) {
  return (
    <div className="space-y-4">
      {results.map((result) => (
        <ResultCard key={result.id} result={result} searchQuery={searchQuery} />
      ))}
    </div>
  )
}

export default ResultsList
