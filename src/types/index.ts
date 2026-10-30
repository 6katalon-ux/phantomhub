export type TabType =
  | 'dashboard'
  | 'bot_settings'
  | 'xui_connection'
  | 'inbounds'
  | 'plans'
  | 'users'
  | 'services'
  | 'wallet'
  | 'gift_codes'
  | 'free_trial'
  | 'payment_settings'
  | 'transactions'
  | 'notifications'
  | 'system_settings'
  | 'logs_backups';

export type Language = 'fa' | 'en';

export interface AdminUser {
  id: number;
  username: string;
  role: string;
  created_at: string;
}

export interface UserItem {
  id: number;
  telegram_id: number;
  username: string;
  first_name: string;
  last_name: string;
  wallet_balance: number;
  trial_used: boolean;
  is_blocked: boolean;
  created_at: string;
  services_count?: number;
}

export interface PlanItem {
  id: number;
  name: string;
  description: string;
  price: number;
  traffic_gb: number;
  duration_days: number;
  inbound_id: number;
  protocol: 'vless' | 'vmess' | 'trojan';
  max_ips: number;
  is_active: boolean;
  sort_order: number;
}

export interface ServiceItem {
  id: number;
  user_id: number;
  telegram_id: number;
  plan_id: number | null;
  protocol: string;
  inbound_id: number;
  client_uuid: string;
  client_email: string;
  config_link: string;
  sub_token: string;
  total_traffic_bytes: number;
  used_traffic_bytes: number;
  expire_time_ms: number;
  is_active: boolean;
  created_at: string;
}

export interface PaymentItem {
  id: number;
  user_id: number;
  username?: string;
  amount: number;
  method: string;
  reference_id: string;
  receipt_note: string;
  status: 'pending' | 'approved' | 'rejected';
  admin_note?: string;
  created_at: string;
  reviewed_at?: string;
}

export interface GiftCodeItem {
  id: number;
  code: string;
  amount: number;
  max_redemptions: number;
  redeemed_count: number;
  expire_at: string | null;
  is_active: boolean;
  created_at: string;
}

export interface InboundItem {
  id: number;
  inbound_id: number;
  remark: string;
  protocol: string;
  port: number;
  network: string;
  security: string;
  total_clients: number;
  is_enabled: boolean;
  reality_sni?: string;
}

export interface TransactionItem {
  id: number;
  user_id: number;
  amount: number;
  balance_after: number;
  type: 'topup' | 'purchase' | 'refund' | 'admin_adjustment';
  description: string;
  created_at: string;
}

export interface AppSettings {
  // Bot Settings
  bot_token: string;
  bot_admin_ids: string;
  bot_enabled: boolean;
  bot_welcome_msg: string;
  bot_support_username: string;
  bot_maintenance: boolean;
  
  // 3X-UI Settings
  xui_url: string;
  xui_username: string;
  xui_password: string;
  xui_token: string;
  xui_tls_verify: boolean;
  xui_timeout: number;
  xui_default_inbound: number;
  vpn_server_host: string;
  
  // Free Trial
  trial_enabled: boolean;
  trial_traffic_gb: number;
  trial_duration_days: number;
  trial_inbound_id: number;
  
  // General & Payment
  site_name: string;
  currency: string;
  card_number: string;
  card_holder: string;
  crypto_wallet: string;
  payment_instructions: string;
  sync_interval_mins: number;
  backup_retention_days: number;
}
