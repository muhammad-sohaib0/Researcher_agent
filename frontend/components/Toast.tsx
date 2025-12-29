"use client";

import React, { useEffect, useState, useCallback } from "react";
import styles from "./Toast.module.css";

export type ToastType = "success" | "error" | "info" | "warning";

export interface ToastProps {
  id: number;
  type: ToastType;
  message: string;
  duration?: number;
  onClose: (id: number) => void;
}

const Toast: React.FC<ToastProps> = ({
  id,
  type,
  message,
  duration = 5000,
  onClose,
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isExiting, setIsExiting] = useState(false);

  useEffect(() => {
    // Trigger enter animation
    const timer = setTimeout(() => setIsVisible(true), 10);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    // Auto-dismiss
    if (duration > 0) {
      const timer = setTimeout(() => {
        handleClose();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [duration]);

  const handleClose = useCallback(() => {
    setIsExiting(true);
    setTimeout(() => onClose(id), 300);
  }, [id, onClose]);

  const getIcon = () => {
    switch (type) {
      case "success":
        return "✓";
      case "error":
        return "✕";
      case "warning":
        return "⚠";
      case "info":
        return "ℹ";
      default:
        return "ℹ";
    }
  };

  return (
    <div
      className={`
        ${styles.toast}
        ${styles[type]}
        ${isVisible ? styles.visible : ""}
        ${isExiting ? styles.exiting : ""}
      `}
      role="alert"
      aria-live="polite"
    >
      <span className={styles.icon}>{getIcon()}</span>
      <span className={styles.message}>{message}</span>
      <button
        className={styles.closeBtn}
        onClick={handleClose}
        aria-label="Close notification"
      >
        ✕
      </button>
    </div>
  );
};

// Toast context for global access
interface ToastContextType {
  toasts: Array<{ id: number; type: ToastType; message: string; duration?: number }>;
  addToast: (message: string, type: ToastType, duration?: number) => void;
  removeToast: (id: number) => void;
  success: (message: string, duration?: number) => void;
  error: (message: string, duration?: number) => void;
  info: (message: string, duration?: number) => void;
  warning: (message: string, duration?: number) => void;
}

let toastId = 0;
let toastContext: ToastContextType | null = null;

const ToastContext = React.createContext<ToastContextType | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Array<{
    id: number;
    type: ToastType;
    message: string;
    duration?: number;
  }>>([]);

  const addToast = useCallback((message: string, type: ToastType, duration?: number) => {
    const id = ++toastId;
    setToasts((prev) => [...prev, { id, message, type, duration }]);
  }, []);

  const removeToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const success = useCallback((message: string, duration?: number) => {
    addToast(message, "success", duration);
  }, [addToast]);

  const error = useCallback((message: string, duration?: number) => {
    addToast(message, "error", duration);
  }, [addToast]);

  const info = useCallback((message: string, duration?: number) => {
    addToast(message, "info", duration);
  }, [addToast]);

  const warning = useCallback((message: string, duration?: number) => {
    addToast(message, "warning", duration);
  }, [addToast]);

  const contextValue: ToastContextType = {
    toasts,
    addToast,
    removeToast,
    success,
    error,
    info,
    warning,
  };

  toastContext = contextValue;

  return (
    <ToastContext.Provider value={contextValue}>
      {children}
      <div className={styles.container}>
        {toasts.map((toast) => (
          <Toast
            key={toast.id}
            id={toast.id}
            type={toast.type}
            message={toast.message}
            duration={toast.duration}
            onClose={removeToast}
          />
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  if (!toastContext) {
    console.warn("useToast used outside ToastProvider");
    return {
      toasts: [],
      addToast: () => {},
      removeToast: () => {},
      success: () => {},
      error: () => {},
      info: () => {},
      warning: () => {},
    };
  }
  return toastContext;
}

// Convenience function to show toast from anywhere
export function showToast(message: string, type: ToastType = "info", duration?: number) {
  if (toastContext) {
    toastContext.addToast(message, type, duration);
  }
}

export function showSuccess(message: string, duration?: number) {
  showToast(message, "success", duration);
}

export function showError(message: string, duration?: number) {
  showToast(message, "error", duration);
}

export function showInfo(message: string, duration?: number) {
  showToast(message, "info", duration);
}

export function showWarning(message: string, duration?: number) {
  showToast(message, "warning", duration);
}

export default Toast;
