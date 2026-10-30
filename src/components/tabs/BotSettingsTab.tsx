import React, { useState } from 'react';
import { Bot, Save, AlertCircle, CheckCircle2, ShieldAlert, Activity, RefreshCw } from 'lucide-react';
import { AppSettings } from '../../types';
import { api } from '../../services/api';

interface BotSettingsTabProps {
  settings: AppSettings;
  onSave: (updated: Partial<AppSettings>) => Promise<void>;
  isRtl: boolean;
}

export const BotSettingsTab: React.FC<BotSettingsTabProps> = ({
  settings,
  onSave,
  isRtl
}) => {
  const [formData, setFormData] = useState<Partial<AppSettings>>({
    bot_token: settings.bot_token || '',
    bot_admin_ids: settings.bot_admin_ids || '',
    bot_welcome_msg: settings.bot_welcome_msg || '',
    bot_support_username: settings.bot_support_username || '',
    bot_enabled: settings.bot_enabled ?? true,
    bot_maintenance: settings.bot_maintenance ?? false
  });
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string; bot?: any } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    await onSave(formData);
    setSaving(false);
  };

  const handleTestBot = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      // First save if edited
      if (formData.bot_token !== settings.bot_token) {
        await onSave(formData);
      }
      const res = await api.testBotToken();
      setTestResult(res);
    } catch (e: any) {
      setTestResult({ success: false, message: e.message || 'خطا در ارتباط' });
    } finally {
      setTesting(false);
    }
  };

  const handleRestartBot = async () => {
    setTesting(true);
    try {
      const res = await api.restartBotService();
      setTestResult({ success: res.success, message: res.message });
    } catch (e: any) {
      setTestResult({ success: false, message: e.message || 'خطا در ریستارت سرویس ربات' });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-neutral-800">
        <div>
          <h1 className="text-lg font-bold text-neutral-100 flex items-center gap-2">
            <Bot className="w-5 h-5 text-cyan-400" />
            <span>{isRtl ? 'تنظیمات ربات تلگرام (Aiogram 3)' : 'Telegram Bot Settings'}</span>
          </h1>
          <p className="text-xs text-neutral-400 mt-0.5">
            {isRtl
              ? 'پیکربندی توکن بات‌فادر، ادمین‌ها و پیام‌های خوش‌آمدگویی ذخیره‌شده در SQLite'
              : 'Manage BotFather token, admin IDs, and welcome messaging'}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleRestartBot}
            disabled={testing}
            className="flex items-center gap-1.5 py-2 px-3.5 bg-neutral-800 hover:bg-neutral-700 text-neutral-300 text-xs font-semibold rounded-xl border border-neutral-700/60 transition-all"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-cyan-400 ${testing ? 'animate-spin' : ''}`} />
            <span>{isRtl ? 'ریستارت ربات' : 'Restart Bot'}</span>
          </button>
          <button
            type="button"
            onClick={handleTestBot}
            disabled={testing}
            className="flex items-center gap-1.5 py-2 px-4 bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 text-xs font-semibold rounded-xl border border-cyan-500/40 transition-all shadow-sm shadow-cyan-950"
          >
            <Activity className={`w-3.5 h-3.5 text-cyan-400 ${testing ? 'animate-pulse' : ''}`} />
            <span>{testing ? (isRtl ? 'در حال بررسی...' : 'Checking...') : (isRtl ? 'تست اتصال ربات' : 'Test Bot Connection')}</span>
          </button>
        </div>
      </div>

      {testResult && (
        <div className={`p-4 rounded-2xl border text-xs flex items-start gap-3 ${
          testResult.success
            ? 'bg-emerald-950/30 border-emerald-800/60 text-emerald-300'
            : 'bg-rose-950/30 border-rose-800/60 text-rose-300'
        }`}>
          {testResult.success ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
          ) : (
            <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          )}
          <div className="space-y-1">
            <div className="font-bold">{testResult.message}</div>
            {testResult.bot && (
              <div className="font-mono text-[11px] text-emerald-400/80">
                Bot ID: {testResult.bot.id} | @{testResult.bot.username}
              </div>
            )}
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Token Card */}
        <div className="bg-neutral-900/60 border border-neutral-800/80 rounded-2xl p-5 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-neutral-200 mb-1.5">
              {isRtl ? 'توکن ربات تلگرام (Bot Token):' : 'Telegram Bot Token:'}
            </label>
            <input
              type="text"
              value={formData.bot_token}
              onChange={e => setFormData({ ...formData, bot_token: e.target.value })}
              placeholder="e.g. 7123456789:AAHq_..."
              className="w-full px-3.5 py-2.5 bg-neutral-950 border border-neutral-800 rounded-xl text-xs font-mono text-neutral-200 focus:outline-none focus:border-cyan-500/60 transition-colors"
            />
            <p className="text-[11px] text-neutral-500 mt-1.5">
              {isRtl
                ? 'توکن دریافتی از @BotFather در تلگرام را اینجا وارد نمایید. پس از ذخیره، سرویس ربات به طور خودکار فعال می‌گردد.'
                : 'Obtain token from @BotFather on Telegram. Service auto-connects upon save.'}
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-neutral-200 mb-1.5">
                {isRtl ? 'آیدی عددی ادمین‌های تلگرام:' : 'Telegram Admin IDs:'}
              </label>
              <input
                type="text"
                value={formData.bot_admin_ids}
                onChange={e => setFormData({ ...formData, bot_admin_ids: e.target.value })}
                placeholder="123456789, 987654321"
                className="w-full px-3.5 py-2.5 bg-neutral-950 border border-neutral-800 rounded-xl text-xs font-mono text-neutral-200 focus:outline-none focus:border-cyan-500/60 transition-colors"
              />
              <p className="text-[11px] text-neutral-500 mt-1">
                {isRtl ? 'آیدی عددی (جدا شده با ویرگول)' : 'Comma-separated numeric Telegram user IDs'}
              </p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-neutral-200 mb-1.5">
                {isRtl ? 'آیدی پشتیبانی در ربات:' : 'Support Username:'}
              </label>
              <input
                type="text"
                value={formData.bot_support_username}
                onChange={e => setFormData({ ...formData, bot_support_username: e.target.value })}
                placeholder="@support_vpn"
                className="w-full px-3.5 py-2.5 bg-neutral-950 border border-neutral-800 rounded-xl text-xs text-neutral-200 focus:outline-none focus:border-cyan-500/60 transition-colors"
              />
              <p className="text-[11px] text-neutral-500 mt-1">
                {isRtl ? 'آیدی تلگرام پشتیبان جهت نمایش در بخش پشتیبانی' : 'Telegram username displayed in support menu'}
              </p>
            </div>
          </div>
        </div>

        {/* Welcome Message Card */}
        <div className="bg-neutral-900/60 border border-neutral-800/80 rounded-2xl p-5 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-neutral-200 mb-1.5">
              {isRtl ? 'متن پیام شروع (/start) ربات:' : 'Bot Welcome Message (/start):'}
            </label>
            <textarea
              rows={4}
              value={formData.bot_welcome_msg}
              onChange={e => setFormData({ ...formData, bot_welcome_msg: e.target.value })}
              className="w-full px-3.5 py-2.5 bg-neutral-950 border border-neutral-800 rounded-xl text-xs text-neutral-200 focus:outline-none focus:border-cyan-500/60 transition-colors"
            />
            <p className="text-[11px] text-neutral-500 mt-1">
              {isRtl ? 'متنی که پس از استارت زدن به کاربر نمایش داده می‌شود.' : 'Message shown to users when sending /start'}
            </p>
          </div>
        </div>

        {/* Toggles Card */}
        <div className="bg-neutral-900/60 border border-neutral-800/80 rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs font-semibold text-neutral-200">
                {isRtl ? 'فعال بودن ربات تلگرام' : 'Enable Telegram Bot'}
              </div>
              <div className="text-[11px] text-neutral-400">
                {isRtl ? 'پاسخگویی ربات به دستورات و کاربران' : 'Allow bot to poll and respond to messages'}
              </div>
            </div>
            <button
              type="button"
              onClick={() => setFormData({ ...formData, bot_enabled: !formData.bot_enabled })}
              className={`w-11 h-6 flex items-center rounded-full p-1 transition-colors ${
                formData.bot_enabled ? 'bg-cyan-600 justify-end' : 'bg-neutral-800 justify-start'
              }`}
            >
              <div className="bg-white w-4 h-4 rounded-full shadow-md" />
            </button>
          </div>

          <div className="pt-3 border-t border-neutral-800/80 flex items-center justify-between">
            <div>
              <div className="text-xs font-semibold text-neutral-200 flex items-center gap-1.5">
                <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
                <span>{isRtl ? 'حالت تعمیر و نگهداری (Maintenance Mode)' : 'Maintenance Mode'}</span>
              </div>
              <div className="text-[11px] text-neutral-400">
                {isRtl ? 'نمایش پیام موقتی به کاربران در حین بروزرسانی سرورها' : 'Temporarily pause purchases during server migration'}
              </div>
            </div>
            <button
              type="button"
              onClick={() => setFormData({ ...formData, bot_maintenance: !formData.bot_maintenance })}
              className={`w-11 h-6 flex items-center rounded-full p-1 transition-colors ${
                formData.bot_maintenance ? 'bg-amber-600 justify-end' : 'bg-neutral-800 justify-start'
              }`}
            >
              <div className="bg-white w-4 h-4 rounded-full shadow-md" />
            </button>
          </div>
        </div>

        {/* Submit */}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 py-2.5 px-6 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold rounded-xl transition-all shadow-lg shadow-cyan-950/50 active:scale-[0.98]"
          >
            <Save className="w-4 h-4" />
            <span>{saving ? (isRtl ? 'در حال ذخیره‌سازی...' : 'Saving...') : (isRtl ? 'ذخیره تنظیمات ربات' : 'Save Bot Settings')}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
