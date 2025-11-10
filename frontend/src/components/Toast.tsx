import { X, CheckCircle, XCircle, AlertCircle, Info } from "lucide-react";
import { useEffect } from "react";

export type ToastType = "success" | "error" | "warning" | "info";

interface ToastProps {
  message: string;
  type: ToastType;
  onClose: () => void;
  duration?: number;
}

export default function Toast({
  message,
  type,
  onClose,
  duration = 5000,
}: ToastProps) {
  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(onClose, duration);
      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);

  const icons = {
    success: CheckCircle,
    error: XCircle,
    warning: AlertCircle,
    info: Info,
  };

  const Icon = icons[type];

  const styles = {
    success: "bg-success-50 border-success-200 text-success-800",
    error: "bg-danger-50 border-danger-200 text-danger-800",
    warning: "bg-warning-50 border-warning-200 text-warning-800",
    info: "bg-primary-50 border-primary-200 text-primary-800",
  };

  return (
    <div
      className={`flex items-center gap-3 p-4 rounded-lg border shadow-lg ${styles[type]} animate-slide-down`}
    >
      <Icon className="w-5 h-5 flex-shrink-0" />
      <p className="flex-1 text-sm font-medium">{message}</p>
      <button
        onClick={onClose}
        className="p-1 hover:bg-white/50 rounded transition-colors"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}
