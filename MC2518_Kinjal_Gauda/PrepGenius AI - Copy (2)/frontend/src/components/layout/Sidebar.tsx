import React from 'react';
import { 
  LayoutDashboard, 
  MessageSquare, 
  FileText, 
  Layers, 
  CheckSquare, 
  Calendar, 
  BarChart3, 
  ChevronRight,
  Database,
  Zap
} from 'lucide-react';
import { ActiveTab } from '../../types';

interface SidebarProps {
  activeTab: ActiveTab;
  setActiveTab: (tab: ActiveTab) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab }) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, badge: null },
    { id: 'chat', label: 'AI Tutor Chat', icon: MessageSquare, badge: 'RAG' },
    { id: 'summarizer', label: 'Smart Summarizer', icon: FileText, badge: 'TTS' },
    { id: 'flashcards', label: 'Flashcards', icon: Layers, badge: 'AI' },
    { id: 'mcqs', label: 'MCQ Quiz Generator', icon: CheckSquare, badge: 'Quiz' },
    { id: 'planner', label: 'Study Planner', icon: Calendar, badge: 'Smart' },
    { id: 'analytics', label: 'Study Analytics', icon: BarChart3, badge: 'Score' },
    { id: 'fusion', label: 'Data Fusion Engine', icon: Database, badge: 'Fusion' },
  ] as const;

  return (
    <aside className="w-64 glass-panel border-r border-dark-border flex flex-col justify-between hidden md:flex shrink-0 min-h-[calc(100vh-4rem)]">
      <div className="p-4 space-y-6">
        {/* Navigation Header */}
        <div className="px-3 py-2 text-[11px] font-bold text-dark-muted uppercase tracking-wider">
          Learning Modules
        </div>

        {/* Links list */}
        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;

            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id as ActiveTab)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-gradient-to-r from-brand-indigo/20 to-brand-violet/10 text-white border border-brand-indigo/30 shadow-md shadow-brand-indigo/10'
                    : 'text-dark-muted hover:text-white hover:bg-dark-surface/60'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-brand-indigo' : 'text-dark-muted'}`} />
                  <span>{item.label}</span>
                </div>

                <div className="flex items-center gap-1.5">
                  {item.badge && (
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                      isActive
                        ? 'bg-brand-indigo text-white border-brand-indigo'
                        : 'bg-dark-surface text-dark-muted border-dark-border'
                    }`}>
                      {item.badge}
                    </span>
                  )}
                  {isActive && <ChevronRight className="w-3.5 h-3.5 text-brand-indigo" />}
                </div>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Pro Banner in sidebar bottom */}
      <div className="p-4 m-3 rounded-2xl bg-gradient-to-br from-brand-indigo/20 via-dark-surface to-brand-violet/20 border border-brand-indigo/30 text-center space-y-3">
        <div className="w-8 h-8 rounded-lg bg-brand-indigo/30 border border-brand-indigo/50 flex items-center justify-center mx-auto text-brand-indigo">
          <Zap className="w-4 h-4" />
        </div>
        <div>
          <h4 className="text-xs font-bold text-white">Local Ollama Qwen2.5</h4>
          <p className="text-[11px] text-dark-muted mt-0.5">100% Private & Unlimited AI RAG Engine</p>
        </div>
      </div>
    </aside>
  );
};
