import { cn } from "@/lib/utils"

function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-zinc-100 dark:bg-zinc-800", className)}
      {...props}
    />
  )
}

function SkeletonCard() {
  return (
    <div className="bg-white dark:bg-[#0F0F12] rounded-xl padding-card border border-gray-200 dark:border-[#1F1F23] shadow-card">
      <div className="flex items-center gap-3 mb-6">
        <Skeleton className="h-4 w-4 rounded" />
        <Skeleton className="h-5 w-32" />
      </div>
      <div className="space-y-3">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
      </div>
    </div>
  )
}

function SkeletonAnalyticsCard() {
  return (
    <div className="bg-zinc-50 dark:bg-zinc-900/70 padding-card-sm rounded-lg border border-zinc-100 dark:border-zinc-800 shadow-card">
      <div className="flex items-center gap-3 mb-3">
        <Skeleton className="h-4 w-4 rounded" />
        <Skeleton className="h-4 w-24" />
      </div>
      <div className="space-y-2">
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-2/3" />
      </div>
    </div>
  )
}

function SkeletonButton() {
  return (
    <div className="bg-zinc-100 dark:bg-zinc-800 py-3 px-4 rounded-lg flex items-center justify-center gap-2 animate-pulse">
      <Skeleton className="h-4 w-4 rounded" />
      <Skeleton className="h-4 w-20" />
    </div>
  )
}

function SkeletonMetric() {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Skeleton className="h-3 w-16" />
        <Skeleton className="h-3 w-8" />
      </div>
      <Skeleton className="h-2 w-full rounded-full" />
    </div>
  )
}

// Enhanced comprehensive skeleton components

function SkeletonChart({ height = "h-64" }: { height?: string }) {
  return (
    <div className={cn("w-full", height, "relative")}>
      {/* Chart header */}
      <div className="flex items-center justify-between mb-4">
        <Skeleton className="h-5 w-32" />
        <div className="flex gap-2">
          <Skeleton className="h-8 w-16 rounded-md" />
          <Skeleton className="h-8 w-16 rounded-md" />
        </div>
      </div>
      
      {/* Chart area */}
      <div className="relative bg-white dark:bg-zinc-900/50 rounded-lg border border-zinc-200 dark:border-zinc-700 p-4">
        {/* Y-axis */}
        <div className="absolute left-0 top-4 bottom-4 w-8 flex flex-col justify-between">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-3 w-6" />
          ))}
        </div>
        
        {/* Chart bars/lines */}
        <div className="ml-12 h-full flex items-end justify-between gap-2">
          {Array.from({ length: 12 }).map((_, i) => (
            <Skeleton 
              key={i} 
              className={cn(
                "w-4 rounded-t",
                i % 3 === 0 ? "h-3/4" : i % 3 === 1 ? "h-1/2" : "h-2/3"
              )} 
            />
          ))}
        </div>
        
        {/* X-axis */}
        <div className="ml-12 mt-2 flex justify-between">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-3 w-8" />
          ))}
        </div>
      </div>
    </div>
  )
}

function SkeletonTable({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <div className="w-full border border-zinc-200 dark:border-zinc-700 rounded-lg overflow-hidden">
      {/* Table header */}
      <div className="bg-zinc-50 dark:bg-zinc-800/50 border-b border-zinc-200 dark:border-zinc-700">
        <div className="grid gap-4 p-4" style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}>
          {Array.from({ length: cols }).map((_, i) => (
            <Skeleton key={i} className="h-4 w-full" />
          ))}
        </div>
      </div>
      
      {/* Table rows */}
      <div className="divide-y divide-zinc-200 dark:divide-zinc-700">
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <div key={rowIndex} className="grid gap-4 p-4" style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}>
            {Array.from({ length: cols }).map((_, colIndex) => (
              <Skeleton 
                key={colIndex} 
                className={cn(
                  "h-4",
                  colIndex === 0 ? "w-3/4" : colIndex === cols - 1 ? "w-1/2" : "w-full"
                )} 
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}

function SkeletonList({ items = 5 }: { items?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: items }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 p-3 bg-white dark:bg-zinc-900/50 rounded-lg border border-zinc-200 dark:border-zinc-700">
          <Skeleton className="h-10 w-10 rounded-full flex-shrink-0" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-3 w-1/2" />
          </div>
          <Skeleton className="h-6 w-16 rounded-full" />
        </div>
      ))}
    </div>
  )
}

function SkeletonNavigation() {
  return (
    <div className="flex items-center gap-6">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="flex items-center gap-2">
          <Skeleton className="h-4 w-4 rounded" />
          <Skeleton className={cn("h-4", i === 0 ? "w-16" : i === 1 ? "w-20" : "w-12")} />
        </div>
      ))}
    </div>
  )
}

function SkeletonDashboard() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-32" />
        </div>
        <div className="flex gap-3">
          <Skeleton className="h-10 w-24 rounded-lg" />
          <Skeleton className="h-10 w-32 rounded-lg" />
        </div>
      </div>
      
      {/* Metrics grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <SkeletonAnalyticsCard key={i} />
        ))}
      </div>
      
      {/* Main content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <SkeletonChart height="h-80" />
        </div>
        <div>
          <SkeletonList items={6} />
        </div>
      </div>
    </div>
  )
}

function SkeletonDataGrid({ 
  title = true, 
  filters = true, 
  pagination = true 
}: { 
  title?: boolean; 
  filters?: boolean; 
  pagination?: boolean; 
}) {
  return (
    <div className="space-y-4">
      {title && (
        <div className="flex items-center justify-between">
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-9 w-32 rounded-lg" />
        </div>
      )}
      
      {filters && (
        <div className="flex gap-3">
          <Skeleton className="h-9 w-48 rounded-lg" />
          <Skeleton className="h-9 w-32 rounded-lg" />
          <Skeleton className="h-9 w-24 rounded-lg" />
        </div>
      )}
      
      <SkeletonTable rows={8} cols={5} />
      
      {pagination && (
        <div className="flex items-center justify-between">
          <Skeleton className="h-4 w-32" />
          <div className="flex gap-2">
            <Skeleton className="h-8 w-8 rounded" />
            <Skeleton className="h-8 w-8 rounded" />
            <Skeleton className="h-8 w-8 rounded" />
            <Skeleton className="h-8 w-8 rounded" />
            <Skeleton className="h-8 w-8 rounded" />
          </div>
        </div>
      )}
    </div>
  )
}

function SkeletonForm({ fields = 4 }: { fields?: number }) {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Skeleton className="h-6 w-32" />
        <Skeleton className="h-4 w-64" />
      </div>
      
      <div className="space-y-4">
        {Array.from({ length: fields }).map((_, i) => (
          <div key={i} className="space-y-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-10 w-full rounded-lg" />
          </div>
        ))}
      </div>
      
      <div className="flex gap-3">
        <Skeleton className="h-10 w-24 rounded-lg" />
        <Skeleton className="h-10 w-20 rounded-lg" />
      </div>
    </div>
  )
}

export { 
  Skeleton, 
  SkeletonCard, 
  SkeletonAnalyticsCard, 
  SkeletonButton, 
  SkeletonMetric,
  SkeletonChart,
  SkeletonTable,
  SkeletonList,
  SkeletonNavigation,
  SkeletonDashboard,
  SkeletonDataGrid,
  SkeletonForm
} 