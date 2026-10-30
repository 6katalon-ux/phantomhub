import React from 'react';
import { AlertCircle, CheckCircle2, Info, X } from 'lucide-react';

export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'info';
  message: string;
}

interface ToastContainerProps {
  toasts: ToastMessage[];
  onDismiss: (id: string) => void;
  isRtl?: boolean;
}

export const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, onDismiss, isRtl = true }) => {
  if (toasts.length === 0) return null;

  return (
    <div 
      className="fixed bottom-16 sm:bottom-6 z-50 flex flex-col gap-2 max-w-sm w-full px-4 pointer-events-none left-1/2 -translate-x-1/2 sm:left-auto sm:right-6 sm:translate-x-0"
      dir={isRtl ? 'rtl' : 'ltr'}
    >
      {toasts.map(t => (
        <div
          key={t.id}
          className={`pointer-events-auto flex items-center justify-between gap-3 p-3.5 rounded-xl border shadow-xl text-sm transition-all duration-200 animate-in slide-in-from-bottom-2 ${
            t.type === 'success'
              ? 'bg-neutral-900 border-emerald-500/40 text-emerald-300'
              : t.type === 'error'
              ? 'bg-neutral-900 border-rose-500/40 text-rose-300'
              : 'bg-neutral-900 border-cyan-500/40 text-cyan-300'
          }`}
        >
          <div className="flex items-center gap-2.5">
            {t.type === 'success' && <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />}
            {t.type === 'error' && <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />}
            {t.type === 'info' && <Info className="w-4 h-4 shrink-0 text-cyan-400" />}
            <span className="font-medium text-neutral-200 leading-snug">{t.message}</span>
          </div>
          <button
            onClick={() => onDismiss(t.id)}
            className="p-1 text-neutral-400 hover:text-neutral-200 rounded-lg hover:bg-neutral-800 transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      ))}
    </div>
  );
};
