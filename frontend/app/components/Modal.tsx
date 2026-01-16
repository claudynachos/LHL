'use client';

import { useEffect } from 'react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  message: string;
  type?: 'alert' | 'confirm';
  onConfirm?: () => void;
  confirmText?: string;
  cancelText?: string;
}

export default function Modal({
  isOpen,
  onClose,
  title,
  message,
  type = 'alert',
  onConfirm,
  confirmText = 'OK',
  cancelText = 'Cancel',
}: ModalProps) {
  useEffect(() => {
    if (isOpen) {
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleConfirm = () => {
    if (onConfirm) {
      onConfirm();
    }
    onClose();
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />

      {/* Modal */}
      <div
        className="relative bg-dark-card rounded-xl shadow-card-hover border border-dark-border p-6 w-full max-w-md"
        onClick={(e) => e.stopPropagation()}
      >
        {title && (
          <h3 className="text-xl font-bold text-dark-text mb-4">{title}</h3>
        )}
        
        <p className="text-dark-text mb-6">{message}</p>

        <div className="flex gap-3 justify-end">
          {type === 'confirm' && (
            <button
              onClick={onClose}
              className="btn btn-secondary"
            >
              {cancelText}
            </button>
          )}
          <button
            onClick={handleConfirm}
            className="btn btn-primary"
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  );
}
