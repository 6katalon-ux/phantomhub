import React, { useState } from 'react';
import { Bell, Send, CheckCircle2 } from 'lucide-react';

interface NotificationsTabProps {
  onSendBroadcast: (title: string, message: string) => Promise<void>;
  isRtl: boolean;
}

export const NotificationsTab: React.FC<NotificationsTabProps> = ({ onSendBroadcast, isRtl }) => {
  const [title, setTitle] = useState('');
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [sentSuccess, setSentSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message) return;
    setSending(true);
    await onSendBroadcast(title, message);
    setSending(false);
    setSentSuccess(true);
    setTimeout(() => setSentSuccess(false), 3000);
    setTitle('');
    setMessage('');
  };

  return (
    <div className="space-y-6">
      <div className="pb-4 border-b border-neutral-800">
        <h1 className="text-lg font-bold text-neutral-100 flex items-center gap-2">
          <Bell className="w-5 h-5 text-cyan-400" />
          <span>{isRtl ? 'ارسال اعلان همگانی در تلگرام (Broadcast)' : 'Telegram Broadcast Announcements'}</span>
        </h1>
        <p className="text-xs text-neutral-400 mt-0.5">
          {isRtl
            ? 'ارسال پیام اطلاع‌رسانی، اخبار سرور، تخفیف‌ها یا تغییر آدرس کانفیگ به کلیه اعضای ربات'
            : 'Broadcast mass announcements to all registered Telegram subscribers'}
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <form onSubmit={handleSubmit} className="lg:col-span-2 space-y-4">
          <div className="bg-neutral-900/60 border border-neutral-800/80 rounded-2xl p-5 space-y-4">
            <div>
              <label className="block text-xs font-semibold text-neutral-200 mb-1.5">
                {isRtl ? 'موضوع اعلان (اختیاری):' : 'Announcement Subject:'}
              </label>
              <input
                type="text"
                value={title}
                onChange={e => setTitle(e.target.value)}
                placeholder="مثال: سرورهای جدید آلمان با پینگ عالی اضافه شدند 🚀"
                className="w-full px-3.5 py-2.5 bg-neutral-950 border border-neutral-800 rounded-xl text-xs text-neutral-200 focus:outline-none focus:border-cyan-500/60 transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-neutral-200 mb-1.5">
                {isRtl ? 'متن پیام اعلان:' : 'Message Content (Markdown supported):'}
              </label>
              <textarea
                rows={6}
                value={message}
                onChange={e => setMessage(e.target.value)}
                placeholder="سلام کاربران گرامی، به اطلاع می‌رساند جهت بهبود کیفیت اتصال..."
                className="w-full px-3.5 py-2.5 bg-neutral-950 border border-neutral-800 rounded-xl text-xs text-neutral-200 focus:outline-none focus:border-cyan-500/60 transition-colors"
                required
              />
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={sending || !message}
              className="flex items-center gap-2 py-2.5 px-6 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white text-xs font-semibold rounded-xl transition-all shadow-lg active:scale-[0.98]"
            >
              <Send className="w-4 h-4" />
              <span>{sending ? (isRtl ? 'در حال ارسال پیام‌ها...' : 'Sending...') : (isRtl ? 'ارسال فوری به تمام اعضا' : 'Send Broadcast')}</span>
            </button>
          </div>
        </form>

        {/* Telegram Message Preview Card */}
        <div className="space-y-2">
          <div className="text-xs font-semibold text-neutral-400">
            {isRtl ? 'پیش‌نمایش در تلگرام:' : 'Live Telegram Preview:'}
          </div>
          <div className="bg-[#18222d] border border-neutral-800 rounded-2xl p-4 shadow-xl space-y-2">
            <div className="flex items-center gap-2 text-cyan-400 text-xs font-bold">
              <span>VPN Store Bot</span>
            </div>
            {title && <div className="text-xs font-bold text-neutral-100">{title}</div>}
            <div className="text-xs text-neutral-200 leading-relaxed whitespace-pre-wrap font-sans">
              {message || (isRtl ? 'متن ارسالی شما در تلگرام به این صورت به کاربر نمایش داده خواهد شد...' : 'Your broadcast will appear here...')}
            </div>
            <div className="text-[10px] text-neutral-500 text-end">14:05</div>
          </div>
        </div>
      </div>
    </div>
  );
};
