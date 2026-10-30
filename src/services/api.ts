import {
  AppSettings, InboundItem, PlanItem, UserItem, ServiceItem,
  PaymentItem, GiftCodeItem, TransactionItem
} from '../types';
import {
  INITIAL_SETTINGS, INITIAL_INBOUNDS, INITIAL_PLANS,
  INITIAL_USERS, INITIAL_SERVICES, INITIAL_PAYMENTS,
  INITIAL_GIFT_CODES, INITIAL_TRANSACTIONS
} from '../data/initialData';

// LocalStorage Persistence Helpers for Preview and Local Operation
function loadFromStorage<T>(key: string, fallback: T): T {
  try {
    const data = localStorage.getItem(`vpn_store_${key}`);
    return data ? JSON.parse(data) : fallback;
  } catch {
    return fallback;
  }
}

function saveToStorage<T>(key: string, data: T): void {
  try {
    localStorage.setItem(`vpn_store_${key}`, JSON.stringify(data));
  } catch (e) {
    console.error('LocalStorage write error:', e);
  }
}

class ApiService {
  private settings: AppSettings = loadFromStorage('settings', INITIAL_SETTINGS);
  private inbounds: InboundItem[] = loadFromStorage('inbounds', INITIAL_INBOUNDS);
  private plans: PlanItem[] = loadFromStorage('plans', INITIAL_PLANS);
  private users: UserItem[] = loadFromStorage('users', INITIAL_USERS);
  private services: ServiceItem[] = loadFromStorage('services', INITIAL_SERVICES);
  private payments: PaymentItem[] = loadFromStorage('payments', INITIAL_PAYMENTS);
  private giftCodes: GiftCodeItem[] = loadFromStorage('gift_codes', INITIAL_GIFT_CODES);
  private transactions: TransactionItem[] = loadFromStorage('transactions', INITIAL_TRANSACTIONS);

  // --- Dashboard ---
  async getDashboardStats() {
    const totalUsers = this.users.length;
    const activeServices = this.services.filter(s => s.is_active).length;
    const expiredServices = this.services.filter(s => !s.is_active).length;
    const pendingPayments = this.payments.filter(p => p.status === 'pending').length;
    
    // Total sales
    const totalSales = this.transactions
      .filter(t => t.type === 'purchase')
      .reduce((sum, t) => sum + Math.abs(t.amount), 0);

    const walletLiabilities = this.users.reduce((sum, u) => sum + u.wallet_balance, 0);

    return {
      users_count: totalUsers,
      active_services: activeServices,
      expired_services: expiredServices,
      total_sales: totalSales,
      wallet_liabilities: walletLiabilities,
      pending_payments: pendingPayments,
      last_sync: new Date().toLocaleTimeString('fa-IR'),
      currency: this.settings.currency,
      bot_configured: Boolean(this.settings.bot_token),
      bot_enabled: this.settings.bot_enabled
    };
  }

  // --- Settings ---
  async getSettings(): Promise<AppSettings> {
    return { ...this.settings };
  }

  async saveSettings(newSettings: Partial<AppSettings>): Promise<boolean> {
    this.settings = { ...this.settings, ...newSettings };
    saveToStorage('settings', this.settings);
    return true;
  }

  async testXUIConnection(): Promise<{ success: boolean; message: string; latency_ms: number; inbounds_count: number }> {
    await new Promise(r => setTimeout(r, 650));
    if (!this.settings.xui_url || !this.settings.xui_username) {
      return {
        success: false,
        message: 'آدرس و مشخصات ورود به پنل 3X-UI تنظیم نشده است.',
        latency_ms: 0,
        inbounds_count: 0
      };
    }
    return {
      success: true,
      message: 'ارتباط با سرور 3X-UI با موفقیت برقرار شد. سشن لاگین معتبر است.',
      latency_ms: 48,
      inbounds_count: this.inbounds.length
    };
  }

  // --- Inbounds ---
  async getInbounds(): Promise<InboundItem[]> {
    return [...this.inbounds];
  }

  // --- Plans ---
  async getPlans(): Promise<PlanItem[]> {
    return [...this.plans];
  }

  async savePlan(plan: Partial<PlanItem>): Promise<PlanItem> {
    if (plan.id) {
      this.plans = this.plans.map(p => p.id === plan.id ? { ...p, ...plan } as PlanItem : p);
    } else {
      const newPlan: PlanItem = {
        id: Date.now(),
        name: plan.name || 'پلن جدید',
        description: plan.description || '',
        price: plan.price || 100000,
        traffic_gb: plan.traffic_gb || 30,
        duration_days: plan.duration_days || 30,
        inbound_id: plan.inbound_id || 1,
        protocol: plan.protocol || 'vless',
        max_ips: plan.max_ips || 2,
        is_active: plan.is_active ?? true,
        sort_order: this.plans.length + 1
      };
      this.plans.push(newPlan);
    }
    saveToStorage('plans', this.plans);
    return plan as PlanItem;
  }

  async deletePlan(planId: number): Promise<boolean> {
    this.plans = this.plans.filter(p => p.id !== planId);
    saveToStorage('plans', this.plans);
    return true;
  }

  // --- Users ---
  async getUsers(searchQuery?: string): Promise<UserItem[]> {
    if (!searchQuery) return [...this.users];
    const q = searchQuery.toLowerCase();
    return this.users.filter(u =>
      u.username?.toLowerCase().includes(q) ||
      u.first_name?.toLowerCase().includes(q) ||
      u.telegram_id.toString().includes(q)
    );
  }

  async adjustUserBalance(userId: number, amount: number, description: string): Promise<number> {
    const user = this.users.find(u => u.id === userId);
    if (!user) throw new Error('کاربر یافت نشد');
    user.wallet_balance = Math.max(0, user.wallet_balance + amount);
    
    // Add transaction
    this.transactions.unshift({
      id: Date.now(),
      user_id: userId,
      amount,
      balance_after: user.wallet_balance,
      type: 'admin_adjustment',
      description: description || 'تغییر دستی موجودی توسط مدیریت',
      created_at: new Date().toISOString()
    });

    saveToStorage('users', this.users);
    saveToStorage('transactions', this.transactions);
    return user.wallet_balance;
  }

  async toggleBlockUser(userId: number): Promise<boolean> {
    const user = this.users.find(u => u.id === userId);
    if (!user) return false;
    user.is_blocked = !user.is_blocked;
    saveToStorage('users', this.users);
    return user.is_blocked;
  }

  async resetUserTrial(userId: number): Promise<boolean> {
    const user = this.users.find(u => u.id === userId);
    if (!user) return false;
    user.trial_used = false;
    saveToStorage('users', this.users);
    return true;
  }

  // --- Services ---
  async getServices(): Promise<ServiceItem[]> {
    return [...this.services];
  }

  async toggleService(serviceId: number): Promise<boolean> {
    const service = this.services.find(s => s.id === serviceId);
    if (!service) return false;
    service.is_active = !service.is_active;
    saveToStorage('services', this.services);
    return service.is_active;
  }

  async deleteService(serviceId: number): Promise<boolean> {
    this.services = this.services.filter(s => s.id !== serviceId);
    saveToStorage('services', this.services);
    return true;
  }

  async syncTrafficNow(): Promise<{ updated: number; timestamp: string }> {
    await new Promise(r => setTimeout(r, 800));
    // Simulate updating traffic
    this.services.forEach(s => {
      if (s.is_active) {
        s.used_traffic_bytes = Math.min(
          s.total_traffic_bytes,
          s.used_traffic_bytes + Math.floor(Math.random() * 200 * 1024 * 1024)
        );
      }
    });
    saveToStorage('services', this.services);
    return {
      updated: this.services.length,
      timestamp: new Date().toLocaleTimeString('fa-IR')
    };
  }

  // --- Payments ---
  async getPayments(): Promise<PaymentItem[]> {
    return [...this.payments];
  }

  async reviewPayment(paymentId: number, action: 'approve' | 'reject', adminNote?: string): Promise<boolean> {
    const payment = this.payments.find(p => p.id === paymentId);
    if (!payment || payment.status !== 'pending') return false;

    payment.status = action === 'approve' ? 'approved' : 'rejected';
    payment.admin_note = adminNote;
    payment.reviewed_at = new Date().toISOString();

    if (action === 'approve') {
      const user = this.users.find(u => u.id === payment.user_id);
      if (user) {
        user.wallet_balance += payment.amount;
        this.transactions.unshift({
          id: Date.now(),
          user_id: user.id,
          amount: payment.amount,
          balance_after: user.wallet_balance,
          type: 'topup',
          description: `شارژ خودکار پس از تایید فیش واریزی #${payment.id}`,
          created_at: new Date().toISOString()
        });
        saveToStorage('users', this.users);
        saveToStorage('transactions', this.transactions);
      }
    }

    saveToStorage('payments', this.payments);
    return true;
  }

  // --- Gift Codes ---
  async getGiftCodes(): Promise<GiftCodeItem[]> {
    return [...this.giftCodes];
  }

  async createGiftCode(gift: Partial<GiftCodeItem>): Promise<GiftCodeItem> {
    const newGift: GiftCodeItem = {
      id: Date.now(),
      code: (gift.code || 'GIFT' + Math.floor(Math.random() * 90000 + 10000)).toUpperCase(),
      amount: gift.amount || 50000,
      max_redemptions: gift.max_redemptions || 10,
      redeemed_count: 0,
      expire_at: gift.expire_at || null,
      is_active: true,
      created_at: new Date().toISOString()
    };
    this.giftCodes.unshift(newGift);
    saveToStorage('gift_codes', this.giftCodes);
    return newGift;
  }

  async deleteGiftCode(giftId: number): Promise<boolean> {
    this.giftCodes = this.giftCodes.filter(g => g.id !== giftId);
    saveToStorage('gift_codes', this.giftCodes);
    return true;
  }

  // --- Transactions ---
  async getTransactions(): Promise<TransactionItem[]> {
    return [...this.transactions];
  }

  // --- Logs & Backups ---
  async getLogs(type: 'web' | 'bot' | 'worker'): Promise<string[]> {
    const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
    if (type === 'bot') {
      return [
        `[${timestamp}] [INFO] [bot]: Starting Aiogram 3 Telegram Bot worker...`,
        `[${timestamp}] [INFO] [bot]: Bot Token verified: @vpn_store_bot`,
        `[${timestamp}] [INFO] [bot]: Registered handlers for /start, buy, free_trial, wallet, support`,
        `[${timestamp}] [INFO] [bot]: Started long polling dispatch loop (0 drop_pending)`
      ];
    }
    if (type === 'worker') {
      return [
        `[${timestamp}] [INFO] [worker]: Background scheduler process online.`,
        `[${timestamp}] [INFO] [worker]: Traffic sync cycle executed. Inbounds queried.`,
        `[${timestamp}] [INFO] [worker]: Checked ${this.services.length} active service records.`,
        `[${timestamp}] [INFO] [worker]: SQLite WAL checkpoint executed.`
      ];
    }
    return [
      `[${timestamp}] [INFO] [uvicorn]: Started server process [PID 4120]`,
      `[${timestamp}] [INFO] [uvicorn]: Uvicorn running on http://0.0.0.0:8000`,
      `[${timestamp}] [INFO] [fastapi]: Mounted /api routes. Database connection established.`,
      `[${timestamp}] [INFO] [web]: Admin dashboard loaded from mobile client (Android 14 Chrome)`
    ];
  }

  async triggerBackup(): Promise<string> {
    await new Promise(r => setTimeout(r, 600));
    return `vpn_store_backup_${Date.now()}.db`;
  }
}

export const api = new ApiService();
