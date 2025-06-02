import { useState } from 'react'
import { MicIcon, SendIcon, VolumeXIcon } from 'lucide-react'

const CenterColumn = ({ activeProject, moderatorConfig }) => {
  const [message, setMessage] = useState('')
  const [isRecording, setIsRecording] = useState(false)

  // Datos de ejemplo que coinciden con la imagen
  const currentQuestion = "What are the main emerging trends in the fintech sector for 2024?"
  const moderatorResponse = "Based on analysis from multiple sources, I identify three key trends: 1) Embedded banking in non-financial ecosystems, 2) Conversational AI for personalized financial advisory, and 3) Real-time payment infrastructure..."

  const handleSendMessage = () => {
    if (message.trim()) {
      // Aquí iría la lógica para enviar el mensaje al backend
      console.log('Sending message:', message)
      setMessage('')
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const toggleRecording = () => {
    setIsRecording(!isRecording)
    // Aquí iría la lógica de speech-to-text
  }

  return (
    <div className="flex flex-col h-full">
      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
        {/* Current Question */}
        <div className="mb-6">
          <div className="bg-blue-600 text-white px-6 py-4 rounded-lg shadow-sm hover-lift smooth-transition">
            <p className="text-lg font-medium">{currentQuestion}</p>
          </div>
        </div>

        {/* Moderator Response */}
        <div className="mb-6">
          <div className="flex items-start space-x-3">
            {/* Moderator Avatar */}
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center hover-lift smooth-transition">
                <span className="text-white font-semibold text-sm">M</span>
              </div>
            </div>
            
            {/* Moderator Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2 mb-2">
                <span className="text-sm font-medium text-gray-900">Moderator</span>
                <button className="text-gray-400 hover:text-gray-600 smooth-transition hover:bg-gray-100 p-1 rounded">
                  <VolumeXIcon className="w-4 h-4" />
                </button>
              </div>
              
              <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm hover-lift smooth-transition">
                <p className="text-gray-700 leading-relaxed">{moderatorResponse}</p>
                
                {/* Expand/Collapse indicator */}
                <div className="mt-3 flex items-center justify-between">
                  <div className="flex space-x-2 text-xs text-gray-500">
                    <span>•••</span>
                  </div>
                  <button className="text-xs text-blue-600 hover:text-blue-800 smooth-transition hover:bg-blue-50 px-2 py-1 rounded">
                    Show more
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 bg-white p-4">
        <div className="flex items-end space-x-3">
          {/* Add File Button */}
          <button className="flex-shrink-0 p-2 text-gray-400 hover:text-gray-600 smooth-transition hover:bg-gray-100 rounded-lg">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
          </button>
          
          {/* Message Input */}
          <div className="flex-1">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type a message..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent smooth-transition hover:border-gray-400"
              rows="1"
              style={{ minHeight: '40px', maxHeight: '120px' }}
            />
          </div>
          
          {/* Microphone Button */}
          <button
            onClick={toggleRecording}
            className={`flex-shrink-0 p-2 rounded-lg smooth-transition ${
              isRecording 
                ? 'bg-red-100 text-red-600 hover:bg-red-200' 
                : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
            }`}
          >
            <MicIcon className="w-5 h-5" />
          </button>
          
          {/* Send Button */}
          <button
            onClick={handleSendMessage}
            disabled={!message.trim()}
            className={`flex-shrink-0 p-2 rounded-lg smooth-transition ${
              message.trim()
                ? 'bg-blue-600 text-white hover:bg-blue-700 hover-lift'
                : 'bg-gray-100 text-gray-400 cursor-not-allowed'
            }`}
          >
            <SendIcon className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  )
}

export default CenterColumn 