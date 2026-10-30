import React, { useState } from 'react';
import { ShieldCheck, Lock, User, Eye, EyeOff, LogIn, AlertCircle, Terminal, Globe } from 'lucide-react';
import { api } from '../services/api';
import { Language } from '../types';

interface LoginScreenProps {
  onLoginSuccess: (admin: any) => void;
  lang: Language;
  onToggleLang: () => void;
}

export const LoginScreen: React.FC<LoginScreenProps> = ({
  onLoginSuccess,
  lang,
  onToggleLang
}) => {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showHelp, setShowHelp] = useState(false);

  const isRtl = lang === 'fa';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      setError(isRtl ? 'لطفاً نام‌کاربری و رمز عبور را وارد نمایید' : 'Please enter username and password');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await api.login(username.trim(), password);
      onLoginSuccess(data.admin);
    } catch (err: any) {
      setError(err.message || (isRtl ? 'نام کاربری یا رمز عبور اشتباه است' : 'Invalid username or password'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 flex flex-col justify-center items-center p-4 sm:p-6 selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* Top Bar with Language switcher */}
      <div className="absolute top-4 right-4 rtl:right-auto rtl:left-4">
        <button
          onClick={onToggleLang}
          className="flex items-center gap-1.5 py-1.5 px-3 rounded-xl border border-neutral-800 bg-neutral-900/60 hover:bg-neutral-800 text-xs font-medium text-neutral-300 transition-colors"
        >
          <Globe className="w-3.5 h-3.5 text-neutral-400" />
          <span>{lang === 'fa' ? 'English' : 'فارسی'}</span>
        </button>
      </div>

      <div className="w-full max-w-md">
        {/* Logo and Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 shadow-lg shadow-cyan-950/40 mb-4">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-neutral-100 font-sans">
            VPN Store
          </h1>
          <p className="text-sm text-neutral-400 mt-1.5">
            {isRtl ? 'ورود به پنل مدیریت سرور' : 'Server Administration Sign In'}
          </p>
        </div>

        {/* Card */}
        <div className="bg-neutral-900/70 border border-neutral-800/80 rounded-3xl p-6 sm:p-8 backdrop-blur-xl shadow-2xl shadow-black/80">
          {error && (
            <div className="mb-6 p-4 rounded-2xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs flex items-start gap-3 animate-in fade-in">
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <div className="font-semibold">{error}</div>
                {error.includes('Authentication') || error.includes('Invalid') ? (
                  <p className="text-rose-400/80 text-[11px]">
                    {isRtl
                      ? 'در صورت فراموشی رمز عبور، دستور راهنما در پایین صفحه را بررسی کنید.'
                      : 'If you forgot your password, see the reset command below.'}
                  </p>
                ) : null}
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Username */}
            <div>
              <label className="block text-xs font-medium text-neutral-300 mb-1.5">
                {isRtl ? 'نام کاربری ادمین:' : 'Admin Username:'}
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 start-0 flex items-center ps-3.5 pointer-events-none text-neutral-500">
                  <User className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  placeholder="admin"
                  autoComplete="username"
                  required
                  className="w-full ps-10 pe-4 py-2.5 bg-neutral-950 border border-neutral-800 rounded-xl text-sm font-mono text-neutral-100 focus:outline-none focus:border-cyan-500/60 transition-colors"
                />
              </div>
            </div>

            {/* Password */}
            <div>
              <label className="block text-xs font-medium text-neutral-300 mb-1.5">
                {isRtl ? 'رمز عبور:' : 'Password:'}
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 start-0 flex items-center ps-3.5 pointer-events-none text-neutral-500">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder={isRtl ? 'رمز عبور پنل' : 'Enter password'}
                  autoComplete="current-password"
                  required
                  className="w-full ps-10 pe-11 py-2.5 bg-neutral-950 border border-neutral-800 rounded-xl text-sm font-mono text-neutral-100 focus:outline-none focus:border-cyan-500/60 transition-colors"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 end-0 flex items-center pe-3.5 text-neutral-500 hover:text-neutral-300 transition-colors"
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 text-neutral-950 font-bold rounded-xl text-sm transition-all shadow-lg shadow-cyan-950/50 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed mt-2"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-neutral-950 border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <LogIn className="w-4 h-4" />
                  <span>{isRtl ? 'ورود به پنل' : 'Sign In'}</span>
                </>
              )}
            </button>
          </form>

          {/* Reset password terminal helper */}
          <div className="mt-6 pt-5 border-t border-neutral-800/80 text-center">
            <button
              type="button"
              onClick={() => setShowHelp(!showHelp)}
              className="text-xs text-neutral-400 hover:text-cyan-400 transition-colors inline-flex items-center gap-1.5"
            >
              <Terminal className="w-3.5 h-3.5" />
              <span>{isRtl ? 'رمز عبور خود را فراموش کرده‌اید؟' : 'Forgot your admin password?'}</span>
            </button>

            {showHelp && (
              <div className="mt-3 p-3.5 rounded-xl bg-neutral-950/80 border border-neutral-800 text-start text-xs space-y-2 animate-in fade-in">
                <p className="text-neutral-400 text-[11px] leading-relaxed">
                  {isRtl
                    ? 'کافیست در ترمینال SSH سرور، دستور زیر را اجرا کنید تا پسورد به admin تغییر کند:'
                    : 'Execute this command in your server SSH terminal to reset password to admin:'}
                </p>
                <div className="bg-black/60 p-2.5 rounded-lg font-mono text-[11px] text-cyan-300 border border-neutral-800/80 select-all overflow-x-auto">
                  sudo python3 reset_password.py admin admin
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer info */}
        <p className="text-center text-[11px] text-neutral-600 mt-6">
          Ubuntu 24.04 LTS · FastAPI · 3X-UI REST API · SQLite
        </p>
      </div>
    </div>
  );
};
