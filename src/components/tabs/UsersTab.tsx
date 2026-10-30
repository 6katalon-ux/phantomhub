import React, { useState } from 'react';
import { Users, Search, PlusCircle, MinusCircle, Ban, CheckCircle2, RotateCcw, X, ShieldAlert } from 'lucide-react';
import { UserItem } from '../../types';

interface UsersTabProps {
  users: UserItem[];
  onAdjustBalance: (userId: number, amount: number, description: string) => Promise<void>;
  onToggleBlock: (userId: number) => Promise<void>;
  onResetTrial: (userId: number) => Promise<void>;
  currency: string;
  isRtl: boolean;
}

export const UsersTab: React.FC<UsersTabProps> = ({
  users,
  onAdjustBalance,
  onToggleBlock,
  onResetTrial,
  currency,
  isRtl
}) => {
  const [search, setSearch] = useState('');
  const [selectedUser, setSelectedUser] = useState<UserItem | null>(null);
  const [adjustAmount, setAdjustAmount] = useState<number>(50000);
  const [adjustType, setAdjustType] = useState<'add' | 'deduct'>('add');
  const [adjustDesc, setAdjustDesc] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const filteredUsers = users.filter(u =>
    u.username?.toLowerCase().includes(search.toLowerCase()) ||
    u.first_name?.toLowerCase().includes(search.toLowerCase()) ||
    u.telegram_id.toString().includes(search)
  );

  const handleAdjustSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUser) return;
    setSubmitting(true);
    const finalAmount = adjustType === 'add' ? Math.abs(adjustAmount) : -Math.abs(adjustAmount);
    await onAdjustBalance(selectedUser.id, finalAmount, adjustDesc);
    setSubmitting(false);
    setSelectedUser(null);
    setAdjustDesc('');
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-neutral-800">
        <div>
          <h1 className="text-lg font-bold text-neutral-100 flex items-center gap-2">
            <Users className="w-5 h-5 text-cyan-400" />
            <span>{isRtl ? 'مدیریت کاربران (Users Manager)' : 'Users Manager'}</span>
          </h1>
          <p className="text-xs text-neutral-400 mt-0.5">
            {isRtl
              ? 'جستجوی اعضای ثبت‌نامی تلگرام، تغییر موجودی کیف پول، مسدودسازی و ریست تست رایگان'
              : 'Search registered members, adjust balances, toggle block status, and manage trials'}
          </p>
        </div>

        {/* Search Bar */}
        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 absolute top-3 right-3 text-neutral-500" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder={isRtl ? 'جستجو نام، آیدی عددی...' : 'Search username, ID...'}
            className="w-full pl-3 pr-9 py-2 bg-neutral-900 border border-neutral-800 rounded-xl text-xs text-neutral-200 placeholder-neutral-500 focus:outline-none focus:border-cyan-500/60"
          />
        </div>
      </div>

      {/* Users Desktop Table / Mobile Card View */}
      <div className="bg-neutral-900/60 border border-neutral-800/80 rounded-2xl overflow-hidden">
        {/* Desktop Table View */}
        <div className="hidden lg:block overflow-x-auto">
          <table className="w-full text-right text-xs">
            <thead className="bg-neutral-950/80 text-neutral-400 border-b border-neutral-800 font-medium">
              <tr>
                <th className="py-3 px-4">کاربر</th>
                <th className="py-3 px-4">آیدی عددی تلگرام</th>
                <th className="py-3 px-4">موجودی کیف پول</th>
                <th className="py-3 px-4">سرویس‌ها</th>
                <th className="py-3 px-4">تست رایگان</th>
                <th className="py-3 px-4">وضعیت</th>
                <th className="py-3 px-4 text-center">عملیات</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-neutral-800/60 text-neutral-300">
              {filteredUsers.map(u => (
                <tr key={u.id} className="hover:bg-neutral-800/30 transition-colors">
                  <td className="py-3 px-4">
                    <div className="font-semibold text-neutral-100">{u.first_name} {u.last_name}</div>
                    <div className="text-[11px] text-neutral-500 font-mono">@{u.username || 'بدون_یوزرنیم'}</div>
                  </td>
                  <td className="py-3 px-4 font-mono tabular-nums text-neutral-300">{u.telegram_id}</td>
                  <td className="py-3 px-4 font-mono font-bold tabular-nums text-cyan-400">
                    {u.wallet_balance.toLocaleString()} {currency}
                  </td>
                  <td className="py-3 px-4 font-mono tabular-nums">{u.services_count || 0} عدد</td>
                  <td className="py-3 px-4">
                    <span className={`text-[11px] px-2 py-0.5 rounded-full ${
                      u.trial_used ? 'bg-neutral-800 text-neutral-400' : 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/40'
                    }`}>
                      {u.trial_used ? 'دریافت شده' : 'قابل دریافت'}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`text-[11px] px-2 py-0.5 rounded-full ${
                      u.is_blocked ? 'bg-rose-950/60 text-rose-400 border border-rose-800/40' : 'bg-emerald-950/60 text-emerald-400'
                    }`}>
                      {u.is_blocked ? 'مسدود' : 'فعال'}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center justify-center gap-1.5">
                      <button
                        onClick={() => setSelectedUser(u)}
                        className="py-1 px-2.5 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-cyan-400 hover:text-cyan-300 text-[11px] font-medium transition-colors"
                      >
                        تغییر موجودی
                      </button>
                      <button
                        onClick={() => onResetTrial(u.id)}
                        className="p-1.5 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-neutral-400 hover:text-amber-400 transition-colors"
                        title="ریست واجد شرایط بودن تست رایگان"
                      >
                        <RotateCcw className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => onToggleBlock(u.id)}
                        className={`p-1.5 rounded-lg transition-colors ${
                          u.is_blocked
                            ? 'bg-rose-950 text-rose-400 hover:bg-rose-900'
                            : 'bg-neutral-800 text-neutral-400 hover:text-rose-400'
                        }`}
                        title={u.is_blocked ? 'رفع مسدودی' : 'مسدودسازی کاربر'}
                      >
                        <Ban className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Mobile View: High Density Cards */}
        <div className="lg:hidden divide-y divide-neutral-800/80">
          {filteredUsers.map(u => (
            <div key={u.id} className="p-4 space-y-3">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="text-xs font-bold text-neutral-100">{u.first_name} {u.last_name}</div>
                  <div className="text-[11px] text-neutral-400 font-mono">@{u.username || 'بدون_یوزرنیم'} · ID: {u.telegram_id}</div>
                </div>
                <span className={`text-[10px] px-2 py-0.5 rounded-full ${
                  u.is_blocked ? 'bg-rose-950/60 text-rose-400 border border-rose-800/40' : 'bg-emerald-950/60 text-emerald-400'
                }`}>
                  {u.is_blocked ? 'مسدود' : 'فعال'}
                </span>
              </div>

              <div className="flex items-center justify-between text-xs py-2 px-3 rounded-xl bg-neutral-950 border border-neutral-800/60">
                <span className="text-neutral-400">موجودی کیف پول:</span>
                <span className="font-mono font-bold text-cyan-400 tabular-nums">
                  {u.wallet_balance.toLocaleString()} {currency}
                </span>
              </div>

              <div className="flex items-center gap-2 pt-1">
                <button
                  onClick={() => setSelectedUser(u)}
                  className="flex-1 py-2 px-3 bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-400 text-xs font-semibold rounded-xl border border-cyan-500/30 transition-colors text-center"
                >
                  افزایش / کسر موجودی
                </button>
                <button
                  onClick={() => onResetTrial(u.id)}
                  className="p-2 bg-neutral-800 text-neutral-300 rounded-xl"
                  title="ریست تست"
                >
                  <RotateCcw className="w-4 h-4 text-amber-400" />
                </button>
                <button
                  onClick={() => onToggleBlock(u.id)}
                  className={`p-2 rounded-xl ${
                    u.is_blocked ? 'bg-rose-900 text-rose-200' : 'bg-neutral-800 text-neutral-400'
                  }`}
                  title="مسدودی"
                >
                  <Ban className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Adjust Balance Modal */}
      {selectedUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in">
          <div
            className="w-full max-w-sm bg-neutral-900 border border-neutral-800 rounded-2xl p-5 shadow-2xl relative text-neutral-100"
            dir={isRtl ? 'rtl' : 'ltr'}
          >
            <div className="flex items-center justify-between pb-3 border-b border-neutral-800 mb-4">
              <h3 className="text-sm font-bold text-neutral-100">
                {isRtl ? 'تغییر موجودی کیف پول کاربر' : 'Adjust Wallet Balance'}
              </h3>
              <button
                onClick={() => setSelectedUser(null)}
                className="p-1 text-neutral-400 hover:text-neutral-200 rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="mb-4 text-xs text-neutral-400">
              <div>کاربر: <span className="font-semibold text-neutral-200">{selectedUser.first_name} (@{selectedUser.username})</span></div>
              <div className="mt-1">موجودی فعلی: <span className="font-mono text-cyan-400 font-bold">{selectedUser.wallet_balance.toLocaleString()} {currency}</span></div>
            </div>

            <form onSubmit={handleAdjustSubmit} className="space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setAdjustType('add')}
                  className={`py-2 px-3 rounded-xl font-medium flex items-center justify-center gap-1.5 transition-colors ${
                    adjustType === 'add'
                      ? 'bg-emerald-600 text-white'
                      : 'bg-neutral-950 text-neutral-400 border border-neutral-800'
                  }`}
                >
                  <PlusCircle className="w-3.5 h-3.5" />
                  <span>افزایش موجودی</span>
                </button>
                <button
                  type="button"
                  onClick={() => setAdjustType('deduct')}
                  className={`py-2 px-3 rounded-xl font-medium flex items-center justify-center gap-1.5 transition-colors ${
                    adjustType === 'deduct'
                      ? 'bg-rose-600 text-white'
                      : 'bg-neutral-950 text-neutral-400 border border-neutral-800'
                  }`}
                >
                  <MinusCircle className="w-3.5 h-3.5" />
                  <span>کسر موجودی</span>
                </button>
              </div>

              <div>
                <label className="block font-semibold text-neutral-300 mb-1">
                  مبلغ ({currency}):
                </label>
                <input
                  type="number"
                  value={adjustAmount}
                  onChange={e => setAdjustAmount(parseInt(e.target.value) || 0)}
                  className="w-full px-3 py-2 bg-neutral-950 border border-neutral-800 rounded-xl font-mono text-neutral-200 focus:outline-none focus:border-cyan-500/60"
                  required
                />
              </div>

              <div>
                <label className="block font-semibold text-neutral-300 mb-1">
                  علت تغییر (توضیحات تراکنش):
                </label>
                <input
                  type="text"
                  value={adjustDesc}
                  onChange={e => setAdjustDesc(e.target.value)}
                  placeholder="مثال: شارژ دستی پس از واریز یا جبران قطعی"
                  className="w-full px-3 py-2 bg-neutral-950 border border-neutral-800 rounded-xl text-neutral-200 focus:outline-none focus:border-cyan-500/60"
                  required
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-neutral-800">
                <button
                  type="button"
                  onClick={() => setSelectedUser(null)}
                  className="py-2 px-4 rounded-xl bg-neutral-800 hover:bg-neutral-700 text-neutral-300 text-xs"
                >
                  انصراف
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="py-2 px-5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs"
                >
                  {submitting ? 'در حال ثبت...' : 'ثبت تراکنش'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
