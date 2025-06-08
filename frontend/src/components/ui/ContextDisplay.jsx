import { useState } from 'react'
import { BookOpenIcon, ChevronDownIcon, ChevronUpIcon, SearchIcon } from 'lucide-react'

const ContextDisplay = ({ contextInfo }) => {
  const [isExpanded, setIsExpanded] = useState(false)

  if (!contextInfo || !contextInfo.chunks_used?.length) {
    return null
  }

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg overflow-hidden">
      {/* Header */}
      <div 
        className="px-4 py-3 cursor-pointer select-none bg-blue-100"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <SearchIcon className="w-4 h-4 text-blue-600" />
            <span className="font-medium text-blue-900">
              Contexto Utilizado
            </span>
            
            {/* Context Stats */}
            <div className="flex items-center space-x-4 text-sm text-blue-700">
              <span>{contextInfo.total_chunks} chunks</span>
              {contextInfo.avg_similarity && (
                <span>~{(contextInfo.avg_similarity * 100).toFixed(0)}% similitud</span>
              )}
            </div>
          </div>

          {/* Expand Icon */}
          {isExpanded ? (
            <ChevronUpIcon className="w-4 h-4 text-blue-600" />
          ) : (
            <ChevronDownIcon className="w-4 h-4 text-blue-600" />
          )}
        </div>
      </div>

      {/* Content */}
      {isExpanded && (
        <div className="bg-white border-t border-blue-200">
          {/* Context Preview */}
          {contextInfo.context_text && (
            <div className="p-4 border-b border-blue-100">
              <h4 className="text-sm font-medium text-gray-900 mb-2 flex items-center">
                <BookOpenIcon className="w-4 h-4 mr-1" />
                Contexto Enviado a las IAs:
              </h4>
              <div className="bg-gray-50 rounded-lg p-3 max-h-48 overflow-y-auto">
                <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono">
                  {contextInfo.context_text.substring(0, 1000)}
                  {contextInfo.context_text.length > 1000 && '...'}
                </pre>
              </div>
            </div>
          )}

          {/* Individual Chunks */}
          {contextInfo.chunks_used && contextInfo.chunks_used.length > 0 && (
            <div className="p-4">
              <h4 className="text-sm font-medium text-gray-900 mb-3">
                Fragmentos Individuales ({contextInfo.chunks_used.length}):
              </h4>
              <div className="space-y-3">
                {contextInfo.chunks_used.map((chunk, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-medium text-gray-600">
                          Chunk #{index + 1}
                        </span>
                        {chunk.source_type && (
                          <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">
                            {chunk.source_type}
                          </span>
                        )}
                      </div>
                      {chunk.similarity_score && (
                        <span className="text-xs text-blue-600 font-mono">
                          {(chunk.similarity_score * 100).toFixed(1)}% similar
                        </span>
                      )}
                    </div>
                    
                    <div className="bg-gray-50 rounded p-2">
                      <p className="text-xs text-gray-700 leading-relaxed">
                        {chunk.content_text?.substring(0, 200)}
                        {chunk.content_text?.length > 200 && '...'}
                      </p>
                    </div>
                    
                    {chunk.source_identifier && (
                      <div className="mt-2 text-xs text-gray-500">
                        Fuente: {chunk.source_identifier}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default ContextDisplay 