import React from 'react';
import { Network, CheckCircle2, ShieldCheck, RefreshCw } from 'lucide-react';
import { InboundItem } from '../../types';

interface InboundsTabProps {
  inbounds: InboundItem[];
  onRefresh: () => void;
  isRtl: boolean;
}

export const InboundsTab: React.FC<InboundsTabProps> = ({ inbounds, onRefresh, isRtl }) => {
  const [refreshing, setRefreshing] = React.useState(false);

  const handleRefreshClick = async () => {
    setRefreshing(true);
    try {
      await onRefresh();
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-neutral-800">
        <div>
          <h1 className="text-lg font-bold text-neutral-100 flex items-center gap-2">
            <Network className="w-5 h-5 text-cyan-400" />
            <span>{isRtl ? 'مدیریت اینباندهای 3X-UI (Inbound Manager)' : 'Inbound Manager'}</span>
          </h1>
          <p className="text-xs text-neutral-400 mt-0.5">
            {isRtl
              ? 'لیست اینباندهای فعال خوانده‌شده از پنل 3X-UI با پروتکل‌های VLESS Reality، VMess و Trojan'
              : 'Active inbounds detected from 3X-UI panel'}
          </p>
        </div>

        <button
          onClick={handleRefreshClick}
          disabled={refreshing}
          className="flex items-center gap-2 py-2 px-4 bg-neutral-800 hover:bg-neutral-700 text-neutral-200 text-xs font-semibold rounded-xl transition-all border border-neutral-700/60"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-cyan-400 ${refreshing ? 'animate-spin' : ''}`} />
          <span>{refreshing ? (isRtl ? 'در حال دریافت...' : 'Refreshing...') : (isRtl ? 'بروزرسانی اینباندها' : 'Refresh Inbounds')}</span>
        </button>
      </div>

      {/* Inbound Cards Grid */}
      {inbounds.length === 0 ? (
        <div className="bg-neutral-900/60 border border-neutral-800/80 rounded-2xl p-8 text-center space-y-3">
          <div className="w-12 h-12 rounded-2xl bg-cyan-950/40 border border-cyan-800/30 flex items-center justify-center mx-auto text-cyan-400">
            <Network className="w-6 h-6" />
          </div>
          <div className="text-sm font-bold text-neutral-200">
            {isRtl ? 'هیچ اینباندی از پنل 3X-UI دریافت نشد' : 'No Inbounds Found'}
          </div>
          <p className="text-xs text-neutral-400 max-w-md mx-auto leading-relaxed">
            {isRtl
              ? 'برای نمایش اینباندها، لطفاً ابتدا در منوی «اتصال به 3X-UI» آدرس پنل (مثلاً http://SERVER_IP:2053) و نام کاربری/رمز عبور ادمین را وارد نموده و دکمه ذخیره و تست را بزنید.'
              : 'Please ensure 3X-UI panel credentials (URL, port, username, password) are properly configured in the 3X-UI Connection tab.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {inbounds.map(ib => (
            <div
              key={ib.id}
              className="bg-neutral-900/60 border border-neutral-800/80 rounded-2xl p-5 space-y-3.5 hover:border-neutral-700 transition-colors"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs px-2 py-0.5 rounded bg-cyan-950/60 text-cyan-400 border border-cyan-800/40">
                      ID #{ib.inbound_id}
                    </span>
                    <span className="text-xs font-semibold text-neutral-200">{ib.remark}</span>
                  </div>
                  {ib.reality_sni && (
                    <div className="text-[11px] text-neutral-400 font-mono mt-1">
                      SNI: <span className="text-neutral-300">{ib.reality_sni}</span>
                    </div>
                  )}
                </div>

                <span className={`text-[11px] font-medium flex items-center gap-1 ${
                  ib.is_enabled ? 'text-emerald-400' : 'text-neutral-500'
                }`}>
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  {ib.is_enabled ? (isRtl ? 'فعال' : 'Active') : (isRtl ? 'غیرفعال' : 'Disabled')}
                </span>
              </div>

              <div className="grid grid-cols-4 gap-2 pt-2 border-t border-neutral-800 text-center">
                <div className="p-2 rounded-xl bg-neutral-950 border border-neutral-800/60">
                  <div className="text-[10px] text-neutral-500">{isRtl ? 'پروتکل' : 'Protocol'}</div>
                  <div className="text-xs font-mono font-semibold uppercase text-cyan-400 mt-0.5">{ib.protocol}</div>
                </div>
                <div className="p-2 rounded-xl bg-neutral-950 border border-neutral-800/60">
                  <div className="text-[10px] text-neutral-500">{isRtl ? 'پورت' : 'Port'}</div>
                  <div className="text-xs font-mono font-semibold text-neutral-200 mt-0.5">{ib.port}</div>
                </div>
                <div className="p-2 rounded-xl bg-neutral-950 border border-neutral-800/60">
                  <div className="text-[10px] text-neutral-500">{isRtl ? 'شبکه' : 'Network'}</div>
                  <div className="text-xs font-mono font-semibold text-neutral-200 mt-0.5">{ib.network}</div>
                </div>
                <div className="p-2 rounded-xl bg-neutral-950 border border-neutral-800/60">
                  <div className="text-[10px] text-neutral-500">{isRtl ? 'امنیت' : 'Security'}</div>
                  <div className="text-xs font-mono font-semibold text-amber-400 mt-0.5">{ib.security}</div>
                </div>
              </div>

              <div className="flex items-center justify-between text-xs text-neutral-400 pt-1">
                <span>{isRtl ? 'تعداد کلاینت‌های متصل:' : 'Connected Clients:'}</span>
                <span className="font-mono text-neutral-200 font-semibold">{ib.total_clients} {isRtl ? 'کاربر' : 'clients'}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
