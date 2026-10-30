import React, { useState } from 'react';
import { Server, Save, Activity, CheckCircle2, AlertTriangle, ShieldCheck } from 'lucide-react';
import { AppSettings } from '../../types';

interface XUIConnectionTabProps {
  settings: AppSettings;
  onSave: (updated: Partial<AppSettings>) => Promise<void>;
  onTestConnection: () => Promise<any>;
  isRtl: boolean;
}

export const XUIConnectionTab: React.FC<XUIConnectionTabProps> = ({
  settings,
  onSave,
  onTestConnection,
  isRtl
}) => {
  const [formData, setFormData] = useState<Partial<AppSettings>>({
    xui_url: settings.xui_url || 'http://127.0.0.1:2053',
    xui_username: settings.xui_username || 'admin',
    xui_password: settings.xui_password || '',
    xui_token: settings.xui_token || '',
    xui_tls_verify: settings.xui_tls_verify ?? false,
    xui_timeout: settings.xui_timeout || 10,
    xui_default_inbound: settings.xui_default_inbound || 1,
    vpn_server_host: settings.vpn_server_host || '185.190.140.25'
  });

  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    await onSave(formData);
    setSaving(false);
  };

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await onTestConnection();
      setTestResult(res);
    } catch (e: any) {
      setTestResult({ success: false, message: e.message || 'خطا در برقراری ارتباط' });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-neutral-800">
        <div>
          <h1 className="text-lg font-bold text-neutral-100 flex items-center gap-2">
            <Server className="w-5 h-5 text-cyan-400" />
            <span>{isRtl ? 'اتصال به پنل مدیریت 3X-UI' : '3X-UI Connection Settings'}</span>
          </h1>
          <p className="text-xs text-neutral-400 mt-0.5">
            {isRtl
              ? 'پیکربندی آدرس API پنل سنایی / علیرضا، اطلاعات ورود و IP سرور جهت ساخت خودکار کانفیگ‌ها'
              : 'Configure 3X-UI REST API endpoints, credentials, and public server host'}
          </p>
        </div>

        <button
          type="button"
          onClick={handleTest}
          disabled={testing}
          className="flex items-center gap-2 py-2 px-4 bg-neutral-800 hover:bg-neutral-700 text-neutral-200 text-xs font-semibold rounded-xl transition-all border border-neutral-700/60 shadow-sm"
        >
          <Activity className={`w-3.5 h-3.5 text-cyan-400 ${testing ? 'animate-spin' : ''}`} />
          <span>{testing ? (isRtl ? 'در حال تست...' : 'Testing...') : (isRtl ? 'تست اتصال به 3X-UI' : 'Test Connection')}</span>
        </button>
      </div>

      {/* Test Connection Banner */}
      {testResult && (
        <div className={`p-4 rounded-xl border text-xs flex items-start gap-3 animate-in fade-in ${
          testResult.success
            ? 'bg-emerald-950/30 border-emerald-500/40 text-emerald-300'
            : 'bg-rose-950/30 border-rose-500/40 text-rose-300'
        }`}>
          {testResult.success ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
          ) : (
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
          )}
          <div className="flex-1 space-y-1">
            <div className="font-semibold">{testResult.message}</div>
            {testResult.success && (
              <div className="text-[11px] opacity-80 font-mono">
                {isRtl ? `پینگ پاسخگویی: ${testResult.latency_ms}ms · اینباندهای شناسایی‌شده: ${testResult.inbounds_count} عدد` : `Latency: ${testResult.latency_ms}ms · Detected Inbounds: ${testResult.inbounds_count}`}
              </div>
            )}
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="bg-neutral-900/60 border border-neutral-800/80 rounded-2xl p-5 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-neutral-200 mb-1.5">
                {isRtl ? 'آدرس پنل 3X-UI (URL):' : '3X-UI Panel Base URL:'}
              </label>
              <input
                type="text"
                value={formData.xui_url}
                onChange={e => setFormData({ ...formData, xui_url: e.target.value })}
                placeholder="http://127.0.0.1:2053"
                className="w-full px-3.5 py-2.5 bg-neutral-950 border border-neutral-800 rounded-xl text-xs font-mono text-neutral-200 focus:outline-none focus:border-cyan-500/60 transition-colors"
                required
              />
              <p className="text-[11px] text-neutral-500 mt-1">
                {isRtl ? 'آدرس محلی یا دامنه سرور با پورت 3X-UI' : 'Panel URL with port e.g. http://127.0.0.1:2053'}
              </p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-neutral-200 mb-1.5">
                {isRtl ? 'آی‌پی یا دامنه عمومی سرور VPN:' : 'Public VPN Server IP / Domain:'}
              </label>
              <input
                type="text"
                value={formData.vpn_server_host}
                onChange={e => setFormData({ ...formData, vpn_server_host: e.target.value })}
                placeholder="185.190.140.25"
                className="w-full px-3.5 py-2.5 bg-neutral-950 border border-neutral-800 rounded-xl text-xs font-mono text-neutral-200 focus:outline-none focus:border-cyan-500/60 transition-colors"
                required
              />
              <p className="text-[11px] text-neutral-500 mt-1">
                {isRtl ? 'این آدرس در کانفیگ‌های تولیدی کاربران قرار می‌گیرد.' : 'Host placed inside generated vless:// client links'}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
            <div>
              <label className="block text-xs font-semibold text-neutral-200 mb-1.5">
                {isRtl ? 'نام کاربری پنل 3X-UI:' : '3X-UI Admin Username:'}
              </label>
              <input
                type="text"
                value={formData.xui_username}
                onChange={e => setFormData({ ...formData, xui_username: e.target.value })}
                placeholder="admin"
                className="w-full px-3.5 py-2.5 bg-neutral-950 border border-neutral-800 rounded-xl text-xs text-neutral-200 focus:outline-none focus:border-cyan-500/60 transition-colors"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-neutral-200 mb-1.5">
                {isRtl ? 'کلمه عبور پنل 3X-UI:' : '3X-UI Admin Password:'}
              </label>
              <input
                type="password"
                value={formData.xui_password}
                onChange={e => setFormData({ ...formData, xui_password: e.target.value })}
                placeholder="••••••••••••"
                className="w-full px-3.5 py-2.5 bg-neutral-950 border border-neutral-800 rounded-xl text-xs font-mono text-neutral-200 focus:outline-none focus:border-cyan-500/60 transition-colors"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
            <div>
              <label className="block text-xs font-semibold text-neutral-200 mb-1.5">
                {isRtl ? 'شناسه اینباند پیش‌فرض (Inbound ID):' : 'Default Inbound ID:'}
              </label>
              <input
                type="number"
                value={formData.xui_default_inbound}
                onChange={e => setFormData({ ...formData, xui_default_inbound: parseInt(e.target.value) || 1 })}
                className="w-full px-3.5 py-2.5 bg-neutral-950 border border-neutral-800 rounded-xl text-xs font-mono text-neutral-200 focus:outline-none focus:border-cyan-500/60 transition-colors"
              />
              <p className="text-[11px] text-neutral-500 mt-1">
                {isRtl ? 'شناسه عددی اینباندی که کانفیگ‌ها در آن ایجاد می‌شوند.' : 'Target inbound for auto client provisioning'}
              </p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-neutral-200 mb-1.5">
                {isRtl ? 'تایم‌اوت ارتباط (ثانیه):' : 'Request Timeout (seconds):'}
              </label>
              <input
                type="number"
                value={formData.xui_timeout}
                onChange={e => setFormData({ ...formData, xui_timeout: parseInt(e.target.value) || 10 })}
                className="w-full px-3.5 py-2.5 bg-neutral-950 border border-neutral-800 rounded-xl text-xs font-mono text-neutral-200 focus:outline-none focus:border-cyan-500/60 transition-colors"
              />
            </div>
          </div>

          {/* TLS Verify Toggle */}
          <div className="pt-3 border-t border-neutral-800/80 flex items-center justify-between">
            <div>
              <div className="text-xs font-semibold text-neutral-200 flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
                <span>{isRtl ? 'بررسی گواهینامه امنیتی SSL/TLS' : 'Verify SSL/TLS Certificate'}</span>
              </div>
              <div className="text-[11px] text-neutral-400">
                {isRtl ? 'اگر از SSL خودامضا (Self-Signed) یا IP استفاده می‌کنید، این گزینه را خاموش نگه دارید.' : 'Disable if using self-signed cert or plain IP'}
              </div>
            </div>
            <button
              type="button"
              onClick={() => setFormData({ ...formData, xui_tls_verify: !formData.xui_tls_verify })}
              className={`w-11 h-6 flex items-center rounded-full p-1 transition-colors ${
                formData.xui_tls_verify ? 'bg-cyan-600 justify-end' : 'bg-neutral-800 justify-start'
              }`}
            >
              <div className="bg-white w-4 h-4 rounded-full shadow-md" />
            </button>
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 py-2.5 px-6 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold rounded-xl transition-all shadow-lg shadow-cyan-950/50 active:scale-[0.98]"
          >
            <Save className="w-4 h-4" />
            <span>{saving ? (isRtl ? 'در حال ذخیره‌سازی...' : 'Saving...') : (isRtl ? 'ذخیره تنظیمات 3X-UI' : 'Save 3X-UI Settings')}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
