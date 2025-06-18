import { useState } from 'react'
import LeftSidebar from './components/layout/LeftSidebar'
import CenterColumn from './components/layout/CenterColumn'
import MobileNavigation from './components/layout/MobileNavigation'
import useAppStore from './store/useAppStore'
import './App.css'

function App() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const { activeProject } = useAppStore()

  return (
    <div className="h-screen flex flex-col md:flex-row bg-gray-50">
      {/* Mobile Navigation */}
      <div className="md:hidden">
        <MobileNavigation 
          isOpen={isMobileMenuOpen}
          setIsOpen={setIsMobileMenuOpen}
        />
      </div>

      {/* Left Sidebar - Hidden on mobile */}
      <div className="hidden md:block md:w-64 lg:w-80 flex-shrink-0 border-r border-gray-200 bg-white overflow-y-auto">
        <LeftSidebar />
      </div>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-h-0 bg-white">
        <div className="flex-1 flex flex-col overflow-hidden">
          <CenterColumn 
            activeProject={activeProject}
          />
        </div>
      </main>
    </div>
  )
}

export default App
