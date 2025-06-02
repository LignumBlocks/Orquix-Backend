import { useState } from 'react'
import { ChevronDownIcon, ChevronRightIcon, PlusIcon, SettingsIcon } from 'lucide-react'
import ProjectModal from '../ui/ProjectModal'

const LeftSidebar = ({ activeProject, setActiveProject, moderatorConfig, setModeratorConfig }) => {
  const [projectsExpanded, setProjectsExpanded] = useState(true)
  const [moderatorExpanded, setModeratorExpanded] = useState(true)
  const [sessionsExpanded, setSessionsExpanded] = useState(true)
  const [showProjectModal, setShowProjectModal] = useState(false)
  const [selectedProjectForModal, setSelectedProjectForModal] = useState(null)

  const projects = [
    { id: 1, name: 'Q4 Competitive Analysis', active: true },
    { id: 2, name: 'Marketing Strategy 2024', active: false },
    { id: 3, name: 'UX Research (Archived)', active: false, archived: true }
  ]

  const recentSessions = [
    { id: 1, time: 'Today, 2:30 PM', preview: 'What are the emerging trends...' },
    { id: 2, time: 'Yesterday, 4:45 PM', preview: 'Analyze user behavior...' }
  ]

  const handleProjectClick = (project) => {
    setSelectedProjectForModal(project)
    setShowProjectModal(true)
  }

  return (
    <div className="p-4 h-full custom-scrollbar">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Control Panel</h2>
      
      {/* Projects Section */}
      <div className="mb-6">
        <button
          onClick={() => setProjectsExpanded(!projectsExpanded)}
          className="flex items-center w-full text-left text-sm font-medium text-gray-700 mb-2 smooth-transition hover:text-gray-900"
        >
          {projectsExpanded ? (
            <ChevronDownIcon className="w-4 h-4 mr-1" />
          ) : (
            <ChevronRightIcon className="w-4 h-4 mr-1" />
          )}
          Projects
        </button>
        
        {projectsExpanded && (
          <div className="ml-5 space-y-1">
            {projects.map((project) => (
              <button
                key={project.id}
                onClick={() => handleProjectClick(project)}
                className={`block w-full text-left text-sm py-1 px-2 rounded smooth-transition hover:bg-gray-100 ${
                  project.active ? 'text-blue-600 font-medium' : 'text-gray-600'
                } ${project.archived ? 'italic' : ''}`}
              >
                • {project.name}
              </button>
            ))}
            <button className="flex items-center text-sm text-blue-600 py-1 px-2 hover:bg-blue-50 rounded smooth-transition">
              <PlusIcon className="w-4 h-4 mr-1" />
              New project
            </button>
          </div>
        )}
      </div>

      {/* Moderator Section */}
      <div className="mb-6">
        <button
          onClick={() => setModeratorExpanded(!moderatorExpanded)}
          className="flex items-center w-full text-left text-sm font-medium text-gray-700 mb-2 smooth-transition hover:text-gray-900"
        >
          {moderatorExpanded ? (
            <ChevronDownIcon className="w-4 h-4 mr-1" />
          ) : (
            <ChevronRightIcon className="w-4 h-4 mr-1" />
          )}
          Moderator
        </button>
        
        {moderatorExpanded && (
          <div className="ml-5 space-y-3">
            {/* Personality */}
            <div>
              <label className="block text-xs text-gray-600 mb-1">Personality</label>
              <select 
                value={moderatorConfig.personality}
                onChange={(e) => setModeratorConfig({...moderatorConfig, personality: e.target.value})}
                className="w-full text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent smooth-transition"
              >
                <option value="Analytical">Analytical</option>
                <option value="Creative">Creative</option>
                <option value="Balanced">Balanced</option>
                <option value="Critical">Critical</option>
              </select>
            </div>

            {/* Temperature */}
            <div>
              <label className="block text-xs text-gray-600 mb-1">
                Temperature: {moderatorConfig.temperature}
              </label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={moderatorConfig.temperature}
                onChange={(e) => setModeratorConfig({...moderatorConfig, temperature: parseFloat(e.target.value)})}
                className="w-full h-2 bg-blue-200 rounded-lg appearance-none cursor-pointer slider"
              />
            </div>

            {/* Length */}
            <div>
              <label className="block text-xs text-gray-600 mb-1">
                Length: {moderatorConfig.length}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={moderatorConfig.length}
                onChange={(e) => setModeratorConfig({...moderatorConfig, length: parseFloat(e.target.value)})}
                className="w-full h-2 bg-blue-200 rounded-lg appearance-none cursor-pointer slider"
              />
            </div>
          </div>
        )}
      </div>

      {/* Recent Sessions Section */}
      <div className="mb-6">
        <button
          onClick={() => setSessionsExpanded(!sessionsExpanded)}
          className="flex items-center w-full text-left text-sm font-medium text-gray-700 mb-2 smooth-transition hover:text-gray-900"
        >
          {sessionsExpanded ? (
            <ChevronDownIcon className="w-4 h-4 mr-1" />
          ) : (
            <ChevronRightIcon className="w-4 h-4 mr-1" />
          )}
          Recent Sessions
        </button>
        
        {sessionsExpanded && (
          <div className="ml-5 space-y-2">
            {recentSessions.map((session) => (
              <button
                key={session.id}
                className="block w-full text-left p-2 hover:bg-gray-50 rounded smooth-transition"
              >
                <div className="text-xs text-gray-500">{session.time}</div>
                <div className="text-sm text-gray-700 truncate">{session.preview}</div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Project Modal */}
      {showProjectModal && (
        <ProjectModal 
          project={selectedProjectForModal}
          onClose={() => setShowProjectModal(false)}
        />
      )}
    </div>
  )
}

export default LeftSidebar 