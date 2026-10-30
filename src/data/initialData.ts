import { AppSettings, InboundItem, PlanItem, UserItem, ServiceItem, PaymentItem, GiftCodeItem, TransactionItem } from '../types';

export const INITIAL_SETTINGS: AppSettings = {
  bot_token: "7123456789:AAHq_EXAMPLE_TOKEN_ABC123xyz",
  bot_admin_ids: "987654321, 123456789",
  bot_enabled: true,
  bot_welcome_msg: "سلام! به ربات رسمی خرید و مدیریت اشتراک خوش آمدید.\nبرای شروع، یکی از گزینه‌های زیر را انتخاب نمایید:",
  bot_support_username: "@vpn_store_support",
  bot_maintenance: false,

  xui_url: "http://127.0.0.1:2053",
  xui_username: "admin",
  xui_password: "admin_password_xyz",
  xui_token: "",
  xui_tls_verify: false,
  xui_timeout: 10,
  xui_default_inbound: 1,
  vpn_server_host: "185.190.140.25",

  trial_enabled: true,
  trial_traffic_gb: 1,
  trial_duration_days: 3,
  trial_inbound_id: 1,

  site_name: "VPN Store",
  currency: "تومان",
  card_number: "6037-9975-4321-8765",
  card_holder: "محمد رضایی",
  crypto_wallet: "USDT (TRC20): TXYZ987654321abcdeFGH12345",
  payment_instructions: "لطفاً پس از واریز به کارت بالا، شماره پیگیری یا اسکرین‌شات فیش را ارسال فرمایید تا کیف پول به طور آنی شارژ گردد.",
  sync_interval_mins: 5,
  backup_retention_days: 14
};

export const INITIAL_INBOUNDS: InboundItem[] = [
  {
    id: 1,
    inbound_id: 1,
    remark: "🇩🇪 Germany - VLESS Reality (TCP/Vision)",
    protocol: "vless",
    port: 443,
    network: "tcp",
    security: "reality",
    total_clients: 42,
    is_enabled: true,
    reality_sni: "speedtest.net"
  },
  {
    id: 2,
    inbound_id: 2,
    remark: "🇫🇮 Finland - VLESS Reality (gRPC/Vision)",
    protocol: "vless",
    port: 8443,
    network: "grpc",
    security: "reality",
    total_clients: 28,
    is_enabled: true,
    reality_sni: "zoom.us"
  },
  {
    id: 3,
    inbound_id: 3,
    remark: "🇳🇱 Netherlands - VMess (WebSocket/CDN)",
    protocol: "vmess",
    port: 2083,
    network: "ws",
    security: "tls",
    total_clients: 19,
    is_enabled: true
  },
  {
    id: 4,
    inbound_id: 4,
    remark: "🇹🇷 Turkey - Trojan (TLS/Direct)",
    protocol: "trojan",
    port: 4433,
    network: "tcp",
    security: "tls",
    total_clients: 11,
    is_enabled: true
  }
];

export const INITIAL_PLANS: PlanItem[] = [
  {
    id: 1,
    name: "اشتراک پایه — ۳۰ گیگابایت",
    description: "سرعت پایدار، مناسب وب‌گردی و اینستاگرام، ۲ کاربره",
    price: 120000,
    traffic_gb: 30,
    duration_days: 30,
    inbound_id: 1,
    protocol: "vless",
    max_ips: 2,
    is_active: true,
    sort_order: 1
  },
  {
    id: 2,
    name: "اشتراک نقره‌ای — ۶۰ گیگابایت",
    description: "محبوب‌ترین پلن، آی‌پی ثابت آلمان، پینگ زیر ۷۰، ۲ کاربره",
    price: 210000,
    traffic_gb: 60,
    duration_days: 30,
    inbound_id: 1,
    protocol: "vless",
    max_ips: 2,
    is_active: true,
    sort_order: 2
  },
  {
    id: 3,
    name: "اشتراک طلایی — ۱۰۰ گیگابایت",
    description: "ویژه استریم یوتیوب و دانلود پرسرعت، ۳ کاربر همزمان",
    price: 320000,
    traffic_gb: 100,
    duration_days: 30,
    inbound_id: 2,
    protocol: "vless",
    max_ips: 3,
    is_active: true,
    sort_order: 3
  },
  {
    id: 4,
    name: "اشتراک فصلی نامحدود — ۲۵۰ گیگابایت",
    description: "اعتبار ۹۰ روزه، دسترسی به تمام سرورها بدون محدودیت پینگ",
    price: 750000,
    traffic_gb: 250,
    duration_days: 90,
    inbound_id: 1,
    protocol: "vless",
    max_ips: 4,
    is_active: true,
    sort_order: 4
  }
];

export const INITIAL_USERS: UserItem[] = [
  {
    id: 1,
    telegram_id: 987654321,
    username: "alireza_dev",
    first_name: "علیرضا",
    last_name: "محمدی",
    wallet_balance: 450000,
    trial_used: true,
    is_blocked: false,
    created_at: "2026-03-15T11:20:00Z",
    services_count: 2
  },
  {
    id: 2,
    telegram_id: 876543210,
    username: "sara_k",
    first_name: "سارا",
    last_name: "کریمی",
    wallet_balance: 85000,
    trial_used: true,
    is_blocked: false,
    created_at: "2026-03-20T14:45:00Z",
    services_count: 1
  },
  {
    id: 3,
    telegram_id: 765432109,
    username: "omid_teh",
    first_name: "امید",
    last_name: "نظری",
    wallet_balance: 0,
    trial_used: false,
    is_blocked: false,
    created_at: "2026-04-01T09:10:00Z",
    services_count: 0
  },
  {
    id: 4,
    telegram_id: 654321098,
    username: "spammer_user",
    first_name: "کاربر",
    last_name: "مسدود",
    wallet_balance: 0,
    trial_used: true,
    is_blocked: true,
    created_at: "2026-04-05T18:00:00Z",
    services_count: 1
  }
];

export const INITIAL_SERVICES: ServiceItem[] = [
  {
    id: 101,
    user_id: 1,
    telegram_id: 987654321,
    plan_id: 2,
    protocol: "vless",
    inbound_id: 1,
    client_uuid: "f47ac10b-58cc-4372-a567-0e02b2c3d479",
    client_email: "u987654321_de1a",
    config_link: "vless://f47ac10b-58cc-4372-a567-0e02b2c3d479@185.190.140.25:443?security=reality&sni=speedtest.net&fp=chrome&pbk=1y7WfX9U8aN9Z2kLmOPqRstUvwXyz0123456789abc=&sid=7a8b9c&type=tcp&flow=xtls-rprx-vision#VPNStore-987654321-Silver",
    sub_token: "sub_token_sec_f47ac10b58cc",
    total_traffic_bytes: 60 * 1024 * 1024 * 1024,
    used_traffic_bytes: 28456123904, // ~26.5 GB
    expire_time_ms: Date.now() + 18 * 86400 * 1000,
    is_active: true,
    created_at: "2026-03-20T15:00:00Z"
  },
  {
    id: 102,
    user_id: 2,
    telegram_id: 876543210,
    plan_id: 1,
    protocol: "vless",
    inbound_id: 1,
    client_uuid: "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    client_email: "u876543210_88bc",
    config_link: "vless://9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d@185.190.140.25:443?security=reality&sni=speedtest.net&fp=chrome&pbk=1y7WfX9U8aN9Z2kLmOPqRstUvwXyz0123456789abc=&sid=7a8b9c&type=tcp&flow=xtls-rprx-vision#VPNStore-876543210-Base",
    sub_token: "sub_token_sec_9b1deb4d3b7d",
    total_traffic_bytes: 30 * 1024 * 1024 * 1024,
    used_traffic_bytes: 31200000000, // Exceeded
    expire_time_ms: Date.now() - 2 * 86400 * 1000,
    is_active: false,
    created_at: "2026-03-01T10:00:00Z"
  }
];

export const INITIAL_PAYMENTS: PaymentItem[] = [
  {
    id: 201,
    user_id: 1,
    username: "alireza_dev",
    amount: 500000,
    method: "card",
    reference_id: "REF-99214710",
    receipt_note: "واریز از کارت بانک سامان ساعت ۱۴:۳۰ به کارت مقصد",
    status: "approved",
    admin_note: "تایید واریزی سامان",
    created_at: "2026-03-15T14:35:00Z",
    reviewed_at: "2026-03-15T14:40:00Z"
  },
  {
    id: 202,
    user_id: 3,
    username: "omid_teh",
    amount: 210000,
    method: "card",
    reference_id: "TRX-448201",
    receipt_note: "فیش شماره ۱۸۵۲ بانک ملت برای پلن ۶۰ گیگ",
    status: "pending",
    created_at: "2026-04-10T08:15:00Z"
  }
];

export const INITIAL_GIFT_CODES: GiftCodeItem[] = [
  {
    id: 1,
    code: "NOWRUZ1405",
    amount: 50000,
    max_redemptions: 100,
    redeemed_count: 34,
    expire_at: "2026-05-01T00:00:00Z",
    is_active: true,
    created_at: "2026-03-20T00:00:00Z"
  },
  {
    id: 2,
    code: "WELCOME20",
    amount: 20000,
    max_redemptions: 500,
    redeemed_count: 142,
    expire_at: null,
    is_active: true,
    created_at: "2026-01-01T00:00:00Z"
  }
];

export const INITIAL_TRANSACTIONS: TransactionItem[] = [
  {
    id: 501,
    user_id: 1,
    amount: 500000,
    balance_after: 500000,
    type: "topup",
    description: "شارژ کیف پول از طریق تایید فیش واریزی #201",
    created_at: "2026-03-15T14:40:00Z"
  },
  {
    id: 502,
    user_id: 1,
    amount: -210000,
    balance_after: 290000,
    type: "purchase",
    description: "خرید پلن اشتراک نقره‌ای — ۶۰ گیگابایت",
    created_at: "2026-03-15T14:42:00Z"
  }
];
