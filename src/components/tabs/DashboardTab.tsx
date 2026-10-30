import React from 'react';
import {
  Users, Wifi, DollarSign, Wallet, Clock, Server, Bot, RefreshCw,
  Plus, ArrowUpRight, CheckCircle2, AlertCircle
} from 'lucide-react';
import { TabType } from '../../types';

interface DashboardTabProps {
  stats: any;
  onSelectTab: (tab: TabType) => void;
  onSyncTraffic: () => void;
  isSyncing: boolean;
  isRtl: boolean;
}

export const DashboardTab: React.FC<DashboardTabProps> = ({
  stats,
  onSelectTab,
  onSyncTraffic,
  isSyncing,
  isRtl
}) => {
  const currency = stats?.currency || 'تومان';

  return (
    <div className="space-y-6">
      {/* Top Banner / Welcome */}
      <div className="bg-neutral-900/60 border border-neutral-800/80 rounded-2xl p-5 sm:p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-lg sm:text-xl font-bold text-neutral-100">
              {isRtl ? 'داشبورد مدیریت فروشگاه VPN' : 'VPN Store Admin Overview'}
            </h1>
            <p className="text-xs text-neutral-400 mt-1">
              {isRtl
                ? 'سامانه یکپارچه مانیتورینگ فروش، ترافیک 3X-UI و کاربران ربات تلگرام'
                : 'Central monitoring for VPN sales, 3X-UI inbounds, and Telegram subscribers'}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onSyncTraffic}
              disabled={isSyncing}
              className="flex items-center gap-2 py-2 px-3.5 bg-neutral-800 hover:bg-neutral-700 text-neutral-200 text-xs font-medium rounded-xl transition-colors border border-neutral-700/60"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-cyan-400 ${isSyncing ? 'animate-spin' : ''}`} />
              <span>{isRtl ? 'سینک دستی 3X-UI' : 'Sync Traffic'}</span>
            </button>
            <button
              onClick={() => onSelectTab('plans')}
              className="flex items-center gap-1.5 py-2 px-3.5 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium rounded-xl transition-colors shadow-md shadow-cyan-950/40"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>{isRtl ? 'افزودن پلن جدید' : 'New Plan'}</span>
            </button>
          </div>
        </div>

        {/* Integration Status Badges */}
        <div className="mt-5 pt-4 border-t border-neutral-800/80 grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="flex items-center justify-between p-2.5 bg-neutral-950/70 border border-neutral-800 rounded-xl text-xs">
            <div className="flex items-center gap-2 text-neutral-300">
              <Server className="w-4 h-4 text-cyan-400" />
              <span>{isRtl ? 'ارتباط با پنل 3X-UI:' : '3X-UI Server:'}</span>
            </div>
            <span className="font-medium text-emerald-400 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" />
              {isRtl ? 'متصل و فعال' : 'Connected'}
            </span>
          </div>

          <div className="flex items-center justify-between p-2.5 bg-neutral-950/70 border border-neutral-800 rounded-xl text-xs">
            <div className="flex items-center gap-2 text-neutral-300">
              <Bot className="w-4 h-4 text-cyan-400" />
              <span>{isRtl ? 'ربات تلگرام:' : 'Telegram Bot:'}</span>
            </div>
            <span className={`font-medium flex items-center gap-1 ${stats?.bot_configured ? 'text-emerald-400' : 'text-amber-400'}`}>
              {stats?.bot_configured ? (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  {isRtl ? 'آماده خدمت' : 'Online'}
                </>
              ) : (
                <>
                  <AlertCircle className="w-3.5 h-3.5" />
                  {isRtl ? 'توکن نیاز است' : 'Token Needed'}
                </>
              )}
            </span>
          </div>

          <div className="flex items-center justify-between p-2.5 bg-neutral-950/70 border border-neutral-800 rounded-xl text-xs">
            <div className="flex items-center gap-2 text-neutral-300">
              <Clock className="w-4 h-4 text-cyan-400" />
              <span>{isRtl ? 'آخرین سینک ترافیک:' : 'Last Sync:'}</span>
            </div>
            <span className="font-mono text-neutral-400 tabular-nums">
              {stats?.last_sync || 'چند لحظه پیش'}
            </span>
          </div>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5 sm:gap-4">
        {/* Total Sales */}
        <div className="bg-neutral-900/60 border border-neutral-800/80 rounded-2xl p-4 sm:p-5">
          <div className="flex items-center justify-between text-neutral-400 text-xs mb-2">
            <span>{isRtl ? 'مجموع فروش اشتراک' : 'Total Sales'}</span>
            <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400">
              <DollarSign className="w-4 h-4" />
            </div>
          </div>
          <div className="text-lg sm:text-xl font-bold text-neutral-100 font-mono tabular-nums">
            {(stats?.total_sales || 0).toLocaleString()} <span className="text-xs font-normal text-neutral-400">{currency}</span>
          </div>
          <div className="text-[11px] text-neutral-500 mt-2">
            {isRtl ? 'مجموع مبالغ کسر شده بابت خرید' : 'Aggregated customer purchases'}
          </div>
        </div>

        {/* Active VPN Services */}
        <div className="bg-neutral-900/60 border border-neutral-800/80 rounded-2xl p-4 sm:p-5">
          <div className="flex items-center justify-between text-neutral-400 text-xs mb-2">
            <span>{isRtl ? 'سرویس‌های فعال' : 'Active Services'}</span>
            <div className="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-400">
              <Wifi className="w-4 h-4" />
            </div>
          </div>
          <div className="text-lg sm:text-xl font-bold text-neutral-100 font-mono tabular-nums">
            {stats?.active_services || 0} <span className="text-xs font-normal text-neutral-400">{isRtl ? 'اکانت' : 'accounts'}</span>
          </div>
          <div className="text-[11px] text-neutral-500 mt-2">
            {stats?.expired_services || 0} {isRtl ? 'سرویس منقضی / تمام شده' : 'expired'}
          </div>
        </div>

        {/* Telegram Registered Users */}
        <div className="bg-neutral-900/60 border border-neutral-800/80 rounded-2xl p-4 sm:p-5">
          <div className="flex items-center justify-between text-neutral-400 text-xs mb-2">
            <span>{isRtl ? 'کاربران ثبت‌نامی' : 'Registered Users'}</span>
            <div className="p-1.5 rounded-lg bg-blue-500/10 text-blue-400">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <div className="text-lg sm:text-xl font-bold text-neutral-100 font-mono tabular-nums">
            {stats?.users_count || 0} <span className="text-xs font-normal text-neutral-400">{isRtl ? 'کاربر' : 'users'}</span>
          </div>
          <div className="text-[11px] text-neutral-500 mt-2">
            {isRtl ? 'ثبت‌نام خودکار از طریق تلگرام' : 'Auto registered via bot'}
          </div>
        </div>

        {/* Pending Payments */}
        <div 
          onClick={() => onSelectTab('transactions')}
          className="bg-neutral-900/60 border border-neutral-800/80 hover:border-amber-500/40 cursor-pointer transition-colors rounded-2xl p-4 sm:p-5"
        >
          <div className="flex items-center justify-between text-neutral-400 text-xs mb-2">
            <span>{isRtl ? 'واریزی‌های در انتظار' : 'Pending Payments'}</span>
            <div className="p-1.5 rounded-lg bg-amber-500/10 text-amber-400">
              <Wallet className="w-4 h-4" />
            </div>
          </div>
          <div className="text-lg sm:text-xl font-bold text-neutral-100 font-mono tabular-nums">
            {stats?.pending_payments || 0} <span className="text-xs font-normal text-amber-400">{isRtl ? 'رسید جدید' : 'receipts'}</span>
          </div>
          <div className="text-[11px] text-cyan-400 mt-2 flex items-center gap-1">
            <span>{isRtl ? 'مشاهده و تایید فیش‌ها' : 'Review & Approve'}</span>
            <ArrowUpRight className="w-3 h-3" />
          </div>
        </div>
      </div>

      {/* Quick Launchpad on Android */}
      <div className="bg-neutral-900/40 border border-neutral-800/80 rounded-2xl p-5">
        <h2 className="text-sm font-semibold text-neutral-200 mb-3">
          {isRtl ? 'دسترسی سریع بخش‌های پرکاربرد (Mobile Shortcuts)' : 'Quick Admin Actions'}
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
          <button
            onClick={() => onSelectTab('services')}
            className="p-3 text-start bg-neutral-950/70 border border-neutral-800/80 hover:border-neutral-700 rounded-xl transition-colors"
          >
            <div className="text-xs font-medium text-neutral-200">{isRtl ? 'لیست کانفیگ‌ها' : 'VPN Configs'}</div>
            <div className="text-[11px] text-neutral-500 mt-0.5">{isRtl ? 'مشاهده، تمدید و کپی' : 'Manage & Copy'}</div>
          </button>

          <button
            onClick={() => onSelectTab('transactions')}
            className="p-3 text-start bg-neutral-950/70 border border-neutral-800/80 hover:border-neutral-700 rounded-xl transition-colors"
          >
            <div className="text-xs font-medium text-neutral-200">{isRtl ? 'تایید فیش کارت' : 'Card Receipts'}</div>
            <div className="text-[11px] text-neutral-500 mt-0.5">{isRtl ? 'شارژ خودکار کیف پول' : 'Approve Payments'}</div>
          </button>

          <button
            onClick={() => onSelectTab('users')}
            className="p-3 text-start bg-neutral-950/70 border border-neutral-800/80 hover:border-neutral-700 rounded-xl transition-colors"
          >
            <div className="text-xs font-medium text-neutral-200">{isRtl ? 'مدیریت کاربران' : 'Users & Wallet'}</div>
            <div className="text-[11px] text-neutral-500 mt-0.5">{isRtl ? 'تغییر موجودی و مسدودی' : 'Balance Adjust'}</div>
          </button>

          <button
            onClick={() => onSelectTab('bot_settings')}
            className="p-3 text-start bg-neutral-950/70 border border-neutral-800/80 hover:border-neutral-700 rounded-xl transition-colors"
          >
            <div className="text-xs font-medium text-neutral-200">{isRtl ? 'تنظیمات ربات' : 'Bot Config'}</div>
            <div className="text-[11px] text-neutral-500 mt-0.5">{isRtl ? 'ویرایش متن خوش‌آمد' : 'Edit Welcome Msg'}</div>
          </button>
        </div>
      </div>
    </div>
  );
};
