import React, { useState } from 'react';
import { Receipt, CheckCircle2, XCircle, Clock, ShieldCheck, ArrowDownLeft, ArrowUpRight } from 'lucide-react';
import { PaymentItem, TransactionItem } from '../../types';

interface TransactionsTabProps {
  payments: PaymentItem[];
  transactions: TransactionItem[];
  onReviewPayment: (paymentId: number, action: 'approve' | 'reject', adminNote?: string) => Promise<void>;
  currency: string;
  isRtl: boolean;
}

export const TransactionsTab: React.FC<TransactionsTabProps> = ({
  payments,
  transactions,
  onReviewPayment,
  currency,
  isRtl
}) => {
  const [activeSubTab, setActiveSubTab] = useState<'pending' | 'all_payments' | 'transactions'>('pending');
  const [processingId, setProcessingId] = useState<number | null>(null);

  const pendingPayments = payments.filter(p => p.status === 'pending');

  const handleReview = async (paymentId: number, action: 'approve' | 'reject') => {
    setProcessingId(paymentId);
    await onReviewPayment(paymentId, action);
    setProcessingId(null);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-neutral-800">
        <div>
          <h1 className="text-lg font-bold text-neutral-100 flex items-center gap-2">
            <Receipt className="w-5 h-5 text-cyan-400" />
            <span>{isRtl ? 'بررسی واریزی‌ها و تراکنش‌های مالی' : 'Payments & Transaction Ledger'}</span>
          </h1>
          <p className="text-xs text-neutral-400 mt-0.5">
            {isRtl
              ? 'تایید یا رد فیش‌های کارت‌به‌کارت با شارژ خودکار کیف پول کاربر و دفترکل تراکنش‌ها'
              : 'Review customer transfer receipts, approve with auto-credit, and audit transactions'}
          </p>
        </div>

        {/* Sub-tab segmented control */}
        <div className="flex items-center gap-1 p-1 bg-neutral-900 border border-neutral-800 rounded-xl text-xs font-medium">
          <button
            onClick={() => setActiveSubTab('pending')}
            className={`py-1.5 px-3 rounded-lg transition-colors flex items-center gap-1.5 ${
              activeSubTab === 'pending'
                ? 'bg-neutral-800 text-cyan-400 shadow-sm'
                : 'text-neutral-400 hover:text-neutral-200'
            }`}
          >
            <span>{isRtl ? 'در انتظار تایید' : 'Pending'}</span>
            {pendingPayments.length > 0 && (
              <span className="w-4 h-4 rounded-full bg-amber-500 text-neutral-950 font-bold text-[10px] flex items-center justify-center">
                {pendingPayments.length}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveSubTab('all_payments')}
            className={`py-1.5 px-3 rounded-lg transition-colors ${
              activeSubTab === 'all_payments'
                ? 'bg-neutral-800 text-cyan-400 shadow-sm'
                : 'text-neutral-400 hover:text-neutral-200'
            }`}
          >
            {isRtl ? 'تمام فیش‌ها' : 'All Payments'}
          </button>
          <button
            onClick={() => setActiveSubTab('transactions')}
            className={`py-1.5 px-3 rounded-lg transition-colors ${
              activeSubTab === 'transactions'
                ? 'bg-neutral-800 text-cyan-400 shadow-sm'
                : 'text-neutral-400 hover:text-neutral-200'
            }`}
          >
            {isRtl ? 'ریز تراکنش‌ها' : 'Transactions'}
          </button>
        </div>
      </div>

      {/* Subtab 1: Pending Receipts */}
      {activeSubTab === 'pending' && (
        <div className="space-y-4">
          {pendingPayments.length === 0 ? (
            <div className="p-8 text-center bg-neutral-900/40 border border-neutral-800 rounded-2xl">
              <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2 opacity-80" />
              <div className="text-sm font-semibold text-neutral-200">
                {isRtl ? 'هیچ فیش واریزی در انتظار بررسی نیست' : 'No pending payments!'}
              </div>
              <div className="text-xs text-neutral-500 mt-1">
                {isRtl ? 'تمامی تراکنش‌ها توسط شما بررسی و تایید شده‌اند.' : 'All customer receipts have been processed.'}
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {pendingPayments.map(p => (
                <div
                  key={p.id}
                  className="bg-neutral-900/60 border border-amber-500/30 rounded-2xl p-5 space-y-4"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="text-xs text-neutral-400">فیش شماره #{p.id}</div>
                      <div className="text-sm font-bold text-neutral-100 font-mono mt-0.5">
                        {p.username ? `@${p.username}` : `User ID: ${p.user_id}`}
                      </div>
                    </div>
                    <span className="text-xs font-mono font-bold text-amber-400 bg-amber-950/60 border border-amber-800/40 px-2.5 py-1 rounded-lg">
                      {p.amount.toLocaleString()} {currency}
                    </span>
                  </div>

                  <div className="p-3 bg-neutral-950 border border-neutral-800 rounded-xl text-xs space-y-1.5">
                    <div className="text-neutral-400">
                      شماره پیگیری: <span className="font-mono text-neutral-200">{p.reference_id || 'ندارد'}</span>
                    </div>
                    <div className="text-neutral-300 leading-relaxed font-sans">
                      {p.receipt_note}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 pt-2 border-t border-neutral-800">
                    <button
                      onClick={() => handleReview(p.id, 'approve')}
                      disabled={processingId === p.id}
                      className="flex-1 flex items-center justify-center gap-1.5 py-2.5 px-4 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-xl transition-all shadow-md active:scale-[0.98]"
                    >
                      <CheckCircle2 className="w-4 h-4" />
                      <span>{isRtl ? 'تایید و شارژ کیف پول' : 'Approve & Credit'}</span>
                    </button>
                    <button
                      onClick={() => handleReview(p.id, 'reject')}
                      disabled={processingId === p.id}
                      className="py-2.5 px-4 bg-neutral-800 hover:bg-rose-950 text-neutral-300 hover:text-rose-400 text-xs font-medium rounded-xl transition-colors"
                    >
                      {isRtl ? 'رد فیش' : 'Reject'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Subtab 2: All Payments */}
      {activeSubTab === 'all_payments' && (
        <div className="bg-neutral-900/60 border border-neutral-800/80 rounded-2xl overflow-hidden">
          <div className="divide-y divide-neutral-800/60">
            {payments.map(p => (
              <div key={p.id} className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-neutral-400">#{p.id}</span>
                    <span className="font-semibold text-neutral-200">
                      {p.username ? `@${p.username}` : `کاربر ${p.user_id}`}
                    </span>
                    <span className={`text-[10px] px-2 py-0.5 rounded-full ${
                      p.status === 'approved'
                        ? 'bg-emerald-950 text-emerald-400 border border-emerald-800/40'
                        : p.status === 'rejected'
                        ? 'bg-rose-950 text-rose-400 border border-rose-800/40'
                        : 'bg-amber-950 text-amber-400 border border-amber-800/40'
                    }`}>
                      {p.status === 'approved' ? 'تایید شده' : p.status === 'rejected' ? 'رد شده' : 'در انتظار'}
                    </span>
                  </div>
                  <div className="text-[11px] text-neutral-400 mt-1 leading-snug">
                    {p.receipt_note}
                  </div>
                </div>
                <div className="text-start sm:text-end font-mono">
                  <div className="font-bold text-cyan-400 tabular-nums">
                    {p.amount.toLocaleString()} {currency}
                  </div>
                  <div className="text-[10px] text-neutral-500 mt-0.5">
                    {new Date(p.created_at).toLocaleDateString('fa-IR')}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Subtab 3: Audit Ledger */}
      {activeSubTab === 'transactions' && (
        <div className="bg-neutral-900/60 border border-neutral-800/80 rounded-2xl overflow-hidden">
          <div className="divide-y divide-neutral-800/60">
            {transactions.map(t => {
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
                        کاربر #{t.user_id} · موجودی پس از تراکنش: {t.balance_after.toLocaleString()} {currency}
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
      )}
    </div>
  );
};
