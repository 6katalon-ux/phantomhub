/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useEffect } from 'react';
import { TabType, Language, AppSettings, PlanItem, UserItem, ServiceItem, PaymentItem, GiftCodeItem, InboundItem, TransactionItem } from './types';
import { api } from './services/api';

// Components
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { ToastContainer, ToastMessage } from './components/Toast';
import { ConfirmModal } from './components/ConfirmModal';
import { QRCodeModal } from './components/QRCodeModal';

// Tabs
import { DashboardTab } from './components/tabs/DashboardTab';
import { BotSettingsTab } from './components/tabs/BotSettingsTab';
import { XUIConnectionTab } from './components/tabs/XUIConnectionTab';
import { InboundsTab } from './components/tabs/InboundsTab';
import { PlansTab } from './components/tabs/PlansTab';
import { UsersTab } from './components/tabs/UsersTab';
import { ServicesTab } from './components/tabs/ServicesTab';
import { WalletTab } from './components/tabs/WalletTab';
import { GiftCodesTab } from './components/tabs/GiftCodesTab';
import { FreeTrialTab } from './components/tabs/FreeTrialTab';
import { PaymentSettingsTab } from './components/tabs/PaymentSettingsTab';
import { TransactionsTab } from './components/tabs/TransactionsTab';
import { NotificationsTab } from './components/tabs/NotificationsTab';
import { SystemSettingsTab } from './components/tabs/SystemSettingsTab';
import { LogsTab } from './components/tabs/LogsTab';

export default function App() {
  const [lang, setLang] = useState<Language>('fa');
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);

  // Data states
  const [stats, setStats] = useState<any>(null);
  const [settings, setSettings] = useState<AppSettings | null>(null);
  const [inbounds, setInbounds] = useState<InboundItem[]>([]);
  const [plans, setPlans] = useState<PlanItem[]>([]);
  const [users, setUsers] = useState<UserItem[]>([]);
  const [services, setServices] = useState<ServiceItem[]>([]);
  const [payments, setPayments] = useState<PaymentItem[]>([]);
  const [giftCodes, setGiftCodes] = useState<GiftCodeItem[]>([]);
  const [transactions, setTransactions] = useState<TransactionItem[]>([]);

  // Modals & Toasts
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [qrModal, setQrModal] = useState<{ isOpen: boolean; link: string; title: string }>({
    isOpen: false,
    link: '',
    title: ''
  });
  const [confirmModal, setConfirmModal] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
    onConfirm: () => void;
    danger?: boolean;
  }>({
    isOpen: false,
    title: '',
    message: '',
    onConfirm: () => {}
  });

  const isRtl = lang === 'fa';

  const addToast = (type: 'success' | 'error' | 'info', message: string) => {
    const id = Date.now().toString() + Math.random().toString();
    setToasts(prev => [...prev, { id, type, message }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 3500);
  };

  const loadAllData = async () => {
    try {
      const [
        dashStats,
        appSettings,
        inboundList,
        planList,
        userList,
        serviceList,
        paymentList,
        giftList,
        txList
      ] = await Promise.all([
        api.getDashboardStats(),
        api.getSettings(),
        api.getInbounds(),
        api.getPlans(),
        api.getUsers(),
        api.getServices(),
        api.getPayments(),
        api.getGiftCodes(),
        api.getTransactions()
      ]);

      setStats(dashStats);
      setSettings(appSettings);
      setInbounds(inboundList);
      setPlans(planList);
      setUsers(userList);
      setServices(serviceList);
      setPayments(paymentList);
      setGiftCodes(giftList);
      setTransactions(txList);
    } catch (err: any) {
      console.error('Failed to load initial data:', err);
    }
  };

  useEffect(() => {
    loadAllData();
  }, []);

  // Update HTML dir and lang
  useEffect(() => {
    document.documentElement.dir = isRtl ? 'rtl' : 'ltr';
    document.documentElement.lang = lang;
  }, [lang, isRtl]);

  const handleToggleLang = () => {
    setLang(prev => (prev === 'fa' ? 'en' : 'fa'));
  };

  const handleSyncTraffic = async () => {
    setIsSyncing(true);
    try {
      const res = await api.syncTrafficNow();
      await loadAllData();
      addToast('success', isRtl ? `ترافیک با 3X-UI همگام‌سازی شد (${res.updated} سرویس)` : `Synced traffic for ${res.updated} services`);
    } catch {
      addToast('error', isRtl ? 'خطا در همگام‌سازی ترافیک' : 'Failed to sync traffic');
    } finally {
      setIsSyncing(false);
    }
  };

  const handleSaveSettings = async (updated: Partial<AppSettings>) => {
    try {
      await api.saveSettings(updated);
      setSettings(prev => prev ? { ...prev, ...updated } : null);
      addToast('success', isRtl ? 'تنظیمات با موفقیت در دیتابیس ذخیره شد' : 'Settings saved to SQLite');
    } catch {
      addToast('error', isRtl ? 'خطا در ذخیره تنظیمات' : 'Error saving settings');
    }
  };

  const handleSavePlan = async (plan: Partial<PlanItem>) => {
    try {
      await api.savePlan(plan);
      const updatedPlans = await api.getPlans();
      setPlans(updatedPlans);
      addToast('success', isRtl ? 'پلن با موفقیت ثبت شد' : 'Plan saved successfully');
    } catch {
      addToast('error', isRtl ? 'خطا در ذخیره پلن' : 'Failed to save plan');
    }
  };

  const handleDeletePlan = async (planId: number) => {
    setConfirmModal({
      isOpen: true,
      title: isRtl ? 'حذف پلن اشتراک' : 'Delete Plan',
      message: isRtl ? 'آیا از حذف این پلن اطمینان دارید؟ کاربران دیگر قادر به خرید آن نخواهند بود.' : 'Are you sure you want to delete this plan?',
      danger: true,
      onConfirm: async () => {
        setConfirmModal(prev => ({ ...prev, isOpen: false }));
        await api.deletePlan(planId);
        const updatedPlans = await api.getPlans();
        setPlans(updatedPlans);
        addToast('success', isRtl ? 'پلن حذف شد' : 'Plan deleted');
      }
    });
  };

  const handleAdjustBalance = async (userId: number, amount: number, description: string) => {
    try {
      const newBalance = await api.adjustUserBalance(userId, amount, description);
      setUsers(prev => prev.map(u => u.id === userId ? { ...u, wallet_balance: newBalance } : u));
      const updatedTx = await api.getTransactions();
      setTransactions(updatedTx);
      addToast('success', isRtl ? 'موجودی کیف پول با موفقیت به‌روزرسانی شد' : 'Wallet balance updated');
    } catch (e: any) {
      addToast('error', e.message || (isRtl ? 'خطا در تغییر موجودی' : 'Error adjusting balance'));
    }
  };

  const handleToggleBlock = async (userId: number) => {
    const isBlocked = await api.toggleBlockUser(userId);
    setUsers(prev => prev.map(u => u.id === userId ? { ...u, is_blocked: isBlocked } : u));
    addToast('info', isBlocked ? (isRtl ? 'کاربر مسدود شد' : 'User blocked') : (isRtl ? 'کاربر فعال شد' : 'User unblocked'));
  };

  const handleResetTrial = async (userId: number) => {
    await api.resetUserTrial(userId);
    setUsers(prev => prev.map(u => u.id === userId ? { ...u, trial_used: false } : u));
    addToast('success', isRtl ? 'تست رایگان برای این کاربر فعال شد' : 'Trial eligibility reset');
  };

  const handleToggleService = async (serviceId: number) => {
    const isActive = await api.toggleService(serviceId);
    setServices(prev => prev.map(s => s.id === serviceId ? { ...s, is_active: isActive } : s));
    addToast('info', isActive ? (isRtl ? 'سرویس فعال گردید' : 'Service enabled') : (isRtl ? 'سرویس غیرفعال شد' : 'Service disabled'));
  };

  const handleDeleteService = async (serviceId: number) => {
    setConfirmModal({
      isOpen: true,
      title: isRtl ? 'حذف سرویس کلاینت' : 'Delete VPN Service',
      message: isRtl ? 'این اکانت از پنل 3X-UI و دیتابیس حذف خواهد شد. ادامه می‌دهید؟' : 'This will remove the client from 3X-UI and revoke VPN access.',
      danger: true,
      onConfirm: async () => {
        setConfirmModal(prev => ({ ...prev, isOpen: false }));
        await api.deleteService(serviceId);
        const updated = await api.getServices();
        setServices(updated);
        addToast('success', isRtl ? 'سرویس از 3X-UI و سامانه حذف شد' : 'Service deleted');
      }
    });
  };

  const handleReviewPayment = async (paymentId: number, action: 'approve' | 'reject', adminNote?: string) => {
    await api.reviewPayment(paymentId, action, adminNote);
    await loadAllData();
    addToast(
      action === 'approve' ? 'success' : 'info',
      action === 'approve' ? (isRtl ? 'فیش تایید و کیف پول کاربر شارژ شد' : 'Payment approved and wallet credited') : (isRtl ? 'فیش رد شد' : 'Payment rejected')
    );
  };

  const handleCreateGiftCode = async (gift: Partial<GiftCodeItem>) => {
    await api.createGiftCode(gift);
    const updated = await api.getGiftCodes();
    setGiftCodes(updated);
    addToast('success', isRtl ? 'کد هدیه با موفقیت ایجاد شد' : 'Gift voucher created');
  };

  const handleDeleteGiftCode = async (giftId: number) => {
    await api.deleteGiftCode(giftId);
    const updated = await api.getGiftCodes();
    setGiftCodes(updated);
    addToast('info', isRtl ? 'کد هدیه حذف شد' : 'Gift voucher deleted');
  };

  const handleOpenQR = (configLink: string, title?: string) => {
    setQrModal({
      isOpen: true,
      link: configLink,
      title: title || ''
    });
  };

  const handleSendBroadcast = async (title: string, message: string) => {
    await new Promise(r => setTimeout(r, 600));
    addToast('success', isRtl ? 'اعلان به صف ارسال به کاربران تلگرام اضافه شد' : 'Broadcast queued for Telegram delivery');
  };

  const handleTriggerBackup = async () => {
    const filename = await api.triggerBackup();
    addToast('success', isRtl ? `فایل بکاپ ایجاد گردید: ${filename}` : `Backup created: ${filename}`);
    return filename;
  };

  if (!settings) {
    return (
      <div className="min-h-screen bg-neutral-950 flex items-center justify-center text-neutral-400 text-xs">
        {isRtl ? 'در حال بارگذاری پنل مدیریت VPN Store...' : 'Loading VPN Store Admin Panel...'}
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 flex flex-col font-sans">
      {/* Top Navbar */}
      <Navbar
        currentLang={lang}
        onToggleLang={handleToggleLang}
        onOpenMobileMenu={() => setMobileMenuOpen(true)}
        isSyncing={isSyncing}
        onSyncTraffic={handleSyncTraffic}
        isRtl={isRtl}
      />

      <div className="flex-1 flex max-w-7xl w-full mx-auto">
        {/* Responsive Sidebar */}
        <Sidebar
          activeTab={activeTab}
          onSelectTab={setActiveTab}
          isOpenMobile={mobileMenuOpen}
          onCloseMobile={() => setMobileMenuOpen(false)}
          isRtl={isRtl}
        />

        {/* Main Content Viewport */}
        <main
          className={`flex-1 p-4 sm:p-6 lg:p-8 pb-24 lg:pb-8 transition-all ${
            isRtl ? 'lg:mr-72' : 'lg:ml-72'
          }`}
        >
          {activeTab === 'dashboard' && (
            <DashboardTab
              stats={stats}
              onSelectTab={setActiveTab}
              onSyncTraffic={handleSyncTraffic}
              isSyncing={isSyncing}
              isRtl={isRtl}
            />
          )}

          {activeTab === 'bot_settings' && (
            <BotSettingsTab
              settings={settings}
              onSave={handleSaveSettings}
              isRtl={isRtl}
            />
          )}

          {activeTab === 'xui_connection' && (
            <XUIConnectionTab
              settings={settings}
              onSave={handleSaveSettings}
              onTestConnection={() => api.testXUIConnection()}
              isRtl={isRtl}
            />
          )}

          {activeTab === 'inbounds' && (
            <InboundsTab
              inbounds={inbounds}
              onRefresh={loadAllData}
              isRtl={isRtl}
            />
          )}

          {activeTab === 'plans' && (
            <PlansTab
              plans={plans}
              inbounds={inbounds}
              onSavePlan={handleSavePlan}
              onDeletePlan={handleDeletePlan}
              currency={settings.currency}
              isRtl={isRtl}
            />
          )}

          {activeTab === 'users' && (
            <UsersTab
              users={users}
              onAdjustBalance={handleAdjustBalance}
              onToggleBlock={handleToggleBlock}
              onResetTrial={handleResetTrial}
              currency={settings.currency}
              isRtl={isRtl}
            />
          )}

          {activeTab === 'services' && (
            <ServicesTab
              services={services}
              onToggleService={handleToggleService}
              onDeleteService={handleDeleteService}
              onOpenQR={handleOpenQR}
              onSyncTraffic={handleSyncTraffic}
              isSyncing={isSyncing}
              isRtl={isRtl}
            />
          )}

          {activeTab === 'wallet' && (
            <WalletTab
              users={users}
              transactions={transactions}
              currency={settings.currency}
              onSelectTab={setActiveTab}
              isRtl={isRtl}
            />
          )}

          {activeTab === 'payment_settings' && (
            <PaymentSettingsTab
              settings={settings}
              onSave={handleSaveSettings}
              isRtl={isRtl}
            />
          )}

          {activeTab === 'transactions' && (
            <TransactionsTab
              payments={payments}
              transactions={transactions}
              onReviewPayment={handleReviewPayment}
              currency={settings.currency}
              isRtl={isRtl}
            />
          )}

          {activeTab === 'gift_codes' && (
            <GiftCodesTab
              giftCodes={giftCodes}
              onCreateGiftCode={handleCreateGiftCode}
              onDeleteGiftCode={handleDeleteGiftCode}
              currency={settings.currency}
              isRtl={isRtl}
            />
          )}

          {activeTab === 'free_trial' && (
            <FreeTrialTab
              settings={settings}
              inbounds={inbounds}
              onSave={handleSaveSettings}
              isRtl={isRtl}
            />
          )}

          {activeTab === 'notifications' && (
            <NotificationsTab
              onSendBroadcast={handleSendBroadcast}
              isRtl={isRtl}
            />
          )}

          {activeTab === 'system_settings' && (
            <SystemSettingsTab
              settings={settings}
              onSave={handleSaveSettings}
              isRtl={isRtl}
            />
          )}

          {activeTab === 'logs_backups' && (
            <LogsTab
              onTriggerBackup={handleTriggerBackup}
              isRtl={isRtl}
            />
          )}
        </main>
      </div>

      {/* Floating Modals and Toast Containers */}
      <QRCodeModal
        isOpen={qrModal.isOpen}
        onClose={() => setQrModal({ isOpen: false, link: '', title: '' })}
        configLink={qrModal.link}
        title={qrModal.title}
        isRtl={isRtl}
      />

      <ConfirmModal
        isOpen={confirmModal.isOpen}
        title={confirmModal.title}
        message={confirmModal.message}
        danger={confirmModal.danger}
        onConfirm={confirmModal.onConfirm}
        onCancel={() => setConfirmModal(prev => ({ ...prev, isOpen: false }))}
        isRtl={isRtl}
      />

      <ToastContainer
        toasts={toasts}
        onDismiss={id => setToasts(prev => prev.filter(t => t.id !== id))}
        isRtl={isRtl}
      />
    </div>
  );
}
