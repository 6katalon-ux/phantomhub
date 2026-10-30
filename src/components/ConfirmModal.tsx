import React from 'react';
import { AlertTriangle, X } from 'lucide-react';

interface ConfirmModalProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  danger?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
  isRtl?: boolean;
}

export const ConfirmModal: React.FC<ConfirmModalProps> = ({
  isOpen,
  title,
  message,
  confirmText = 'تایید',
  cancelText = 'انصراف',
  danger = false,
  onConfirm,
  onCancel,
  isRtl = true
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div
        className="w-full max-w-sm bg-neutral-900 border border-neutral-800 rounded-2xl p-5 shadow-2xl relative text-neutral-100"
        dir={isRtl ? 'rtl' : 'ltr'}
      >
        <div className="flex items-start gap-3 mb-4">
          <div className={`p-2.5 rounded-xl ${danger ? 'bg-rose-500/10 text-rose-400' : 'bg-cyan-500/10 text-cyan-400'}`}>
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div className="flex-1">
            <h3 className="text-base font-semibold text-neutral-100 mb-1">{title}</h3>
            <p className="text-xs text-neutral-400 leading-relaxed">{message}</p>
          </div>
          <button
            onClick={onCancel}
            className="p-1 text-neutral-400 hover:text-neutral-200 rounded-lg hover:bg-neutral-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex items-center gap-2 pt-2 border-t border-neutral-800">
          <button
            onClick={onConfirm}
            className={`flex-1 py-2.5 px-4 text-xs font-semibold rounded-xl transition-all shadow-md active:scale-[0.98] ${
              danger
                ? 'bg-rose-600 hover:bg-rose-500 text-white shadow-rose-950/50'
                : 'bg-cyan-600 hover:bg-cyan-500 text-white shadow-cyan-950/50'
            }`}
          >
            {confirmText}
          </button>
          <button
            onClick={onCancel}
            className="py-2.5 px-4 bg-neutral-800 hover:bg-neutral-700 text-neutral-300 text-xs font-medium rounded-xl transition-colors"
          >
            {cancelText}
          </button>
        </div>
      </div>
    </div>
  );
};
