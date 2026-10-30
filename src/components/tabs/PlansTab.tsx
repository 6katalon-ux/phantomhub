import React, { useState } from 'react';
import { Package, Plus, Edit2, Trash2, CheckCircle2, X } from 'lucide-react';
import { PlanItem, InboundItem } from '../../types';

interface PlansTabProps {
  plans: PlanItem[];
  inbounds: InboundItem[];
  onSavePlan: (plan: Partial<PlanItem>) => Promise<void>;
  onDeletePlan: (planId: number) => Promise<void>;
  currency: string;
  isRtl: boolean;
}

export const PlansTab: React.FC<PlansTabProps> = ({
  plans,
  inbounds,
  onSavePlan,
  onDeletePlan,
  currency,
  isRtl
}) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [editingPlan, setEditingPlan] = useState<Partial<PlanItem> | null>(null);
  const [saving, setSaving] = useState(false);

  const openCreateModal = () => {
    setEditingPlan({
      name: '',
      description: '',
      price: 150000,
      traffic_gb: 40,
      duration_days: 30,
      inbound_id: inbounds[0]?.inbound_id || 1,
      protocol: 'vless',
      max_ips: 2,
      is_active: true,
      sort_order: plans.length + 1
    });
    setModalOpen(true);
  };

  const openEditModal = (plan: PlanItem) => {
    setEditingPlan({ ...plan });
    setModalOpen(true);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingPlan) return;
    setSaving(true);
    await onSavePlan(editingPlan);
    setSaving(false);
    setModalOpen(false);
    setEditingPlan(null);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-neutral-800">
        <div>
          <h1 className="text-lg font-bold text-neutral-100 flex items-center gap-2">
            <Package className="w-5 h-5 text-cyan-400" />
            <span>{isRtl ? 'مدیریت پلن‌های فروش (Plans Manager)' : 'Plans Manager'}</span>
          </h1>
          <p className="text-xs text-neutral-400 mt-0.5">
            {isRtl
              ? 'تعریف پلن‌های اشتراک نامحدود، قیمت‌گذاری، حجم ترافیک و تخصیص اینباند'
              : 'Configure subscription packages, pricing, quotas, and inbound routing'}
          </p>
        </div>

        <button
          onClick={openCreateModal}
          className="flex items-center gap-2 py-2 px-4 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold rounded-xl transition-all shadow-md shadow-cyan-950/40 active:scale-[0.98]"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>{isRtl ? 'افزودن پلن جدید' : 'Create New Plan'}</span>
        </button>
      </div>

      {/* Plans Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {plans.map(p => (
          <div
            key={p.id}
            className="bg-neutral-900/60 border border-neutral-800/80 rounded-2xl p-5 space-y-4 hover:border-neutral-700 transition-colors"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-sm font-bold text-neutral-100">{p.name}</h3>
                <p className="text-xs text-neutral-400 mt-1 leading-relaxed">{p.description}</p>
              </div>
              <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full shrink-0 ${
                p.is_active ? 'bg-emerald-950/60 text-emerald-400 border border-emerald-800/40' : 'bg-neutral-800 text-neutral-500'
              }`}>
                {p.is_active ? (isRtl ? 'فعال در ربات' : 'Active') : (isRtl ? 'غیرفعال' : 'Inactive')}
              </span>
            </div>

            <div className="grid grid-cols-3 gap-2.5 py-3 border-y border-neutral-800/80 text-center">
              <div>
                <div className="text-[10px] text-neutral-500">{isRtl ? 'قیمت' : 'Price'}</div>
                <div className="text-xs font-mono font-bold text-neutral-100 mt-0.5">
                  {p.price.toLocaleString()} <span className="text-[10px] font-normal text-neutral-400">{currency}</span>
                </div>
              </div>
              <div>
                <div className="text-[10px] text-neutral-500">{isRtl ? 'حجم ترافیک' : 'Traffic'}</div>
                <div className="text-xs font-mono font-bold text-cyan-400 mt-0.5">
                  {p.traffic_gb} GB
                </div>
              </div>
              <div>
                <div className="text-[10px] text-neutral-500">{isRtl ? 'مدت اعتبار' : 'Duration'}</div>
                <div className="text-xs font-mono font-bold text-neutral-200 mt-0.5">
                  {p.duration_days} {isRtl ? 'روز' : 'days'}
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between text-xs text-neutral-400">
              <div className="flex items-center gap-2">
                <span className="font-mono text-[11px] uppercase bg-neutral-950 px-2 py-0.5 rounded border border-neutral-800">
                  {p.protocol}
                </span>
                <span>{p.max_ips} {isRtl ? 'کاربر همزمان' : 'devices'}</span>
              </div>

              <div className="flex items-center gap-1.5">
                <button
                  onClick={() => openEditModal(p)}
                  className="p-1.5 text-neutral-400 hover:text-cyan-400 hover:bg-neutral-800 rounded-lg transition-colors"
                  title="ویرایش پلن"
                >
                  <Edit2 className="w-4 h-4" />
                </button>
                <button
                  onClick={() => onDeletePlan(p.id)}
                  className="p-1.5 text-neutral-400 hover:text-rose-400 hover:bg-neutral-800 rounded-lg transition-colors"
                  title="حذف پلن"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Plan Edit / Create Modal */}
      {modalOpen && editingPlan && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in">
          <div
            className="w-full max-w-md bg-neutral-900 border border-neutral-800 rounded-2xl p-5 shadow-2xl relative text-neutral-100 max-h-[90vh] overflow-y-auto"
            dir={isRtl ? 'rtl' : 'ltr'}
          >
            <div className="flex items-center justify-between pb-3 border-b border-neutral-800 mb-4">
              <h3 className="text-base font-bold text-neutral-100">
                {editingPlan.id ? (isRtl ? 'ویرایش پلن اشتراک' : 'Edit Plan') : (isRtl ? 'افزودن پلن جدید' : 'New Plan')}
              </h3>
              <button
                onClick={() => setModalOpen(false)}
                className="p-1 text-neutral-400 hover:text-neutral-200 rounded-lg"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSave} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-neutral-300 mb-1">
                  {isRtl ? 'نام پلن:' : 'Plan Name:'}
                </label>
                <input
                  type="text"
                  value={editingPlan.name || ''}
                  onChange={e => setEditingPlan({ ...editingPlan, name: e.target.value })}
                  placeholder="اشتراک طلایی ۱۰۰ گیگ"
                  className="w-full px-3 py-2 bg-neutral-950 border border-neutral-800 rounded-xl text-neutral-200 focus:outline-none focus:border-cyan-500/60"
                  required
                />
              </div>

              <div>
                <label className="block font-semibold text-neutral-300 mb-1">
                  {isRtl ? 'توضیحات کوتاه:' : 'Description:'}
                </label>
                <input
                  type="text"
                  value={editingPlan.description || ''}
                  onChange={e => setEditingPlan({ ...editingPlan, description: e.target.value })}
                  placeholder="سرعت بالا، آی‌پی ثابت ۲ کاربره"
                  className="w-full px-3 py-2 bg-neutral-950 border border-neutral-800 rounded-xl text-neutral-200 focus:outline-none focus:border-cyan-500/60"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-neutral-300 mb-1">
                    {isRtl ? `قیمت (${currency}):` : `Price (${currency}):`}
                  </label>
                  <input
                    type="number"
                    value={editingPlan.price || 0}
                    onChange={e => setEditingPlan({ ...editingPlan, price: parseInt(e.target.value) || 0 })}
                    className="w-full px-3 py-2 bg-neutral-950 border border-neutral-800 rounded-xl font-mono text-neutral-200 focus:outline-none focus:border-cyan-500/60"
                    required
                  />
                </div>

                <div>
                  <label className="block font-semibold text-neutral-300 mb-1">
                    {isRtl ? 'حجم (گیگابایت):' : 'Traffic (GB):'}
                  </label>
                  <input
                    type="number"
                    value={editingPlan.traffic_gb || 0}
                    onChange={e => setEditingPlan({ ...editingPlan, traffic_gb: parseInt(e.target.value) || 0 })}
                    className="w-full px-3 py-2 bg-neutral-950 border border-neutral-800 rounded-xl font-mono text-neutral-200 focus:outline-none focus:border-cyan-500/60"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-neutral-300 mb-1">
                    {isRtl ? 'مدت اعتبار (روز):' : 'Duration (Days):'}
                  </label>
                  <input
                    type="number"
                    value={editingPlan.duration_days || 30}
                    onChange={e => setEditingPlan({ ...editingPlan, duration_days: parseInt(e.target.value) || 30 })}
                    className="w-full px-3 py-2 bg-neutral-950 border border-neutral-800 rounded-xl font-mono text-neutral-200 focus:outline-none focus:border-cyan-500/60"
                    required
                  />
                </div>

                <div>
                  <label className="block font-semibold text-neutral-300 mb-1">
                    {isRtl ? 'اینباند 3X-UI:' : 'Target Inbound:'}
                  </label>
                  <select
                    value={editingPlan.inbound_id || 1}
                    onChange={e => setEditingPlan({ ...editingPlan, inbound_id: parseInt(e.target.value) || 1 })}
                    className="w-full px-3 py-2 bg-neutral-950 border border-neutral-800 rounded-xl text-neutral-200 focus:outline-none focus:border-cyan-500/60"
                  >
                    {inbounds.map(ib => (
                      <option key={ib.id} value={ib.inbound_id}>
                        ID #{ib.inbound_id} - {ib.remark}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-neutral-300 mb-1">
                    {isRtl ? 'حداکثر کاربر همزمان:' : 'Max IPs:'}
                  </label>
                  <input
                    type="number"
                    value={editingPlan.max_ips || 2}
                    onChange={e => setEditingPlan({ ...editingPlan, max_ips: parseInt(e.target.value) || 2 })}
                    className="w-full px-3 py-2 bg-neutral-950 border border-neutral-800 rounded-xl font-mono text-neutral-200 focus:outline-none focus:border-cyan-500/60"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-neutral-300 mb-1">
                    {isRtl ? 'ترتیب نمایش:' : 'Sort Order:'}
                  </label>
                  <input
                    type="number"
                    value={editingPlan.sort_order || 1}
                    onChange={e => setEditingPlan({ ...editingPlan, sort_order: parseInt(e.target.value) || 1 })}
                    className="w-full px-3 py-2 bg-neutral-950 border border-neutral-800 rounded-xl font-mono text-neutral-200 focus:outline-none focus:border-cyan-500/60"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2 pt-2">
                <input
                  type="checkbox"
                  id="plan_active_chk"
                  checked={editingPlan.is_active ?? true}
                  onChange={e => setEditingPlan({ ...editingPlan, is_active: e.target.checked })}
                  className="rounded border-neutral-800 text-cyan-600 focus:ring-cyan-500 w-4 h-4"
                />
                <label htmlFor="plan_active_chk" className="text-neutral-300 font-medium">
                  {isRtl ? 'پلن برای خرید در ربات فعال باشد' : 'Plan is active and visible in bot'}
                </label>
              </div>

              <div className="flex items-center justify-end gap-2 pt-4 border-t border-neutral-800">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="py-2 px-4 rounded-xl bg-neutral-800 hover:bg-neutral-700 text-neutral-300 text-xs"
                >
                  {isRtl ? 'انصراف' : 'Cancel'}
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="py-2 px-5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs transition-colors"
                >
                  {saving ? (isRtl ? 'در حال ذخیره...' : 'Saving...') : (isRtl ? 'ذخیره پلن' : 'Save Plan')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
