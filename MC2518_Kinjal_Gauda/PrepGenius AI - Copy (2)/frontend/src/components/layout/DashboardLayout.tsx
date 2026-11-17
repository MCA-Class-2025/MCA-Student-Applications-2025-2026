import React, { useEffect, useState } from 'react';
import { Navbar } from './Navbar';
import { Sidebar } from './Sidebar';
import { ActiveTab, SystemHealth } from '../../types';
import { healthApi } from '../../services/api';

interface DashboardLayoutProps {
  children: (activeTab: ActiveTab, setActiveTab: (tab: ActiveTab) => void) => React.ReactNode;
}

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children }) => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('dashboard');
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const health = await healthApi.checkHealth();
        setSystemHealth(health);
      } catch (err) {
        console.error('Failed to fetch system health:', err);
      }
    };

    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen flex flex-col bg-dark-bg text-dark-text font-sans">
      <Navbar systemHealth={systemHealth} />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
        <main className="flex-1 p-6 lg:p-8 overflow-y-auto max-h-[calc(100vh-4rem)]">
          {children(activeTab, setActiveTab)}
        </main>
      </div>
    </div>
  );
};
