interface LoadingSpinnerProps {
  size?: "sm" | "md" | "lg";
  text?: string;
}

export default function LoadingSpinner({
  size = "md",
  text,
}: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: "h-6 w-6",
    md: "h-12 w-12",
    lg: "h-16 w-16",
  };

  return (
    <div className="flex flex-col items-center justify-center py-12 animate-fade-in">
      <div className={`spinner ${sizeClasses[size]} border-primary-600 mb-4`} />
      {text && <p className="text-gray-600 font-medium">{text}</p>}
    </div>
  );
}
