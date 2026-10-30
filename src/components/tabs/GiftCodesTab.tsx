import React, { useState } from 'react';
import { Gift, Plus, Trash2, Sparkles, X, CheckCircle2 } from 'lucide-react';
import { GiftCodeItem } from '../../types';

interface GiftCodesTabProps {
  giftCodes: GiftCodeItem[];
  onCreateGiftCode: (gift: Partial<GiftCodeItem>) => Promise<void>;
  onDeleteGiftCode: (giftId: number) => Promise<void>;
  currency: string;
  isRtl: boolean;
}

export const GiftCodesTab: React.FC<GiftCodesTabProps> = ({
  giftCodes,
  onCreateGiftCode,
  onDeleteGiftCode,
  currency,
  isRtl
}) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [formData, setFormData] = useState({
    code: '',
    amount: 50000,
    max_redemptions: 20,
    expire_days: 30
  });
  const [submitting, setSubmitting] = useState(false);

  const generateRandomCode = () => {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    let res = 'GIFT-';
    for (let i = 0; i < 6; i++) {
      res += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    setFormData({ ...formData, code: res });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    await onCreateGiftCode(formData);
    setSubmitting(false);
    setModalOpen(false);
    setFormData({ code: '', amount: 50000, max_redemptions: 20, expire_days: 30 });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-neutral-800">
        <div>
          <h1 className="text-lg font-bold text-neutral-100 flex items-center gap-2">
            <Gift className="w-5 h-5 text-cyan-400" />
            <span>{isRtl ? 'مدیریت کدهای هدیه (Gift Codes)' : 'Gift Codes Manager'}</span>
          </h1>
          <p className="text-xs text-neutral-400 mt-0.5">
            {isRtl
              ? 'تولید کدهای تخفیف و شارژ هدیه کیف پول جهت بازاریابی و جذب مشتریان در کانال تلگرام'
              : 'Create promo codes and wallet vouchers with single-claim rules'}
          </p>
        </div>

        <button
          onClick={() => {
            generateRandomCode();
            setModalOpen(true);
          }}
          className="flex items-center gap-2 py-2 px-4 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold rounded-xl transition-all shadow-md active:scale-[0.98]"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>{isRtl ? 'ایجاد کد هدیه جدید' : 'New Gift Code'}</span>
        </button>
      </div>

      {/* Gift Codes Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {giftCodes.map(g => (
          <div
            key={g.id}
            className="bg-neutral-900/60 border border-neutral-800/80 rounded-2xl p-5 space-y-3.5 hover:border-neutral-700 transition-colors"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="font-mono text-sm font-bold px-3 py-1 rounded-xl bg-neutral-950 text-cyan-400 border border-neutral-800 tracking-wider">
                  {g.code}
                </span>
              </div>
              <button
                onClick={() => onDeleteGiftCode(g.id)}
                className="p-1.5 text-neutral-400 hover:text-rose-400 hover:bg-neutral-800 rounded-lg transition-colors"
                title="حذف کد"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs pt-1">
              <div className="p-2.5 rounded-xl bg-neutral-950 border border-neutral-800/60">
                <div className="text-[10px] text-neutral-500">{isRtl ? 'مبلغ اعتبار' : 'Credit Amount'}</div>
                <div className="font-mono font-bold text-emerald-400 mt-0.5">
                  {g.amount.toLocaleString()} {currency}
                </div>
              </div>

              <div className="p-2.5 rounded-xl bg-neutral-950 border border-neutral-800/60">
                <div className="text-[10px] text-neutral-500">{isRtl ? 'ظرفیت استفاده' : 'Redemptions'}</div>
                <div className="font-mono font-bold text-neutral-200 mt-0.5">
                  {g.redeemed_count} / {g.max_redemptions} {isRtl ? 'نفر' : 'uses'}
                </div>
              </div>
            </div>

            <div className="text-[11px] text-neutral-500 flex items-center justify-between pt-1 border-t border-neutral-800/60">
              <span>{isRtl ? 'مهلت اعتبار:' : 'Expires:'}</span>
              <span className="font-mono text-neutral-400">
                {g.expire_at ? new Date(g.expire_at).toLocaleDateString('fa-IR') : (isRtl ? 'همیشگی' : 'No Expiry')}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Create Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in">
          <div
            className="w-full max-w-sm bg-neutral-900 border border-neutral-800 rounded-2xl p-5 shadow-2xl relative text-neutral-100"
            dir={isRtl ? 'rtl' : 'ltr'}
          >
            <div className="flex items-center justify-between pb-3 border-b border-neutral-800 mb-4">
              <h3 className="text-sm font-bold text-neutral-100">
                {isRtl ? 'ایجاد کد هدیه جدید' : 'Create Gift Voucher'}
              </h3>
              <button
                onClick={() => setModalOpen(false)}
                className="p-1 text-neutral-400 hover:text-neutral-200 rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4 text-xs">
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="font-semibold text-neutral-300">
                    {isRtl ? 'متن کد:' : 'Voucher Code:'}
                  </label>
                  <button
                    type="button"
                    onClick={generateRandomCode}
                    className="text-[11px] text-cyan-400 hover:underline flex items-center gap-1"
                  >
                    <Sparkles className="w-3 h-3" />
                    <span>{isRtl ? 'تولید رندوم' : 'Randomize'}</span>
                  </button>
                </div>
                <input
                  type="text"
                  value={formData.code}
                  onChange={e => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                  className="w-full px-3 py-2 bg-neutral-950 border border-neutral-800 rounded-xl font-mono uppercase text-neutral-200 focus:outline-none focus:border-cyan-500/60"
                  required
                />
              </div>

              <div>
                <label className="block font-semibold text-neutral-300 mb-1">
                  {isRtl ? `مبلغ شارژ (${currency}):` : `Credit Amount (${currency}):`}
                </label>
                <input
                  type="number"
                  value={formData.amount}
                  onChange={e => setFormData({ ...formData, amount: parseInt(e.target.value) || 0 })}
                  className="w-full px-3 py-2 bg-neutral-950 border border-neutral-800 rounded-xl font-mono text-neutral-200 focus:outline-none focus:border-cyan-500/60"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-neutral-300 mb-1">
                    {isRtl ? 'تعداد قابل استفاده:' : 'Max Redemptions:'}
                  </label>
                  <input
                    type="number"
                    value={formData.max_redemptions}
                    onChange={e => setFormData({ ...formData, max_redemptions: parseInt(e.target.value) || 1 })}
                    className="w-full px-3 py-2 bg-neutral-950 border border-neutral-800 rounded-xl font-mono text-neutral-200 focus:outline-none focus:border-cyan-500/60"
                    required
                  />
                </div>

                <div>
                  <label className="block font-semibold text-neutral-300 mb-1">
                    {isRtl ? 'اعتبار (روز):' : 'Expires in (Days):'}
                  </label>
                  <input
                    type="number"
                    value={formData.expire_days}
                    onChange={e => setFormData({ ...formData, expire_days: parseInt(e.target.value) || 30 })}
                    className="w-full px-3 py-2 bg-neutral-950 border border-neutral-800 rounded-xl font-mono text-neutral-200 focus:outline-none focus:border-cyan-500/60"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-neutral-800">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="py-2 px-4 rounded-xl bg-neutral-800 hover:bg-neutral-700 text-neutral-300 text-xs"
                >
                  {isRtl ? 'انصراف' : 'Cancel'}
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="py-2 px-5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs"
                >
                  {submitting ? (isRtl ? 'در حال ثبت...' : 'Saving...') : (isRtl ? 'ایجاد کد هدیه' : 'Create Voucher')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
