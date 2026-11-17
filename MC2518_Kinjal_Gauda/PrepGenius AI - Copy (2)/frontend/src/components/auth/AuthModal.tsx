import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Sparkles, LogIn, UserPlus, Lock, Mail, User, AlertCircle } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../ui/Button';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialMode?: 'login' | 'register';
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, initialMode = 'login' }) => {
  const [mode, setMode] = useState<'login' | 'register'>(initialMode);
  const { login, register } = useAuth();

  // Form states
  const [usernameOrEmail, setUsernameOrEmail] = useState('');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (mode === 'login') {
        await login({ username_or_email: usernameOrEmail, password });
      } else {
        await register({ username, email, password, full_name: fullName });
      }
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.error?.message || err.message || 'Authentication failed. Please check details.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          className="relative w-full max-w-md glass-card rounded-3xl p-6 border border-brand-indigo/40 shadow-2xl space-y-6"
        >
          {/* Close button */}
          <button
            onClick={onClose}
            className="absolute top-5 right-5 p-2 rounded-xl bg-dark-surface hover:bg-dark-hover text-dark-muted hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>

          {/* Modal Header */}
          <div className="text-center space-y-2">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-brand-indigo to-brand-violet mx-auto flex items-center justify-center text-white shadow-lg shadow-brand-indigo/30 border border-white/20">
              <Sparkles className="w-6 h-6" />
            </div>
            <h2 className="text-2xl font-extrabold text-white">
              {mode === 'login' ? 'Welcome Back to PrepGenius' : 'Create PrepGenius Account'}
            </h2>
            <p className="text-xs text-dark-muted">
              {mode === 'login' ? 'Access your AI study assistant & notes' : 'Unlock unlimited RAG AI learning tools'}
            </p>
          </div>

          {/* Tab switchers */}
          <div className="grid grid-cols-2 p-1 rounded-xl bg-dark-bg border border-dark-border text-xs font-semibold">
            <button
              onClick={() => { setMode('login'); setError(null); }}
              className={`py-2 rounded-lg transition-all ${mode === 'login' ? 'bg-brand-indigo text-white shadow' : 'text-dark-muted hover:text-white'}`}
            >
              Sign In
            </button>
            <button
              onClick={() => { setMode('register'); setError(null); }}
              className={`py-2 rounded-lg transition-all ${mode === 'register' ? 'bg-brand-indigo text-white shadow' : 'text-dark-muted hover:text-white'}`}
            >
              Register
            </button>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="p-3 rounded-xl bg-brand-rose/10 border border-brand-rose/30 text-brand-rose text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === 'login' ? (
              <div>
                <label className="text-xs font-semibold text-dark-muted mb-1 block">Username or Email</label>
                <div className="relative">
                  <User className="w-4 h-4 text-dark-muted absolute left-3.5 top-3" />
                  <input
                    type="text"
                    required
                    value={usernameOrEmail}
                    onChange={(e) => setUsernameOrEmail(e.target.value)}
                    placeholder="student@prepgenius.ai or username"
                    className="w-full bg-dark-bg/80 border border-dark-border rounded-xl pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-brand-indigo/60"
                  />
                </div>
              </div>
            ) : (
              <>
                <div>
                  <label className="text-xs font-semibold text-dark-muted mb-1 block">Username</label>
                  <div className="relative">
                    <User className="w-4 h-4 text-dark-muted absolute left-3.5 top-3" />
                    <input
                      type="text"
                      required
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      placeholder="johndoe"
                      className="w-full bg-dark-bg/80 border border-dark-border rounded-xl pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-brand-indigo/60"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-xs font-semibold text-dark-muted mb-1 block">Email Address</label>
                  <div className="relative">
                    <Mail className="w-4 h-4 text-dark-muted absolute left-3.5 top-3" />
                    <input
                      type="email"
                      required
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="student@example.com"
                      className="w-full bg-dark-bg/80 border border-dark-border rounded-xl pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-brand-indigo/60"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-xs font-semibold text-dark-muted mb-1 block">Full Name (Optional)</label>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="John Doe"
                    className="w-full bg-dark-bg/80 border border-dark-border rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-brand-indigo/60"
                  />
                </div>
              </>
            )}

            <div>
              <label className="text-xs font-semibold text-dark-muted mb-1 block">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 text-dark-muted absolute left-3.5 top-3" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-dark-bg/80 border border-dark-border rounded-xl pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-brand-indigo/60"
                />
              </div>
            </div>

            <Button
              type="submit"
              variant="glow"
              className="w-full mt-2"
              disabled={loading}
              icon={mode === 'login' ? <LogIn className="w-4 h-4" /> : <UserPlus className="w-4 h-4" />}
            >
              {loading ? 'Processing...' : mode === 'login' ? 'Sign In to Account' : 'Create Free Account'}
            </Button>
          </form>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
