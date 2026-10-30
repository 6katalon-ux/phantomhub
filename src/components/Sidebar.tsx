import React from 'react';
import {
  LayoutDashboard, Bot, Server, Network, Package, Users,
  Wifi, Wallet, Gift, Sparkles, CreditCard, Receipt,
  Bell, Settings, Terminal, X
} from 'lucide-react';
import { TabType } from '../types';

interface SidebarProps {
  activeTab: TabType;
  onSelectTab: (tab: TabType) => void;
  isOpenMobile: boolean;
  onCloseMobile: () => void;
  isRtl: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onSelectTab,
  isOpenMobile,
  onCloseMobile,
  isRtl
}) => {
  const navSections = [
    {
      group: isRtl ? 'داشبورد و مانیتورینگ' : 'Dashboard & Overview',
      items: [
        { id: 'dashboard', label: isRtl ? 'داشبورد اصلی' : 'Dashboard', icon: LayoutDashboard }
      ]
    },
    {
      group: isRtl ? 'هسته اتصال و سرور' : 'Core & Server Integrations',
      items: [
        { id: 'bot_settings', label: isRtl ? 'تنظیمات ربات تلگرام' : 'Telegram Bot', icon: Bot },
        { id: 'xui_connection', label: isRtl ? 'اتصال 3X-UI' : '3X-UI Connection', icon: Server },
        { id: 'inbounds', label: isRtl ? 'مدیریت اینباندها' : 'Inbound Manager', icon: Network }
      ]
    },
    {
      group: isRtl ? 'فروشگاه و اشتراک‌ها' : 'Store & Subscriptions',
      items: [
        { id: 'plans', label: isRtl ? 'مدیریت پلن‌ها' : 'Plans Manager', icon: Package },
        { id: 'users', label: isRtl ? 'مدیریت کاربران' : 'Users Manager', icon: Users },
        { id: 'services', label: isRtl ? 'سرویس‌ها و کانفیگ‌ها' : 'Services & Configs', icon: Wifi }
      ]
    },
    {
      group: isRtl ? 'سیستم مالی و هدایا' : 'Finance & Promotions',
      items: [
        { id: 'wallet', label: isRtl ? 'کیف پول و موجودی' : 'Wallet Manager', icon: Wallet },
        { id: 'payment_settings', label: isRtl ? 'تنظیمات پرداخت' : 'Payment Settings', icon: CreditCard },
        { id: 'transactions', label: isRtl ? 'بررسی واریزی‌ها' : 'Payment Review', icon: Receipt },
        { id: 'gift_codes', label: isRtl ? 'کدهای هدیه' : 'Gift Codes', icon: Gift },
        { id: 'free_trial', label: isRtl ? 'تست رایگان' : 'Free Trial', icon: Sparkles }
      ]
    },
    {
      group: isRtl ? 'مدیریت سامانه' : 'System Administration',
      items: [
        { id: 'notifications', label: isRtl ? 'ارسال اعلان همگانی' : 'Broadcasts', icon: Bell },
        { id: 'system_settings', label: isRtl ? 'تنظیمات سامانه' : 'System Settings', icon: Settings },
        { id: 'logs_backups', label: isRtl ? 'لاگ‌ها و پشتیبان‌گیری' : 'Logs & Backups', icon: Terminal }
      ]
    }
  ];

  return (
    <>
      {/* Mobile Drawer Backdrop */}
      {isOpenMobile && (
        <div
          onClick={onCloseMobile}
          className="fixed inset-0 z-40 bg-black/70 backdrop-blur-sm lg:hidden transition-opacity"
        />
      )}

      {/* Sidebar Container (Desktop Sticky + Mobile Slide Drawer) */}
      <aside
        className={`fixed top-0 bottom-0 z-40 w-72 bg-neutral-950 border-neutral-800/80 p-4 overflow-y-auto transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          isRtl ? 'right-0 border-l' : 'left-0 border-r'
        } ${
          isOpenMobile
            ? 'translate-x-0'
            : isRtl
            ? 'translate-x-full'
            : '-translate-x-full'
        }`}
      >
        {/* Drawer Header (Mobile Close Button) */}
        <div className="flex items-center justify-between pb-3 border-b border-neutral-800/80 mb-4 lg:hidden">
          <span className="text-sm font-semibold text-neutral-200">
            {isRtl ? 'منوی بخش‌های پنل' : 'Navigation Menu'}
          </span>
          <button
            onClick={onCloseMobile}
            className="p-1.5 text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Groups */}
        <nav className="space-y-6 pb-20 lg:pb-6">
          {navSections.map((section, idx) => (
            <div key={idx}>
              <div className="px-3 mb-2 text-[11px] font-semibold tracking-wider text-neutral-500 uppercase">
                {section.group}
              </div>
              <div className="space-y-0.5">
                {section.items.map(item => {
                  const Icon = item.icon;
                  const isActive = activeTab === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => {
                        onSelectTab(item.id as TabType);
                        onCloseMobile();
                      }}
                      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition-all ${
                        isActive
                          ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-sm'
                          : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-900 border border-transparent'
                      }`}
                    >
                      <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-cyan-400' : 'text-neutral-500'}`} />
                      <span className="truncate">{item.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
      </aside>

      {/* Mobile Bottom Navigation Bar (Android Thumb Quick Actions) */}
      <div className="lg:hidden fixed bottom-0 left-0 right-0 z-30 h-14 bg-neutral-950/95 backdrop-blur-md border-t border-neutral-800/80 px-2 flex items-center justify-around">
        <button
          onClick={() => onSelectTab('dashboard')}
          className={`flex flex-col items-center gap-0.5 py-1 px-2 rounded-lg text-[10px] font-medium ${
            activeTab === 'dashboard' ? 'text-cyan-400' : 'text-neutral-400'
          }`}
        >
          <LayoutDashboard className="w-4 h-4" />
          <span>{isRtl ? 'داشبورد' : 'Home'}</span>
        </button>

        <button
          onClick={() => onSelectTab('services')}
          className={`flex flex-col items-center gap-0.5 py-1 px-2 rounded-lg text-[10px] font-medium ${
            activeTab === 'services' ? 'text-cyan-400' : 'text-neutral-400'
          }`}
        >
          <Wifi className="w-4 h-4" />
          <span>{isRtl ? 'سرویس‌ها' : 'Services'}</span>
        </button>

        <button
          onClick={() => onSelectTab('transactions')}
          className={`flex flex-col items-center gap-0.5 py-1 px-2 rounded-lg text-[10px] font-medium ${
            activeTab === 'transactions' ? 'text-cyan-400' : 'text-neutral-400'
          }`}
        >
          <Receipt className="w-4 h-4" />
          <span>{isRtl ? 'واریزی‌ها' : 'Payments'}</span>
        </button>

        <button
          onClick={() => onSelectTab('users')}
          className={`flex flex-col items-center gap-0.5 py-1 px-2 rounded-lg text-[10px] font-medium ${
            activeTab === 'users' ? 'text-cyan-400' : 'text-neutral-400'
          }`}
        >
          <Users className="w-4 h-4" />
          <span>{isRtl ? 'کاربران' : 'Users'}</span>
        </button>

        <button
          onClick={() => onSelectTab('system_settings')}
          className={`flex flex-col items-center gap-0.5 py-1 px-2 rounded-lg text-[10px] font-medium ${
            activeTab === 'system_settings' ? 'text-cyan-400' : 'text-neutral-400'
          }`}
        >
          <Settings className="w-4 h-4" />
          <span>{isRtl ? 'تنظیمات' : 'Settings'}</span>
        </button>
      </div>
    </>
  );
};
