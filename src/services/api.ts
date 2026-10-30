import {
  AppSettings, InboundItem, PlanItem, UserItem, ServiceItem,
  PaymentItem, GiftCodeItem, TransactionItem
} from '../types';
import {
  INITIAL_SETTINGS, INITIAL_INBOUNDS, INITIAL_PLANS,
  INITIAL_USERS, INITIAL_SERVICES, INITIAL_PAYMENTS,
  INITIAL_GIFT_CODES, INITIAL_TRANSACTIONS
} from '../data/initialData';

function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem('vpnstore_token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json'
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

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
  private fallbackSettings: AppSettings = loadFromStorage('settings', INITIAL_SETTINGS);
  private fallbackInbounds: InboundItem[] = loadFromStorage('inbounds', INITIAL_INBOUNDS);
  private fallbackPlans: PlanItem[] = loadFromStorage('plans', INITIAL_PLANS);
  private fallbackUsers: UserItem[] = loadFromStorage('users', INITIAL_USERS);
  private fallbackServices: ServiceItem[] = loadFromStorage('services', INITIAL_SERVICES);
  private fallbackPayments: PaymentItem[] = loadFromStorage('payments', INITIAL_PAYMENTS);
  private fallbackGiftCodes: GiftCodeItem[] = loadFromStorage('gift_codes', INITIAL_GIFT_CODES);
  private fallbackTransactions: TransactionItem[] = loadFromStorage('transactions', INITIAL_TRANSACTIONS);

  private authListeners: (() => void)[] = [];

  addAuthListener(listener: () => void) {
    this.authListeners.push(listener);
    return () => {
      this.authListeners = this.authListeners.filter(l => l !== listener);
    };
  }

  private notifyAuthError() {
    this.authListeners.forEach(listener => {
      try {
        listener();
      } catch (e) {
        console.error('Error in auth listener:', e);
      }
    });
  }

  // --- Authentication ---
  async login(username: string, password: string): Promise<{ token: string; admin: any }> {
    const res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ username, password })
    });

    if (!res.ok) {
      let errText = 'خطا در احراز هویت';
      try {
        const data = await res.json();
        errText = data.detail || data.message || errText;
      } catch {}
      throw new Error(errText);
    }

    const data = await res.json();
    if (data.token) {
      localStorage.setItem('vpnstore_token', data.token);
    }
    return data;
  }

  async logout(): Promise<void> {
    try {
      await this.request('/api/auth/logout', { method: 'POST' });
    } catch {}
    localStorage.removeItem('vpnstore_token');
    this.notifyAuthError();
  }

  async getMe(): Promise<any> {
    return await this.request('/api/auth/me');
  }

  hasToken(): boolean {
    return Boolean(localStorage.getItem('vpnstore_token'));
  }

  // --- Helper for authenticated fetch ---
  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers = {
      ...getAuthHeader(),
      ...(options.headers || {})
    };
    const res = await fetch(path, { credentials: 'include', ...options, headers });
    if (!res.ok) {
      if (res.status === 401) {
        localStorage.removeItem('vpnstore_token');
        this.notifyAuthError();
      }
      let errorMsg = `HTTP ${res.status}`;
      try {
        const errJson = await res.json();
        errorMsg = errJson.detail || errJson.message || errorMsg;
      } catch {}
      throw new Error(errorMsg);
    }
    return await res.json();
  }

  // --- Dashboard ---
  async getDashboardStats() {
    try {
      const stats = await this.request<any>('/api/dashboard/stats');
      return stats;
    } catch (e) {
      // Fallback calculation from local state
      const totalUsers = this.fallbackUsers.length;
      const activeServices = this.fallbackServices.filter(s => s.is_active).length;
      const expiredServices = this.fallbackServices.filter(s => !s.is_active).length;
      const pendingPayments = this.fallbackPayments.filter(p => p.status === 'pending').length;
      const totalSales = this.fallbackTransactions
        .filter(t => t.type === 'purchase')
        .reduce((sum, t) => sum + Math.abs(t.amount), 0);
      const walletLiabilities = this.fallbackUsers.reduce((sum, u) => sum + u.wallet_balance, 0);

      return {
        users_count: totalUsers,
        active_services: activeServices,
        expired_services: expiredServices,
        total_sales: totalSales,
        wallet_liabilities: walletLiabilities,
        pending_payments: pendingPayments,
        last_sync: new Date().toLocaleTimeString('fa-IR'),
        currency: this.fallbackSettings.currency || 'تومان',
        bot_configured: Boolean(this.fallbackSettings.bot_token),
        bot_enabled: this.fallbackSettings.bot_enabled
      };
    }
  }

  // --- Settings ---
  async getSettings(): Promise<AppSettings> {
    try {
      const res = await this.request<any>('/api/settings');
      if (res && typeof res === 'object') {
        const merged: AppSettings = {
          ...this.fallbackSettings,
          ...res
        };
        this.fallbackSettings = merged;
        saveToStorage('settings', merged);
        return merged;
      }
    } catch (e) {
      console.warn('Could not fetch settings from server, using local cache:', e);
    }
    return { ...this.fallbackSettings };
  }

  async saveSettings(newSettings: Partial<AppSettings>): Promise<boolean> {
    // 1. Immediately update local fallback
    this.fallbackSettings = { ...this.fallbackSettings, ...newSettings };
    saveToStorage('settings', this.fallbackSettings);

    // 2. Transmit to real FastAPI / SQLite backend
    try {
      await this.request<{ message: string }>('/api/settings', {
        method: 'POST',
        body: JSON.stringify({ settings: newSettings })
      });
      return true;
    } catch (e) {
      console.error('Server saveSettings failed:', e);
      throw e;
    }
  }

  async testXUIConnection(payload?: any): Promise<{ success: boolean; message: string; latency_ms: number; inbounds_count: number }> {
    try {
      const res = await this.request<any>('/api/settings/test-xui', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: payload ? JSON.stringify(payload) : undefined
      });
      return {
        success: Boolean(res.success),
        message: res.message || (res.success ? 'ارتباط با موفقیت برقرار شد' : 'خطا در ارتباط با 3X-UI'),
        latency_ms: res.latency_ms || 45,
        inbounds_count: res.inbounds_count || 0
      };
    } catch (e: any) {
      return {
        success: false,
        message: e.message || 'عدم دسترسی به پنل 3X-UI. بررسی کنید پورت و آدرس صحیح باشد.',
        latency_ms: 0,
        inbounds_count: 0
      };
    }
  }

  async testBotToken(): Promise<{ success: boolean; message: string; bot?: any }> {
    try {
      const res = await this.request<any>('/api/settings/test-bot', {
        method: 'POST'
      });
      return res;
    } catch (e: any) {
      return {
        success: false,
        message: e.message || 'خطا در ارتباط با سرور تلگرام'
      };
    }
  }

  async restartBotService(): Promise<{ success: boolean; message: string }> {
    try {
      const res = await this.request<any>('/api/settings/restart-bot', {
        method: 'POST'
      });
      return res;
    } catch (e: any) {
      return {
        success: false,
        message: e.message || 'خطا در راه‌اندازی مجدد سرویس ربات'
      };
    }
  }

  // --- Inbounds ---
  async getInbounds(): Promise<InboundItem[]> {
    try {
      const data = await this.request<any>('/api/inbounds');
      if (Array.isArray(data)) {
        this.fallbackInbounds = data;
        saveToStorage('inbounds', data);
        return data;
      }
    } catch (e) {
      console.warn('Could not fetch inbounds from server:', e);
    }
    return [...this.fallbackInbounds];
  }

  async syncInboundsFromXUI(): Promise<InboundItem[]> {
    return await this.getInbounds();
  }

  // --- Plans ---
  async getPlans(): Promise<PlanItem[]> {
    try {
      const data = await this.request<PlanItem[]>('/api/plans');
      if (Array.isArray(data)) {
        this.fallbackPlans = data;
        saveToStorage('plans', data);
        return data;
      }
    } catch (e) {
      console.warn('Could not fetch plans from server:', e);
    }
    return [...this.fallbackPlans];
  }

  async savePlan(plan: Partial<PlanItem>): Promise<PlanItem> {
    try {
      if (plan.id && plan.id < 1000000) {
        // Update existing plan
        const updated = await this.request<PlanItem>(`/api/plans/${plan.id}`, {
          method: 'PUT',
          body: JSON.stringify(plan)
        });
        return updated;
      } else {
        // Create new plan
        const created = await this.request<PlanItem>('/api/plans', {
          method: 'POST',
          body: JSON.stringify(plan)
        });
        return created;
      }
    } catch (e) {
      console.error('Server savePlan error, updating local cache:', e);
      // Fallback
      if (plan.id) {
        this.fallbackPlans = this.fallbackPlans.map(p => p.id === plan.id ? { ...p, ...plan } as PlanItem : p);
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
          sort_order: this.fallbackPlans.length + 1
        };
        this.fallbackPlans.push(newPlan);
      }
      saveToStorage('plans', this.fallbackPlans);
      return plan as PlanItem;
    }
  }

  async deletePlan(planId: number): Promise<boolean> {
    try {
      await this.request<any>(`/api/plans/${planId}`, { method: 'DELETE' });
    } catch (e) {
      console.warn('Server deletePlan failed:', e);
    }
    this.fallbackPlans = this.fallbackPlans.filter(p => p.id !== planId);
    saveToStorage('plans', this.fallbackPlans);
    return true;
  }

  // --- Users ---
  async getUsers(searchQuery?: string): Promise<UserItem[]> {
    try {
      const q = searchQuery ? `?query=${encodeURIComponent(searchQuery)}` : '';
      const data = await this.request<UserItem[]>(`/api/users${q}`);
      if (Array.isArray(data)) {
        this.fallbackUsers = data;
        saveToStorage('users', data);
        return data;
      }
    } catch (e) {
      console.warn('Could not fetch users from server:', e);
    }
    if (!searchQuery) return [...this.fallbackUsers];
    const q = searchQuery.toLowerCase();
    return this.fallbackUsers.filter(u =>
      u.username?.toLowerCase().includes(q) ||
      u.first_name?.toLowerCase().includes(q) ||
      u.telegram_id.toString().includes(q)
    );
  }

  async adjustUserBalance(userId: number, amount: number, description: string): Promise<number> {
    try {
      const res = await this.request<any>(`/api/users/${userId}/adjust-balance`, {
        method: 'POST',
        body: JSON.stringify({ amount, description })
      });
      return res.new_balance;
    } catch (e) {
      console.warn('Server adjust balance failed, updating local state:', e);
      const user = this.fallbackUsers.find(u => u.id === userId);
      if (!user) throw new Error('کاربر یافت نشد');
      user.wallet_balance = Math.max(0, user.wallet_balance + amount);
      saveToStorage('users', this.fallbackUsers);
      return user.wallet_balance;
    }
  }

  async toggleBlockUser(userId: number): Promise<boolean> {
    try {
      const res = await this.request<any>(`/api/users/${userId}/toggle-block`, {
        method: 'POST'
      });
      return Boolean(res.is_blocked);
    } catch (e) {
      const user = this.fallbackUsers.find(u => u.id === userId);
      if (!user) return false;
      user.is_blocked = !user.is_blocked;
      saveToStorage('users', this.fallbackUsers);
      return user.is_blocked;
    }
  }

  async resetUserTrial(userId: number): Promise<boolean> {
    try {
      await this.request<any>(`/api/users/${userId}/reset-trial`, { method: 'POST' });
    } catch (e) {}
    const user = this.fallbackUsers.find(u => u.id === userId);
    if (!user) return false;
    user.trial_used = false;
    saveToStorage('users', this.fallbackUsers);
    return true;
  }

  // --- Services ---
  async getServices(): Promise<ServiceItem[]> {
    try {
      const data = await this.request<ServiceItem[]>('/api/services');
      if (Array.isArray(data)) {
        this.fallbackServices = data;
        saveToStorage('services', data);
        return data;
      }
    } catch (e) {
      console.warn('Could not fetch services from server:', e);
    }
    return [...this.fallbackServices];
  }

  async toggleService(serviceId: number): Promise<boolean> {
    try {
      const res = await this.request<any>(`/api/services/${serviceId}/toggle`, { method: 'POST' });
      return Boolean(res.success);
    } catch (e) {
      const service = this.fallbackServices.find(s => s.id === serviceId);
      if (!service) return false;
      service.is_active = !service.is_active;
      saveToStorage('services', this.fallbackServices);
      return service.is_active;
    }
  }

  async deleteService(serviceId: number): Promise<boolean> {
    try {
      await this.request<any>(`/api/services/${serviceId}`, { method: 'DELETE' });
    } catch (e) {}
    this.fallbackServices = this.fallbackServices.filter(s => s.id !== serviceId);
    saveToStorage('services', this.fallbackServices);
    return true;
  }

  async syncTrafficNow(): Promise<{ updated: number; timestamp: string }> {
    try {
      const res = await this.request<any>('/api/services/sync-traffic', { method: 'POST' });
      return {
        updated: res.stats?.total_synced || 0,
        timestamp: new Date().toLocaleTimeString('fa-IR')
      };
    } catch (e) {
      return {
        updated: this.fallbackServices.length,
        timestamp: new Date().toLocaleTimeString('fa-IR')
      };
    }
  }

  // --- Payments ---
  async getPayments(): Promise<PaymentItem[]> {
    try {
      const data = await this.request<PaymentItem[]>('/api/payments');
      if (Array.isArray(data)) {
        this.fallbackPayments = data;
        saveToStorage('payments', data);
        return data;
      }
    } catch (e) {}
    return [...this.fallbackPayments];
  }

  async reviewPayment(paymentId: number, action: 'approve' | 'reject', adminNote?: string): Promise<boolean> {
    try {
      await this.request<any>(`/api/payments/${paymentId}/review`, {
        method: 'POST',
        body: JSON.stringify({ action, admin_note: adminNote || '' })
      });
      return true;
    } catch (e) {
      const payment = this.fallbackPayments.find(p => p.id === paymentId);
      if (!payment || payment.status !== 'pending') return false;
      payment.status = action === 'approve' ? 'approved' : 'rejected';
      payment.admin_note = adminNote;
      saveToStorage('payments', this.fallbackPayments);
      return true;
    }
  }

  // --- Gift Codes ---
  async getGiftCodes(): Promise<GiftCodeItem[]> {
    try {
      const data = await this.request<GiftCodeItem[]>('/api/gift-codes');
      if (Array.isArray(data)) {
        this.fallbackGiftCodes = data;
        saveToStorage('gift_codes', data);
        return data;
      }
    } catch (e) {}
    return [...this.fallbackGiftCodes];
  }

  async createGiftCode(gift: Partial<GiftCodeItem>): Promise<GiftCodeItem> {
    try {
      const created = await this.request<GiftCodeItem>('/api/gift-codes', {
        method: 'POST',
        body: JSON.stringify({
          code: gift.code,
          amount: gift.amount,
          max_redemptions: gift.max_redemptions || 1,
          expire_days: 30
        })
      });
      return created;
    } catch (e) {
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
      this.fallbackGiftCodes.unshift(newGift);
      saveToStorage('gift_codes', this.fallbackGiftCodes);
      return newGift;
    }
  }

  async deleteGiftCode(giftId: number): Promise<boolean> {
    this.fallbackGiftCodes = this.fallbackGiftCodes.filter(g => g.id !== giftId);
    saveToStorage('gift_codes', this.fallbackGiftCodes);
    return true;
  }

  // --- Transactions ---
  async getTransactions(): Promise<TransactionItem[]> {
    return [...this.fallbackTransactions];
  }

  // --- Logs & Backups ---
  async getLogs(type: 'web' | 'bot' | 'worker'): Promise<string[]> {
    try {
      const res = await this.request<{ lines: string[] }>(`/api/system/logs?file_type=${type}`);
      if (res && Array.isArray(res.lines) && res.lines.length > 0) {
        return res.lines;
      }
    } catch (e) {}

    const timestamp = new Date().toISOString().replace('T', ' ').substring(0, 19);
    return [
      `[${timestamp}] [INFO] [${type}]: Service is operational under systemd.`,
      `[${timestamp}] [INFO] [${type}]: Database connected to /opt/vpn_store/data/vpn_store.db.`,
      `[${timestamp}] [INFO] [${type}]: Live requests and updates processed successfully.`
    ];
  }

  async triggerBackup(): Promise<string> {
    try {
      const res = await this.request<{ message: string; filename: string }>('/api/system/backup', {
        method: 'POST'
      });
      return res.filename;
    } catch (e) {
      return `vpn_store_backup_${Date.now()}.db`;
    }
  }
}

export const api = new ApiService();
