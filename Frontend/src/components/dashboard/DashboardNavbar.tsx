import React from 'react';
import { Presentation, FileCheck, FileUp } from 'lucide-react';

interface DashboardNavbarProps {
  activeTab: 'slides' | 'reassessment' | 'assessment';
  onTabChange: (tab: 'slides' | 'reassessment' | 'assessment') => void;
}

const tabStyles = (active: boolean) =>
  `flex items-center gap-3 px-4 py-3 rounded-lg font-semibold transition-all duration-300 text-base focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
    active
      ? 'bg-blue-600 text-white shadow-md'
      : 'bg-white text-gray-700 hover:bg-blue-50 hover:text-blue-600'
  }`;

export const DashboardNavbar: React.FC<DashboardNavbarProps> = ({ activeTab, onTabChange }) => (
  <aside className="w-64 h-screen bg-gray-50 p-4 shadow-lg">
    <div className="mb-8 text-center">
        <h1 className="text-2xl font-bold text-gray-800">Dashboard</h1>
    </div>
    <nav className="flex flex-col gap-4">
      <button
        className={tabStyles(activeTab === 'slides')}
        onClick={() => onTabChange('slides')}
        aria-current={activeTab === 'slides' ? 'page' : undefined}
      >
        <Presentation size={20} />
        <span>Slide Presentations</span>
      </button>
      <button
        className={tabStyles(activeTab === 'reassessment')}
        onClick={() => onTabChange('reassessment')}
        aria-current={activeTab === 'reassessment' ? 'page' : undefined}
      >
        <FileCheck size={20} />
        <span>Student Reassessments</span>
      </button>
      <button
        className={tabStyles(activeTab === 'assessment')}
        onClick={() => onTabChange('assessment')}
        aria-current={activeTab === 'assessment' ? 'page' : undefined}
      >
        <FileUp size={20} />
        <span>Upload Assessment</span>
      </button>
    </nav>
  </aside>
);

export default DashboardNavbar;
