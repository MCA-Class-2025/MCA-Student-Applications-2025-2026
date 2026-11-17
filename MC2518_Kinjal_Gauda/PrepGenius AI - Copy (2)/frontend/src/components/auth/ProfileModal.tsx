import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, User, Mail, Shield, Calendar, LogOut, Check, AlertCircle } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../ui/Button';
import { authApi } from '../../services/authApi';

interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ProfileModal: React.FC<ProfileModalProps> = ({ isOpen, onClose }) => {
  const { user, logout, updateUser } = useAuth();

  const [fullName, setFullName] = useState(user?.full_name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen || !user) return null;

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setLoading(true);

    try {
      const updated = await authApi.updateProfile({
        full_name: fullName,
        email: email !== user.email ? email : undefined,
        current_password: currentPassword || undefined,
        new_password: newPassword || undefined,
      });
      updateUser(updated);
      setSuccess('Profile updated successfully!');
      setCurrentPassword('');
      setNewPassword('');
    } catch (err: any) {
      setError(err.response?.data?.error?.message || err.message || 'Failed to update profile.');
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
          className="relative w-full max-w-lg glass-card rounded-3xl p-6 border border-brand-indigo/40 shadow-2xl space-y-6 max-h-[90vh] overflow-y-auto"
        >
          <button
            onClick={onClose}
            className="absolute top-5 right-5 p-2 rounded-xl bg-dark-surface hover:bg-dark-hover text-dark-muted hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>

          <div className="flex items-center gap-4 border-b border-dark-border pb-5">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-brand-indigo via-brand-violet to-brand-cyan flex items-center justify-center text-white text-xl font-bold shadow-lg border border-white/20">
              {user.username.charAt(0).toUpperCase()}
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">{user.full_name || user.username}</h2>
              <div className="flex items-center gap-2 text-xs text-dark-muted mt-0.5">
                <span>@{user.username}</span>
                <span>•</span>
                <span className="text-brand-emerald font-semibold">Active Student</span>
              </div>
            </div>
          </div>

          {success && (
            <div className="p-3 rounded-xl bg-brand-emerald/10 border border-brand-emerald/30 text-brand-emerald text-xs flex items-center gap-2">
              <Check className="w-4 h-4" />
              <span>{success}</span>
            </div>
          )}

          {error && (
            <div className="p-3 rounded-xl bg-brand-rose/10 border border-brand-rose/30 text-brand-rose text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleUpdate} className="space-y-4 text-xs">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="font-semibold text-dark-muted mb-1 block">Full Name</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full bg-dark-bg/80 border border-dark-border rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-indigo"
                />
              </div>

              <div>
                <label className="font-semibold text-dark-muted mb-1 block">Email Address</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-dark-bg/80 border border-dark-border rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-indigo"
                />
              </div>
            </div>

            <div className="pt-2 border-t border-dark-border">
              <span className="font-bold text-white uppercase tracking-wider text-[11px] mb-3 block">
                Change Password (Optional)
              </span>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="font-semibold text-dark-muted mb-1 block">Current Password</label>
                  <input
                    type="password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full bg-dark-bg/80 border border-dark-border rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-indigo"
                  />
                </div>

                <div>
                  <label className="font-semibold text-dark-muted mb-1 block">New Password</label>
                  <input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full bg-dark-bg/80 border border-dark-border rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-brand-indigo"
                  />
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-dark-border">
              <Button
                type="button"
                variant="outline"
                size="sm"
                icon={<LogOut className="w-4 h-4 text-brand-rose" />}
                onClick={() => { logout(); onClose(); }}
                className="text-brand-rose hover:bg-brand-rose/10 hover:border-brand-rose/30"
              >
                Sign Out
              </Button>

              <Button type="submit" variant="primary" size="sm" disabled={loading}>
                {loading ? 'Saving...' : 'Save Profile Changes'}
              </Button>
            </div>
          </form>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
