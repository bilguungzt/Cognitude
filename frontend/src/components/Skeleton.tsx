interface SkeletonProps {
  className?: string;
  variant?: "text" | "circular" | "rectangular";
}

export default function Skeleton({
  className = "",
  variant = "rectangular",
}: SkeletonProps) {
  const variantClasses = {
    text: "h-4 rounded",
    circular: "rounded-full",
    rectangular: "rounded-lg",
  };

  return <div className={`skeleton ${variantClasses[variant]} ${className}`} />;
}

export function SkeletonCard() {
  return (
    <div className="card animate-pulse">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <Skeleton className="h-6 w-3/4 mb-2" />
          <Skeleton className="h-4 w-1/2" />
        </div>
        <Skeleton variant="circular" className="h-10 w-10" />
      </div>
      <div className="space-y-2">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-5/6" />
        <Skeleton className="h-4 w-4/6" />
      </div>
      <div className="flex gap-2 mt-4">
        <Skeleton className="h-8 w-24" />
        <Skeleton className="h-8 w-24" />
      </div>
    </div>
  );
}
