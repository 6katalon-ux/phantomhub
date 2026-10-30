import React from 'react';
import { Wallet, ArrowDownLeft, ArrowUpRight, DollarSign, Users } from 'lucide-react';
import { TransactionItem, UserItem, TabType } from '../../types';

interface WalletTabProps {
  users: UserItem[];
  transactions: TransactionItem[];
  currency: string;
  onSelectTab: (tab: TabType) => void;
  isRtl: boolean;
}

export const WalletTab: React.FC<WalletTabProps> = ({
  users,
  transactions,
  currency,
  onSelectTab,
  isRtl
}) => {
  const totalLiabilities = users.reduce((acc, u) => acc + u.wallet_balance, 0);
  const usersWithBalance = users.filter(u => u.wallet_balance > 0);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-neutral-800">
        <div>
          <h1 className="text-lg font-bold text-neutral-100 flex items-center gap-2">
            <Wallet className="w-5 h-5 text-cyan-400" />
            <span>{isRtl ? 'مدیریت کیف پول و موجودی‌ها' : 'Wallet & Customer Balances'}</span>
          </h1>
          <p className="text-xs text-neutral-400 mt-0.5">
            {isRtl
              ? 'مجموع تعهدات مالی و مانده حساب کاربران، واریزی‌ها و تاریخچه کامل تراکنش‌ها'
              : 'Overview of user wallet liabilities and ledger history'}
          </p>
        </div>

        <button
          onClick={() => onSelectTab('users')}
          className="flex items-center gap-2 py-2 px-4 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold rounded-xl transition-all shadow-md active:scale-[0.98]"
        >
          <Users className="w-3.5 h-3.5" />
          <span>{isRtl ? 'شارژ دستی کاربر در لیست کاربران' : 'Adjust in Users List'}</span>
        </button>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="bg-neutral-900/60 border border-neutral-800/80 rounded-2xl p-5">
          <div className="text-xs text-neutral-400 mb-1">
            {isRtl ? 'مجموع تعهدات کیف پول (موجودی نزد کاربران):' : 'Total User Balances:'}
          </div>
          <div className="text-xl sm:text-2xl font-bold font-mono text-cyan-400 tabular-nums">
            {totalLiabilities.toLocaleString()} <span className="text-xs font-normal text-neutral-400">{currency}</span>
          </div>
          <div className="text-[11px] text-neutral-500 mt-2">
            {usersWithBalance.length} {isRtl ? 'کاربر دارای موجودی مثبت هستند' : 'users hold positive balance'}
          </div>
        </div>

        <div className="bg-neutral-900/60 border border-neutral-800/80 rounded-2xl p-5">
          <div className="text-xs text-neutral-400 mb-1">
            {isRtl ? 'تعداد کل تراکنش‌های ثبت‌شده:' : 'Total Recorded Transactions:'}
          </div>
          <div className="text-xl sm:text-2xl font-bold font-mono text-neutral-100 tabular-nums">
            {transactions.length} <span className="text-xs font-normal text-neutral-400">{isRtl ? 'تراکنش' : 'records'}</span>
          </div>
          <div className="text-[11px] text-neutral-500 mt-2">
            {isRtl ? 'تراکنش‌های خرید، شارژ و استرداد خودکار' : 'Includes purchases, top-ups and refunds'}
          </div>
        </div>
      </div>

      {/* Recent Ledger List */}
      <div className="bg-neutral-900/60 border border-neutral-800/80 rounded-2xl overflow-hidden">
        <div className="p-4 border-b border-neutral-800 font-semibold text-xs text-neutral-200">
          {isRtl ? 'تاریخچه تراکنش‌های اخیر کیف پول:' : 'Recent Wallet Transactions:'}
        </div>
        <div className="divide-y divide-neutral-800/60">
          {transactions.slice(0, 15).map(t => {
            const isCredit = t.amount > 0;
            return (
              <div key={t.id} className="p-4 flex items-center justify-between gap-4 text-xs">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-xl ${isCredit ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'}`}>
                    {isCredit ? <ArrowDownLeft className="w-4 h-4" /> : <ArrowUpRight className="w-4 h-4" />}
                  </div>
                  <div>
                    <div className="font-semibold text-neutral-200">{t.description}</div>
                    <div className="text-[11px] text-neutral-500 mt-0.5 font-mono">
                      کاربر #{t.user_id} · مانده حساب: {t.balance_after.toLocaleString()} {currency}
                    </div>
                  </div>
                </div>
                <div className="text-end font-mono">
                  <div className={`font-bold tabular-nums ${isCredit ? 'text-emerald-400' : 'text-neutral-300'}`}>
                    {isCredit ? '+' : ''}{t.amount.toLocaleString()} {currency}
                  </div>
                  <div className="text-[10px] text-neutral-500 mt-0.5">
                    {new Date(t.created_at).toLocaleDateString('fa-IR')}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
