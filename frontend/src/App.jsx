import { useState } from 'react'
import { config } from './config'
import LeftSidebar from './components/layout/LeftSidebar'
import CenterColumn from './components/layout/CenterColumn'
import RightSidebar from './components/layout/RightSidebar'

function App() {
  const [activeProject, setActiveProject] = useState(null)
  const [moderatorConfig, setModeratorConfig] = useState({
    personality: 'Analytical',
    temperature: 0.7,
    length: 0.5
  })

  return (
    <div className="h-screen bg-gray-50 flex">
      {/* Left Sidebar - 15% */}
      <div className="w-[15%] bg-white border-r border-gray-200 overflow-y-auto">
        <LeftSidebar 
          activeProject={activeProject}
          setActiveProject={setActiveProject}
          moderatorConfig={moderatorConfig}
          setModeratorConfig={setModeratorConfig}
        />
      </div>

      {/* Center Column - 60% */}
      <div className="w-[60%] bg-gray-50 flex flex-col">
        <CenterColumn 
          activeProject={activeProject}
          moderatorConfig={moderatorConfig}
        />
      </div>

      {/* Right Sidebar - 25% */}
      <div className="w-[25%] bg-white border-l border-gray-200 overflow-y-auto">
        <RightSidebar />
      </div>
    </div>
  )
}

export default App
