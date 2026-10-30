import { Menu, Globe, RefreshCw, ShieldCheck, LogOut, User } from 'lucide-react';
import { Language } from '../types';

interface NavbarProps {
  currentLang: Language;
  onToggleLang: () => void;
  onOpenMobileMenu: () => void;
  isSyncing: boolean;
  onSyncTraffic: () => void;
  isRtl: boolean;
  adminUser?: any;
  onLogout?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentLang,
  onToggleLang,
  onOpenMobileMenu,
  isSyncing,
  onSyncTraffic,
  isRtl,
  adminUser,
  onLogout
}) => {
  return (
    <header className="sticky top-0 z-30 h-16 bg-neutral-950/90 backdrop-blur-md border-b border-neutral-800/80 px-4 sm:px-6 flex items-center justify-between gap-4">
      {/* Zone 1: Brand Wordmark (Single text element) */}
      <div className="flex items-center gap-3 shrink-0">
        <button
          onClick={onOpenMobileMenu}
          className="lg:hidden p-2 text-neutral-400 hover:text-neutral-100 hover:bg-neutral-800/60 rounded-xl transition-colors"
          aria-label="Open Navigation Menu"
        >
          <Menu className="w-5 h-5" />
        </button>

        <a href="#dashboard" className="flex items-center gap-2.5 text-base sm:text-lg font-bold tracking-tight text-neutral-100 whitespace-nowrap">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shrink-0">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <span className="font-sans">VPN Store</span>
        </a>
      </div>

      {/* Zone 2: Navigation / Quick Metrics (Desktop) */}
      <div className="hidden md:flex items-center gap-6 text-xs text-neutral-400">
        <div className="flex items-center gap-2">
          <span className="text-neutral-500">{isRtl ? 'سیستم‌عامل سرور:' : 'OS:'}</span>
          <span className="font-mono text-neutral-300">Ubuntu 24.04</span>
        </div>
        <span className="text-neutral-700" aria-hidden="true">·</span>
        <div className="flex items-center gap-2">
          <span className="text-neutral-500">{isRtl ? 'هسته اتصال:' : 'Core:'}</span>
          <span className="font-mono text-neutral-300">3X-UI REST</span>
        </div>
        <span className="text-neutral-700" aria-hidden="true">·</span>
        <div className="flex items-center gap-2">
          <span className="text-neutral-500">{isRtl ? 'ربات:' : 'Bot:'}</span>
          <span className="font-mono text-neutral-300">Aiogram 3</span>
        </div>
      </div>

      {/* Zone 3: Primary Action & Language Toggle */}
      <div className="flex items-center gap-2.5 shrink-0">
        {/* Quick Sync Button */}
        <button
          onClick={onSyncTraffic}
          disabled={isSyncing}
          className="flex items-center gap-1.5 py-1.5 px-3 rounded-lg border border-neutral-800 bg-neutral-900/60 hover:bg-neutral-800 text-xs font-medium text-neutral-300 transition-colors whitespace-nowrap"
          title={isRtl ? 'همگام‌سازی ترافیک با 3X-UI' : 'Sync Traffic with 3X-UI'}
        >
          <RefreshCw className={`w-3.5 h-3.5 text-cyan-400 ${isSyncing ? 'animate-spin' : ''}`} />
          <span className="hidden sm:inline">
            {isRtl ? (isSyncing ? 'در حال سینک...' : 'سینک ترافیک') : (isSyncing ? 'Syncing...' : 'Sync Traffic')}
          </span>
        </button>

        {/* Language Switcher */}
        <button
          onClick={onToggleLang}
          className="flex items-center gap-1.5 py-1.5 px-3 rounded-lg border border-neutral-800 bg-neutral-900/60 hover:bg-neutral-800 text-xs font-medium text-neutral-300 transition-colors whitespace-nowrap"
        >
          <Globe className="w-3.5 h-3.5 text-neutral-400" />
          <span>{currentLang === 'fa' ? 'English' : 'فارسی'}</span>
        </button>

        {/* Admin Badge & Logout */}
        {onLogout && (
          <div className="flex items-center gap-1.5 ps-1 border-s border-neutral-800">
            {adminUser && (
              <span className="hidden xl:flex items-center gap-1 text-[11px] font-mono text-cyan-400/90 bg-cyan-950/40 border border-cyan-800/40 px-2 py-1 rounded-md">
                <User className="w-3 h-3 text-cyan-400" />
                <span>{adminUser.username || 'admin'}</span>
              </span>
            )}
            <button
              onClick={onLogout}
              className="flex items-center gap-1 py-1.5 px-2.5 rounded-lg border border-neutral-800 bg-neutral-900/60 hover:bg-rose-950/40 hover:border-rose-800/50 hover:text-rose-300 text-xs text-neutral-400 transition-colors"
              title={isRtl ? 'خروج از حساب مدیریت' : 'Sign out'}
            >
              <LogOut className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">{isRtl ? 'خروج' : 'Logout'}</span>
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
