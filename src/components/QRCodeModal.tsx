import React, { useEffect, useState } from 'react';
import QRCode from 'qrcode';
import { Copy, Check, X, QrCode } from 'lucide-react';

interface QRCodeModalProps {
  isOpen: boolean;
  onClose: () => void;
  configLink: string;
  title?: string;
  isRtl?: boolean;
}

export const QRCodeModal: React.FC<QRCodeModalProps> = ({
  isOpen,
  onClose,
  configLink,
  title,
  isRtl = true
}) => {
  const [qrDataUrl, setQrDataUrl] = useState<string>('');
  const [copied, setCopied] = useState<boolean>(false);

  useEffect(() => {
    if (configLink && isOpen) {
      QRCode.toDataURL(configLink, {
        width: 320,
        margin: 2,
        color: {
          dark: '#000000',
          light: '#ffffff'
        }
      })
        .then(url => setQrDataUrl(url))
        .catch(err => console.error('QR code generation error:', err));
    }
  }, [configLink, isOpen]);

  if (!isOpen) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(configLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div 
        className="w-full max-w-sm bg-neutral-900 border border-neutral-800 rounded-2xl p-5 shadow-2xl relative text-neutral-100"
        dir={isRtl ? 'rtl' : 'ltr'}
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-neutral-800 mb-4">
          <div className="flex items-center gap-2">
            <QrCode className="w-5 h-5 text-cyan-400" />
            <h3 className="text-base font-semibold text-neutral-100">
              {title || (isRtl ? 'اسکن بارکد و کپی کانفیگ' : 'Scan QR & Copy Config')}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800 rounded-lg transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* QR Canvas Container */}
        <div className="flex flex-col items-center justify-center bg-white p-3 rounded-xl shadow-inner mb-4">
          {qrDataUrl ? (
            <img 
              src={qrDataUrl} 
              alt="VPN Config QR Code" 
              className="w-56 h-56 rounded-md object-contain"
            />
          ) : (
            <div className="w-56 h-56 flex items-center justify-center text-neutral-400 text-sm">
              {isRtl ? 'در حال تولید بارکد...' : 'Generating QR code...'}
            </div>
          )}
        </div>

        {/* Config Link Raw Box */}
        <div className="mb-4">
          <label className="block text-xs text-neutral-400 mb-1.5 font-medium">
            {isRtl ? 'لینک کانکشن مستقیم:' : 'Direct Connection String:'}
          </label>
          <div className="p-2.5 bg-neutral-950 border border-neutral-800 rounded-lg font-mono text-xs text-neutral-300 break-all max-h-24 overflow-y-auto select-all">
            {configLink}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleCopy}
            className="flex-1 flex items-center justify-center gap-2 py-2.5 px-4 bg-cyan-600 hover:bg-cyan-500 text-white text-sm font-medium rounded-xl transition-all shadow-lg shadow-cyan-950/50 active:scale-[0.98]"
          >
            {copied ? (
              <>
                <Check className="w-4 h-4 text-emerald-300" />
                <span>{isRtl ? 'کانفیگ کپی شد!' : 'Copied!'}</span>
              </>
            ) : (
              <>
                <Copy className="w-4 h-4" />
                <span>{isRtl ? 'کپی کانفیگ' : 'Copy Config'}</span>
              </>
            )}
          </button>

          <button
            onClick={onClose}
            className="py-2.5 px-4 bg-neutral-800 hover:bg-neutral-700 text-neutral-300 text-sm font-medium rounded-xl transition-colors"
          >
            {isRtl ? 'بستن' : 'Close'}
          </button>
        </div>
      </div>
    </div>
  );
};
