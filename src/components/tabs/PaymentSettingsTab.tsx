import React, { useState } from 'react';
import { CreditCard, Save, Info } from 'lucide-react';
import { AppSettings } from '../../types';

interface PaymentSettingsTabProps {
  settings: AppSettings;
  onSave: (updated: Partial<AppSettings>) => Promise<void>;
  isRtl: boolean;
}

export const PaymentSettingsTab: React.FC<PaymentSettingsTabProps> = ({
  settings,
  onSave,
  isRtl
}) => {
  const [formData, setFormData] = useState<Partial<AppSettings>>({
    card_number: settings.card_number || '6037-9975-4321-8765',
    card_holder: settings.card_holder || 'محمد رضایی',
    crypto_wallet: settings.crypto_wallet || '',
    payment_instructions: settings.payment_instructions || '',
    currency: settings.currency || 'تومان'
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
          <CreditCard className="w-5 h-5 text-cyan-400" />
          <span>{isRtl ? 'تنظیمات درگاه و پرداخت کارت‌به‌کارت' : 'Payment Methods & Gateway Settings'}</span>
        </h1>
        <p className="text-xs text-neutral-400 mt-0.5">
          {isRtl
            ? 'شماره کارت مقصد، نام صاحب حساب، ولت کریپتو و متن راهنمای واریزی نمایش داده‌شده در ربات'
            : 'Configure card-to-card details, crypto addresses, and payment instructions'}
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="bg-neutral-900/60 border border-neutral-800/80 rounded-2xl p-5 space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-neutral-200 mb-1.5">
                {isRtl ? 'شماره کارت بانکی مقصد:' : 'Bank Card Number:'}
              </label>
              <input
                type="text"
                value={formData.card_number}
                onChange={e => setFormData({ ...formData, card_number: e.target.value })}
                placeholder="6037-9975-..."
                className="w-full px-3.5 py-2.5 bg-neutral-950 border border-neutral-800 rounded-xl text-xs font-mono text-neutral-200 focus:outline-none focus:border-cyan-500/60 transition-colors"
                required
              />
              <p className="text-[11px] text-neutral-500 mt-1">
                {isRtl ? 'شماره کارتی که به کاربر تلگرام جهت واریز وجه نمایش داده می‌شود' : 'Card number displayed to users'}
              </p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-neutral-200 mb-1.5">
                {isRtl ? 'نام و نام خانوادگی صاحب کارت:' : 'Card Holder Name:'}
              </label>
              <input
                type="text"
                value={formData.card_holder}
                onChange={e => setFormData({ ...formData, card_holder: e.target.value })}
                placeholder="نام صاحب حساب"
                className="w-full px-3.5 py-2.5 bg-neutral-950 border border-neutral-800 rounded-xl text-xs text-neutral-200 focus:outline-none focus:border-cyan-500/60 transition-colors"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
            <div>
              <label className="block text-xs font-semibold text-neutral-200 mb-1.5">
                {isRtl ? 'آدرس کیف پول رمزارز / تتر (اختیاری):' : 'Crypto / USDT Wallet Address:'}
              </label>
              <input
                type="text"
                value={formData.crypto_wallet}
                onChange={e => setFormData({ ...formData, crypto_wallet: e.target.value })}
                placeholder="USDT (TRC20): T..."
                className="w-full px-3.5 py-2.5 bg-neutral-950 border border-neutral-800 rounded-xl text-xs font-mono text-neutral-200 focus:outline-none focus:border-cyan-500/60 transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-neutral-200 mb-1.5">
                {isRtl ? 'واحد پولی سامانه:' : 'Currency Label:'}
              </label>
              <input
                type="text"
                value={formData.currency}
                onChange={e => setFormData({ ...formData, currency: e.target.value })}
                placeholder="تومان"
                className="w-full px-3.5 py-2.5 bg-neutral-950 border border-neutral-800 rounded-xl text-xs text-neutral-200 focus:outline-none focus:border-cyan-500/60 transition-colors"
                required
              />
            </div>
          </div>

          <div className="pt-2">
            <label className="block text-xs font-semibold text-neutral-200 mb-1.5">
              {isRtl ? 'متن راهنما و قوانین پرداخت:' : 'Payment Instructions:'}
            </label>
            <textarea
              rows={4}
              value={formData.payment_instructions}
              onChange={e => setFormData({ ...formData, payment_instructions: e.target.value })}
              className="w-full px-3.5 py-2.5 bg-neutral-950 border border-neutral-800 rounded-xl text-xs text-neutral-200 focus:outline-none focus:border-cyan-500/60 transition-colors"
            />
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 py-2.5 px-6 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold rounded-xl transition-all shadow-lg shadow-cyan-950/50 active:scale-[0.98]"
          >
            <Save className="w-4 h-4" />
            <span>{saving ? (isRtl ? 'در حال ذخیره‌سازی...' : 'Saving...') : (isRtl ? 'ذخیره مشخصات پرداخت' : 'Save Payment Info')}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
