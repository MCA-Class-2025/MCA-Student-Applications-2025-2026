import React from 'react';
import { ThemeProvider } from './contexts/ThemeContext';
import { AuthProvider } from './contexts/AuthContext';
import { DashboardLayout } from './components/layout/DashboardLayout';
import { DashboardPage } from './pages/DashboardPage';
import { ChatPage } from './pages/ChatPage';
import { SummarizerPage } from './pages/SummarizerPage';
import { FlashcardsPage } from './pages/FlashcardsPage';
import { McqPage } from './pages/McqPage';
import { PlannerPage } from './pages/PlannerPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { FusionPage } from './pages/FusionPage';
import { ActiveTab } from './types';

export const App: React.FC = () => {
  const renderActiveTab = (activeTab: ActiveTab, setActiveTab: (tab: ActiveTab) => void) => {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardPage setActiveTab={setActiveTab} />;
      case 'chat':
        return <ChatPage />;
      case 'summarizer':
        return <SummarizerPage />;
      case 'flashcards':
        return <FlashcardsPage />;
      case 'mcqs':
        return <McqPage />;
      case 'planner':
        return <PlannerPage />;
      case 'analytics':
        return <AnalyticsPage />;
      case 'fusion':
        return <FusionPage />;
      default:
        return <DashboardPage setActiveTab={setActiveTab} />;
    }
  };

  return (
    <AuthProvider>
      <ThemeProvider>
        <DashboardLayout>
          {(activeTab, setActiveTab) => renderActiveTab(activeTab, setActiveTab)}
        </DashboardLayout>
      </ThemeProvider>
    </AuthProvider>
  );
};

export default App;
