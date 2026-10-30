import React, { useState } from 'react';
import { Sparkles, Save, ShieldCheck } from 'lucide-react';
import { AppSettings, InboundItem } from '../../types';

interface FreeTrialTabProps {
  settings: AppSettings;
  inbounds: InboundItem[];
  onSave: (updated: Partial<AppSettings>) => Promise<void>;
  isRtl: boolean;
}

export const FreeTrialTab: React.FC<FreeTrialTabProps> = ({
  settings,
  inbounds,
  onSave,
  isRtl
}) => {
  const [formData, setFormData] = useState<Partial<AppSettings>>({
    trial_enabled: settings.trial_enabled ?? true,
    trial_traffic_gb: settings.trial_traffic_gb || 1,
    trial_duration_days: settings.trial_duration_days || 3,
    trial_inbound_id: settings.trial_inbound_id || inbounds[0]?.inbound_id || 1
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
          <Sparkles className="w-5 h-5 text-cyan-400" />
          <span>{isRtl ? 'تنظیمات تست رایگان (Free Trial Settings)' : 'Free Trial Settings'}</span>
        </h1>
        <p className="text-xs text-neutral-400 mt-0.5">
          {isRtl
            ? 'ارائه اشتراک تست ۱ بار برای هر کاربر تلگرام جهت جلب اعتماد خریداران'
            : 'Configure one-time complimentary VPN trials for new Telegram users'}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="bg-neutral-900/60 border border-neutral-800/80 rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-neutral-800/80">
            <div>
              <div className="text-xs font-semibold text-neutral-200">
                {isRtl ? 'فعال بودن دکمه تست رایگان در ربات' : 'Enable Free Trial in Telegram Bot'}
              </div>
              <div className="text-[11px] text-neutral-400">
                {isRtl ? 'کاربران واجد شرایط می‌توانند ۱ بار اشتراک تست دریافت نمایند' : 'Permit eligible users to auto-provision a test client'}
              </div>
            </div>
            <button
              type="button"
              onClick={() => setFormData({ ...formData, trial_enabled: !formData.trial_enabled })}
              className={`w-11 h-6 flex items-center rounded-full p-1 transition-colors ${
                formData.trial_enabled ? 'bg-cyan-600 justify-end' : 'bg-neutral-800 justify-start'
              }`}
            >
              <div className="bg-white w-4 h-4 rounded-full shadow-md" />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
            <div>
              <label className="block text-xs font-semibold text-neutral-200 mb-1.5">
                {isRtl ? 'حجم ترافیک تست (گیگابایت):' : 'Trial Traffic (GB):'}
              </label>
              <input
                type="number"
                value={formData.trial_traffic_gb}
                onChange={e => setFormData({ ...formData, trial_traffic_gb: parseInt(e.target.value) || 1 })}
                className="w-full px-3.5 py-2.5 bg-neutral-950 border border-neutral-800 rounded-xl text-xs font-mono text-neutral-200 focus:outline-none focus:border-cyan-500/60 transition-colors"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-neutral-200 mb-1.5">
                {isRtl ? 'مدت اعتبار تست (روز):' : 'Duration (Days):'}
              </label>
              <input
                type="number"
                value={formData.trial_duration_days}
                onChange={e => setFormData({ ...formData, trial_duration_days: parseInt(e.target.value) || 3 })}
                className="w-full px-3.5 py-2.5 bg-neutral-950 border border-neutral-800 rounded-xl text-xs font-mono text-neutral-200 focus:outline-none focus:border-cyan-500/60 transition-colors"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-neutral-200 mb-1.5">
                {isRtl ? 'اینباند تخصیص‌یافته:' : 'Trial Inbound:'}
              </label>
              <select
                value={formData.trial_inbound_id}
                onChange={e => setFormData({ ...formData, trial_inbound_id: parseInt(e.target.value) || 1 })}
                className="w-full px-3.5 py-2.5 bg-neutral-950 border border-neutral-800 rounded-xl text-xs text-neutral-200 focus:outline-none focus:border-cyan-500/60 transition-colors"
              >
                {inbounds.map(ib => (
                  <option key={ib.id} value={ib.inbound_id}>
                    ID #{ib.inbound_id} - {ib.remark}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 py-2.5 px-6 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold rounded-xl transition-all shadow-lg shadow-cyan-950/50 active:scale-[0.98]"
          >
            <Save className="w-4 h-4" />
            <span>{saving ? (isRtl ? 'در حال ذخیره‌سازی...' : 'Saving...') : (isRtl ? 'ذخیره تنظیمات تست' : 'Save Trial Settings')}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
