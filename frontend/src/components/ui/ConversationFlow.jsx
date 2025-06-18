import { useState } from 'react'
import { ChevronDownIcon, ChevronUpIcon, BrainIcon, MessageSquareIcon, SparklesIcon } from 'lucide-react'

const AccordionSection = ({ title, icon: Icon, isOpen, onToggle, children }) => {
  return (
    <div className="border rounded-lg mb-4 bg-white shadow-sm">
      <button
        className="w-full flex items-center justify-between p-4 text-left"
        onClick={onToggle}
      >
        <div className="flex items-center space-x-2">
          <Icon className="w-5 h-5 text-purple-600" />
          <span className="font-medium text-gray-900">{title}</span>
        </div>
        {isOpen ? (
          <ChevronUpIcon className="w-5 h-5 text-gray-500" />
        ) : (
          <ChevronDownIcon className="w-5 h-5 text-gray-500" />
        )}
      </button>
      {isOpen && (
        <div className="px-4 pb-4 text-gray-600">
          {children}
        </div>
      )}
    </div>
  )
}

const ConversationFlow = ({
  preAnalystResult,
  clarificationSession,
  continuityInfo,
  lastConversationContext,
  aiResponses,
  moderatedResponse
}) => {
  const [openSections, setOpenSections] = useState({
    preAnalysis: true,
    clarification: true,
    continuity: true,
    responses: true
  })

  const toggleSection = (section) => {
    setOpenSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }))
  }

  return (
    <div className="space-y-4">
      {/* PreAnalyst Section */}
      {preAnalystResult && (
        <AccordionSection
          title="Análisis Previo"
          icon={BrainIcon}
          isOpen={openSections.preAnalysis}
          onToggle={() => toggleSection('preAnalysis')}
        >
          <div className="space-y-3">
            <div>
              <h4 className="font-medium text-gray-700">Intención Interpretada:</h4>
              <p className="text-gray-600">{preAnalystResult.interpreted_intent}</p>
            </div>
            {preAnalystResult.clarification_questions?.length > 0 && (
              <div>
                <h4 className="font-medium text-gray-700">Preguntas de Clarificación:</h4>
                <ul className="list-disc list-inside space-y-1">
                  {preAnalystResult.clarification_questions.map((q, i) => (
                    <li key={i} className="text-gray-600">{q}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </AccordionSection>
      )}

      {/* Clarification Session */}
      {clarificationSession && (
        <AccordionSection
          title="Sesión de Clarificación"
          icon={MessageSquareIcon}
          isOpen={openSections.clarification}
          onToggle={() => toggleSection('clarification')}
        >
          <div className="space-y-3">
            <div className="bg-purple-50 p-3 rounded-lg">
              <p className="text-sm text-purple-700">
                Estamos refinando tu consulta para obtener la mejor respuesta posible
              </p>
            </div>
            {clarificationSession.questions_and_answers?.map((qa, i) => (
              <div key={i} className="space-y-2">
                <p className="font-medium text-purple-600">Orquix: {qa.question}</p>
                {qa.answer && (
                  <p className="text-gray-600">Tú: {qa.answer}</p>
                )}
              </div>
            ))}
          </div>
        </AccordionSection>
      )}

      {/* Continuity Info */}
      {continuityInfo && (
        <AccordionSection
          title="Contexto de Continuidad"
          icon={SparklesIcon}
          isOpen={openSections.continuity}
          onToggle={() => toggleSection('continuity')}
        >
          <div className="space-y-3">
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-gray-700">Tipo de Referencia:</span>
              <span className="text-sm text-gray-600">{continuityInfo.reference_type}</span>
            </div>
            {lastConversationContext && (
              <div>
                <h4 className="font-medium text-gray-700">Contexto Anterior:</h4>
                <p className="text-gray-600">{lastConversationContext.previous_synthesis}</p>
              </div>
            )}
          </div>
        </AccordionSection>
      )}

      {/* AI Responses */}
      {aiResponses?.length > 0 && (
        <AccordionSection
          title="Respuestas de IAs"
          icon={SparklesIcon}
          isOpen={openSections.responses}
          onToggle={() => toggleSection('responses')}
        >
          <div className="space-y-4">
            {aiResponses.map((response, i) => (
              <div key={i} className="border-b pb-4 last:border-b-0 last:pb-0">
                <h4 className="font-medium text-gray-700 mb-2">{response.provider}</h4>
                <p className="text-gray-600 whitespace-pre-wrap">{response.response_text}</p>
              </div>
            ))}
            {moderatedResponse && (
              <div className="mt-4 bg-green-50 p-4 rounded-lg">
                <h4 className="font-medium text-green-700 mb-2">Síntesis Final</h4>
                <p className="text-green-600">{moderatedResponse}</p>
              </div>
            )}
          </div>
        </AccordionSection>
      )}
    </div>
  )
}

export default ConversationFlow 