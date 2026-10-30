import React, { useState, useEffect } from 'react';
import { Terminal, Download, RefreshCw, HardDrive, CheckCircle2 } from 'lucide-react';
import { api } from '../../services/api';

interface LogsTabProps {
  onTriggerBackup: () => Promise<string>;
  isRtl: boolean;
}

export const LogsTab: React.FC<LogsTabProps> = ({ onTriggerBackup, isRtl }) => {
  const [logType, setLogType] = useState<'web' | 'bot' | 'worker'>('web');
  const [logLines, setLogLines] = useState<string[]>([]);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [backupLoading, setBackupLoading] = useState(false);
  const [backupSuccessMsg, setBackupSuccessMsg] = useState('');

  const fetchLogs = async () => {
    setLoadingLogs(true);
    try {
      const lines = await api.getLogs(logType);
      setLogLines(lines);
    } catch {
      setLogLines(['خطا در دریافت فایل لاگ.']);
    } finally {
      setLoadingLogs(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [logType]);

  const handleBackup = async () => {
    setBackupLoading(true);
    try {
      const filename = await onTriggerBackup();
      setBackupSuccessMsg(filename);
      setTimeout(() => setBackupSuccessMsg(''), 4000);
    } finally {
      setBackupLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-neutral-800">
        <div>
          <h1 className="text-lg font-bold text-neutral-100 flex items-center gap-2">
            <Terminal className="w-5 h-5 text-cyan-400" />
            <span>{isRtl ? 'لاگ‌های زنده و پشتیبان‌گیری (Logs & Backups)' : 'Live Logs & Database Backups'}</span>
          </h1>
          <p className="text-xs text-neutral-400 mt-0.5">
            {isRtl
              ? 'مشاهده لاگ‌های زنده وب‌سرور، ربات تلگرام و دانلود فایل پشتیبان دیتابیس SQLite بدون نیاز به SSH'
              : 'Audit system logs and download instant SQLite database dumps'}
          </p>
        </div>

        <button
          onClick={handleBackup}
          disabled={backupLoading}
          className="flex items-center gap-2 py-2 px-4 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-xl transition-all shadow-md active:scale-[0.98]"
        >
          <HardDrive className={`w-3.5 h-3.5 ${backupLoading ? 'animate-spin' : ''}`} />
          <span>{backupLoading ? (isRtl ? 'در حال پشتیبان‌گیری...' : 'Backing up...') : (isRtl ? 'پشتیبان‌گیری آنی از دیتابیس' : 'Backup Database Now')}</span>
        </button>
      </div>

      {backupSuccessMsg && (
        <div className="p-3.5 rounded-xl bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{isRtl ? `پشتیبان با موفقیت ایجاد شد: ${backupSuccessMsg}` : `Backup file ready: ${backupSuccessMsg}`}</span>
        </div>
      )}

      {/* Log Type Selector & Viewer */}
      <div className="bg-neutral-900/60 border border-neutral-800/80 rounded-2xl p-5 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-1.5 p-1 bg-neutral-950 border border-neutral-800 rounded-xl text-xs font-medium">
            <button
              onClick={() => setLogType('web')}
              className={`py-1.5 px-3 rounded-lg transition-colors ${
                logType === 'web' ? 'bg-neutral-800 text-cyan-400' : 'text-neutral-400 hover:text-neutral-200'
              }`}
            >
              {isRtl ? 'وب‌سرور و API' : 'Web & API'}
            </button>
            <button
              onClick={() => setLogType('bot')}
              className={`py-1.5 px-3 rounded-lg transition-colors ${
                logType === 'bot' ? 'bg-neutral-800 text-cyan-400' : 'text-neutral-400 hover:text-neutral-200'
              }`}
            >
              {isRtl ? 'ربات تلگرام' : 'Telegram Bot'}
            </button>
            <button
              onClick={() => setLogType('worker')}
              className={`py-1.5 px-3 rounded-lg transition-colors ${
                logType === 'worker' ? 'bg-neutral-800 text-cyan-400' : 'text-neutral-400 hover:text-neutral-200'
              }`}
            >
              {isRtl ? 'سینک ترافیک' : 'Traffic Sync'}
            </button>
          </div>

          <button
            onClick={fetchLogs}
            disabled={loadingLogs}
            className="flex items-center gap-1.5 py-1.5 px-3 text-xs bg-neutral-800 hover:bg-neutral-700 text-neutral-300 rounded-lg transition-colors border border-neutral-700/60"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loadingLogs ? 'animate-spin' : ''}`} />
            <span>{isRtl ? 'تازه‌سازی لاگ‌ها' : 'Refresh'}</span>
          </button>
        </div>

        {/* Terminal Window */}
        <div className="p-4 bg-neutral-950 border border-neutral-800 rounded-xl font-mono text-[11px] text-neutral-300 h-80 overflow-y-auto space-y-1.5 select-all">
          {logLines.map((line, idx) => (
            <div key={idx} className="leading-relaxed">
              {line.includes('[ERROR]') ? (
                <span className="text-rose-400">{line}</span>
              ) : line.includes('[WARN]') ? (
                <span className="text-amber-400">{line}</span>
              ) : (
                <span className="text-neutral-300">{line}</span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
