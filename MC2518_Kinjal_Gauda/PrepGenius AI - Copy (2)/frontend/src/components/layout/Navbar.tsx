import React, { useState } from 'react';
import { Sparkles, Cpu, Database, Bell, User, LogIn, UserPlus, LogOut, ShieldCheck } from 'lucide-react';
import { SystemHealth } from '../../types';
import { useAuth } from '../../contexts/AuthContext';
import { AuthModal } from '../auth/AuthModal';
import { ProfileModal } from '../auth/ProfileModal';
import { Button } from '../ui/Button';

interface NavbarProps {
  systemHealth: SystemHealth | null;
}

export const Navbar: React.FC<NavbarProps> = ({ systemHealth }) => {
  const { user, isAuthenticated, logout } = useAuth();
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [profileModalOpen, setProfileModalOpen] = useState(false);

  const openAuth = (mode: 'login' | 'register') => {
    setAuthMode(mode);
    setAuthModalOpen(true);
  };

  return (
    <>
      <header className="sticky top-0 z-30 h-16 glass-panel border-b border-dark-border px-6 flex items-center justify-between">
        {/* Brand logo & tagline */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-brand-indigo via-brand-violet to-brand-cyan flex items-center justify-center shadow-lg shadow-brand-indigo/30 border border-white/20">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-brand-indigo bg-clip-text text-transparent">
                PrepGenius AI
              </span>
              <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-brand-indigo/20 text-brand-indigo border border-brand-indigo/30 tracking-wider">
                PRO v1.0
              </span>
            </div>
            <p className="text-xs text-dark-muted hidden sm:block">
              Next-Gen Autonomous AI Learning Ecosystem
            </p>
          </div>
        </div>

        {/* System Status Indicators & Auth Actions */}
        <div className="flex items-center gap-4">
          {/* Status Badges */}
          <div className="hidden md:flex items-center gap-3 px-3 py-1.5 rounded-xl bg-dark-bg/60 border border-dark-border text-xs">
            <div className="flex items-center gap-1.5" title="SQLite DB Status">
              <Database className="w-3.5 h-3.5 text-dark-muted" />
              <span className={`w-2 h-2 rounded-full ${systemHealth?.database_connected ? 'bg-brand-emerald shadow-[0_0_8px_#10b981]' : 'bg-brand-rose'}`} />
              <span className="text-dark-muted">DB</span>
            </div>

            <div className="h-3 w-[1px] bg-dark-border" />

            <div className="flex items-center gap-1.5" title={`Ollama LLM Status (${systemHealth?.ollama_model || 'qwen2.5:3b'})`}>
              <Cpu className="w-3.5 h-3.5 text-dark-muted" />
              <span className={`w-2 h-2 rounded-full ${systemHealth?.ollama_connected ? 'bg-brand-emerald shadow-[0_0_8px_#10b981]' : 'bg-brand-amber animate-pulse'}`} />
              <span className="text-dark-muted">Ollama ({systemHealth?.ollama_model || 'Qwen2.5'})</span>
            </div>
          </div>

          {/* User Auth Section */}
          {isAuthenticated && user ? (
            <div className="flex items-center gap-3 pl-2 border-l border-dark-border">
              <button
                onClick={() => setProfileModalOpen(true)}
                className="flex items-center gap-2.5 p-1 rounded-xl hover:bg-dark-surface/60 transition-colors text-left group"
              >
                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-indigo to-brand-violet flex items-center justify-center text-white font-bold shadow-md border border-white/20">
                  {user.username.charAt(0).toUpperCase()}
                </div>
                <div className="hidden lg:block">
                  <div className="text-xs font-bold text-white group-hover:text-brand-indigo transition-colors">
                    {user.full_name || user.username}
                  </div>
                  <div className="text-[10px] text-brand-emerald font-semibold flex items-center gap-1">
                    <ShieldCheck className="w-3 h-3" />
                    <span>JWT Verified</span>
                  </div>
                </div>
              </button>

              <button
                onClick={logout}
                title="Sign Out"
                className="w-8 h-8 rounded-lg bg-dark-surface hover:bg-brand-rose/20 text-dark-muted hover:text-brand-rose border border-dark-border transition-colors flex items-center justify-center"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2 pl-2 border-l border-dark-border">
              <Button
                variant="outline"
                size="sm"
                icon={<LogIn className="w-3.5 h-3.5" />}
                onClick={() => openAuth('login')}
              >
                Sign In
              </Button>
              <Button
                variant="primary"
                size="sm"
                icon={<UserPlus className="w-3.5 h-3.5" />}
                onClick={() => openAuth('register')}
              >
                Register
              </Button>
            </div>
          )}
        </div>
      </header>

      {/* Modals */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        initialMode={authMode}
      />

      <ProfileModal
        isOpen={profileModalOpen}
        onClose={() => setProfileModalOpen(false)}
      />
    </>
  );
};
