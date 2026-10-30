import React, { useState } from 'react';
import {
  Wifi, Copy, Check, QrCode, Power, Trash2, RefreshCw, ExternalLink, ShieldCheck
} from 'lucide-react';
import { ServiceItem } from '../../types';

interface ServicesTabProps {
  services: ServiceItem[];
  onToggleService: (serviceId: number) => Promise<void>;
  onDeleteService: (serviceId: number) => Promise<void>;
  onOpenQR: (configLink: string, title?: string) => void;
  onSyncTraffic: () => void;
  isSyncing: boolean;
  isRtl: boolean;
}

export const ServicesTab: React.FC<ServicesTabProps> = ({
  services,
  onToggleService,
  onDeleteService,
  onOpenQR,
  onSyncTraffic,
  isSyncing,
  isRtl
}) => {
  const [copiedId, setCopiedId] = useState<number | null>(null);

  const handleCopyLink = (serviceId: number, link: string) => {
    navigator.clipboard.writeText(link);
    setCopiedId(serviceId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-neutral-800">
        <div>
          <h1 className="text-lg font-bold text-neutral-100 flex items-center gap-2">
            <Wifi className="w-5 h-5 text-cyan-400" />
            <span>{isRtl ? 'مدیریت سرویس‌ها و کانفیگ‌ها (Services Manager)' : 'Services & VPN Clients'}</span>
          </h1>
          <p className="text-xs text-neutral-400 mt-0.5">
            {isRtl
              ? 'لیست کامل کلاینت‌های فعال و منقضی در 3X-UI، نمایش مصرف ترافیک و لینک‌های ساب'
              : 'Monitor real client traffic, generate QR codes, toggle, or revoke VPN subscriptions'}
          </p>
        </div>

        <button
          onClick={onSyncTraffic}
          disabled={isSyncing}
          className="flex items-center gap-2 py-2 px-4 bg-neutral-800 hover:bg-neutral-700 text-neutral-200 text-xs font-semibold rounded-xl transition-all border border-neutral-700/60"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-cyan-400 ${isSyncing ? 'animate-spin' : ''}`} />
          <span>{isRtl ? 'سینک زنده ترافیک 3X-UI' : 'Sync 3X-UI Stats'}</span>
        </button>
      </div>

      {/* Services Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {services.map(s => {
          const usedGb = (s.used_traffic_bytes / (1024 ** 3)).toFixed(2);
          const totalGb = (s.total_traffic_bytes / (1024 ** 3)).toFixed(1);
          const percentage = Math.min(100, Math.round((s.used_traffic_bytes / s.total_traffic_bytes) * 100)) || 0;
          const expireDate = new Date(s.expire_time_ms).toLocaleDateString('fa-IR');
          const isExpired = Date.now() > s.expire_time_ms || s.used_traffic_bytes >= s.total_traffic_bytes;

          return (
            <div
              key={s.id}
              className={`bg-neutral-900/60 border rounded-2xl p-5 space-y-4 transition-colors ${
                s.is_active && !isExpired ? 'border-neutral-800/80 hover:border-neutral-700' : 'border-rose-900/40 bg-neutral-950/80'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs px-2 py-0.5 rounded bg-neutral-950 text-cyan-400 border border-neutral-800">
                      #{s.id}
                    </span>
                    <span className="text-xs font-semibold text-neutral-200 font-mono">{s.client_email}</span>
                  </div>
                  <div className="text-[11px] text-neutral-400 mt-1 font-mono">
                    Telegram ID: <span className="text-neutral-200 font-bold">{s.telegram_id}</span>
                  </div>
                </div>

                <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${
                  s.is_active && !isExpired
                    ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/40'
                    : 'bg-rose-950/60 text-rose-400 border border-rose-800/40'
                }`}>
                  {s.is_active && !isExpired ? (isRtl ? 'اتصال برقرار' : 'Active') : (isRtl ? 'منقضی / مسدود' : 'Expired / Inactive')}
                </span>
              </div>

              {/* Traffic Progress */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-xs text-neutral-400">
                  <span>{isRtl ? 'حجم مصرف‌شده:' : 'Traffic Used:'}</span>
                  <span className="font-mono tabular-nums text-neutral-200 font-medium">
                    {usedGb} / {totalGb} GB <span className="text-neutral-500">({percentage}%)</span>
                  </span>
                </div>
                <div className="h-2 w-full bg-neutral-950 rounded-full overflow-hidden border border-neutral-800/80">
                  <div
                    className={`h-full transition-all duration-300 ${
                      percentage >= 90 ? 'bg-rose-500' : percentage >= 75 ? 'bg-amber-500' : 'bg-cyan-500'
                    }`}
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>

              {/* Expiration & Protocol Info */}
              <div className="flex items-center justify-between text-xs text-neutral-400 pt-2 border-t border-neutral-800/80">
                <div className="flex items-center gap-2">
                  <span className="font-mono uppercase text-[10px] px-1.5 py-0.5 rounded bg-neutral-950 border border-neutral-800 text-neutral-300">
                    {s.protocol}
                  </span>
                  <span>اینباند #{s.inbound_id}</span>
                </div>
                <div className="font-mono text-[11px]">
                  {isRtl ? 'انقضا:' : 'Expires:'} <span className="text-neutral-200">{expireDate}</span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2 pt-2 border-t border-neutral-800/80">
                <button
                  onClick={() => handleCopyLink(s.id, s.config_link)}
                  className="flex-1 flex items-center justify-center gap-1.5 py-2 px-3 bg-neutral-800 hover:bg-neutral-700 text-neutral-200 text-xs font-medium rounded-xl transition-colors border border-neutral-700/60"
                  title="کپی کانفیگ VLESS"
                >
                  {copiedId === s.id ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                      <span>{isRtl ? 'کپی شد' : 'Copied'}</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>{isRtl ? 'کپی کانفیگ' : 'Copy'}</span>
                    </>
                  )}
                </button>

                <button
                  onClick={() => onOpenQR(s.config_link, `کانفیگ ${s.client_email}`)}
                  className="p-2 bg-neutral-800 hover:bg-neutral-700 text-cyan-400 rounded-xl transition-colors border border-neutral-700/60"
                  title="نمایش بارکد QR جهت اسکن در موبایل"
                >
                  <QrCode className="w-4 h-4" />
                </button>

                <button
                  onClick={() => onToggleService(s.id)}
                  className={`p-2 rounded-xl border transition-colors ${
                    s.is_active
                      ? 'bg-neutral-800 border-neutral-700/60 text-neutral-300 hover:text-amber-400'
                      : 'bg-emerald-950 border-emerald-800/60 text-emerald-400'
                  }`}
                  title={s.is_active ? 'غیرفعال‌سازی در 3X-UI' : 'فعال‌سازی مجدد'}
                >
                  <Power className="w-4 h-4" />
                </button>

                <button
                  onClick={() => onDeleteService(s.id)}
                  className="p-2 bg-neutral-800 hover:bg-rose-950 text-neutral-400 hover:text-rose-400 border border-neutral-700/60 rounded-xl transition-colors"
                  title="حذف کامل از 3X-UI و دیتابیس"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
