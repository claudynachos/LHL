'use client';

import { createContext, useContext, useState, ReactNode } from 'react';
import Modal from './Modal';

interface ModalContextType {
  showAlert: (message: string, title?: string) => Promise<void>;
  showConfirm: (message: string, title?: string) => Promise<boolean>;
}

const ModalContext = createContext<ModalContextType | undefined>(undefined);

export function ModalProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [modalProps, setModalProps] = useState<{
    title?: string;
    message: string;
    type: 'alert' | 'confirm';
    resolve?: (value?: boolean) => void;
  } | null>(null);

  const showAlert = (message: string, title?: string): Promise<void> => {
    return new Promise((resolve) => {
      setModalProps({
        title,
        message,
        type: 'alert',
        resolve: () => {
          resolve();
        },
      });
      setIsOpen(true);
    });
  };

  const showConfirm = (message: string, title?: string): Promise<boolean> => {
    return new Promise((resolve) => {
      setModalProps({
        title,
        message,
        type: 'confirm',
        resolve: (value: boolean) => {
          resolve(value);
        },
      });
      setIsOpen(true);
    });
  };

  const handleClose = () => {
    if (modalProps?.resolve) {
      if (modalProps.type === 'confirm') {
        modalProps.resolve(false);
      } else {
        modalProps.resolve();
      }
    }
    setIsOpen(false);
    setModalProps(null);
  };

  const handleConfirm = () => {
    if (modalProps?.resolve) {
      if (modalProps.type === 'confirm') {
        modalProps.resolve(true);
      } else {
        modalProps.resolve();
      }
    }
    setIsOpen(false);
    setModalProps(null);
  };

  return (
    <ModalContext.Provider value={{ showAlert, showConfirm }}>
      {children}
      {modalProps && (
        <Modal
          isOpen={isOpen}
          onClose={handleClose}
          title={modalProps.title}
          message={modalProps.message}
          type={modalProps.type}
          onConfirm={handleConfirm}
        />
      )}
    </ModalContext.Provider>
  );
}

export function useModal() {
  const context = useContext(ModalContext);
  if (context === undefined) {
    throw new Error('useModal must be used within a ModalProvider');
  }
  return context;
}
