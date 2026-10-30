import React, { useState } from 'react';
import { Settings, Save, Database, ShieldCheck, HardDrive, RefreshCw } from 'lucide-react';
import { AppSettings } from '../../types';

interface SystemSettingsTabProps {
  settings: AppSettings;
  onSave: (updated: Partial<AppSettings>) => Promise<void>;
  isRtl: boolean;
}

export const SystemSettingsTab: React.FC<SystemSettingsTabProps> = ({
  settings,
  onSave,
  isRtl
}) => {
  const [formData, setFormData] = useState<Partial<AppSettings>>({
    site_name: settings.site_name || 'VPN Store',
    currency: settings.currency || 'تومان',
    sync_interval_mins: settings.sync_interval_mins || 5,
    backup_retention_days: settings.backup_retention_days || 14
  });
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    await onSave(formData);
    setSaving(false);
  };

  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-neutral-800">
        <h1 className="text-lg font-bold text-neutral-100 flex items-center gap-2">
          <Settings className="w-5 h-5 text-cyan-400" />
          <span>{isRtl ? 'تنظیمات کلی سامانه (System Settings)' : 'System Settings'}</span>
        </h1>
        <p className="text-xs text-neutral-400 mt-0.5">
          {isRtl
            ? 'عنوان برند، زمان‌بندی همگام‌سازی ترافیک، نگهداری بکاپ‌ها و پارامترهای دیتابیس SQLite'
            : 'Configure site branding, traffic sync frequency, and backup retention'}
        </p>
      </div>

      {/* System Engine Health Card */}
      <div className="bg-neutral-900/40 border border-neutral-800 rounded-2xl p-5">
        <h2 className="text-xs font-semibold text-neutral-300 uppercase tracking-wider mb-3">
          {isRtl ? 'وضعیت پروسس‌های سامانه در اوبونتو 24.04:' : 'Ubuntu 24.04 Process Status:'}
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div className="p-3 bg-neutral-950 border border-neutral-800/80 rounded-xl flex items-center justify-between">
            <span className="text-neutral-400">وب‌سرور FastAPI:</span>
            <span className="text-emerald-400 font-medium font-mono">active (running)</span>
          </div>
          <div className="p-3 bg-neutral-950 border border-neutral-800/80 rounded-xl flex items-center justify-between">
            <span className="text-neutral-400">ربات Aiogram 3:</span>
            <span className="text-emerald-400 font-medium font-mono">active (running)</span>
          </div>
          <div className="p-3 bg-neutral-950 border border-neutral-800/80 rounded-xl flex items-center justify-between">
            <span className="text-neutral-400">دیتابیس SQLite:</span>
            <span className="text-emerald-400 font-medium font-mono">WAL Mode (OK)</span>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="bg-neutral-900/60 border border-neutral-800/80 rounded-2xl p-5 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-neutral-200 mb-1.5">
                {isRtl ? 'نام برند و عنوان فروشگاه:' : 'Store Name / Brand:'}
              </label>
              <input
                type="text"
                value={formData.site_name}
                onChange={e => setFormData({ ...formData, site_name: e.target.value })}
                placeholder="VPN Store"
                className="w-full px-3.5 py-2.5 bg-neutral-950 border border-neutral-800 rounded-xl text-xs text-neutral-200 focus:outline-none focus:border-cyan-500/60 transition-colors"
                required
              />
              <p className="text-[11px] text-neutral-500 mt-1">
                {isRtl ? 'این نام در پیام‌های ربات و ریمارک کانفیگ‌های تولیدی قرار می‌گیرد.' : 'Prefix used in bot headers and config remarks'}
              </p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-neutral-200 mb-1.5">
                {isRtl ? 'دوره همگام‌سازی ترافیک با 3X-UI (دقیقه):' : 'Traffic Sync Interval (minutes):'}
              </label>
              <input
                type="number"
                value={formData.sync_interval_mins}
                onChange={e => setFormData({ ...formData, sync_interval_mins: parseInt(e.target.value) || 5 })}
                className="w-full px-3.5 py-2.5 bg-neutral-950 border border-neutral-800 rounded-xl text-xs font-mono text-neutral-200 focus:outline-none focus:border-cyan-500/60 transition-colors"
                required
              />
              <p className="text-[11px] text-neutral-500 mt-1">
                {isRtl ? 'جاب پس‌زمینه هر چند دقیقه یکبار ترافیک مصرفی را از 3X-UI بخواند.' : 'Worker query frequency for data usage update'}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
            <div>
              <label className="block text-xs font-semibold text-neutral-200 mb-1.5">
                {isRtl ? 'مدت نگهداری فایل‌های بکاپ دیتابیس (روز):' : 'Backup Retention (Days):'}
              </label>
              <input
                type="number"
                value={formData.backup_retention_days}
                onChange={e => setFormData({ ...formData, backup_retention_days: parseInt(e.target.value) || 14 })}
                className="w-full px-3.5 py-2.5 bg-neutral-950 border border-neutral-800 rounded-xl text-xs font-mono text-neutral-200 focus:outline-none focus:border-cyan-500/60 transition-colors"
                required
              />
              <p className="text-[11px] text-neutral-500 mt-1">
                {isRtl ? 'بکاپ‌های قدیمی‌تر از این تعداد روز به طور خودکار پاک می‌شوند.' : 'Purge SQLite point-in-time backups older than X days'}
              </p>
            </div>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 py-2.5 px-6 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold rounded-xl transition-all shadow-lg active:scale-[0.98]"
          >
            <Save className="w-4 h-4" />
            <span>{saving ? (isRtl ? 'در حال ذخیره‌سازی...' : 'Saving...') : (isRtl ? 'ذخیره تنظیمات سیستم' : 'Save System Settings')}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
