"use client"

import { useState, useEffect, memo, useCallback, useMemo } from "react"
import Link from "next/link"
import { Gauge, AlertTriangle } from "lucide-react"
import { SkeletonMetric } from "@/components/ui/skeleton"
import { useApiError } from "@/components/error-context"
import apiClient from "@/lib/api-error-handler"

interface SystemMetrics {
  cpu_usage_pct: number
  memory_usage_pct: number
  disk_usage_pct: number
  api_response_time_ms: number
}

// Memoized MetricBar component for performance optimization
const MetricBar = memo(({ label, value, colorClass }: { label: string, value: number, colorClass: string }) => (
  <div>
    <div className="flex items-center justify-between text-caption mb-2">
      <span className="text-zinc-600 dark:text-zinc-400">{label}</span>
      <span className="text-zinc-900 dark:text-zinc-100 font-medium">{value.toFixed(1)}%</span>
    </div>
    <div className="h-2 bg-zinc-100 dark:bg-zinc-800 rounded-full overflow-hidden">
      <div 
        className={`h-full ${colorClass} rounded-full transition-all duration-700 ease-out`} 
        style={{ width: `${Math.min(value, 100)}%` }} 
      />
    </div>
  </div>
))

MetricBar.displayName = 'MetricBar'

const SystemHealthCard = memo(() => {
  const [data, setData] = useState<SystemMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { handleApiError } = useApiError()

  const fetchSystemMetrics = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const result = await apiClient.get<SystemMetrics>('/api/system/metrics', {
        retry: {
          maxRetries: 2,
          retryDelay: 1000,
          exponentialBackoff: true,
          retryCondition: (error) => error.status >= 500 || error.status === 0
        }
      })
      
      setData(result)
    } catch (e: any) {
      handleApiError(e, 'System Metrics')
      setError('Failed to load system metrics')
    } finally {
      setLoading(false)
    }
  }, [handleApiError])

  useEffect(() => {
    fetchSystemMetrics()
  }, [fetchSystemMetrics])

  const renderContent = useMemo(() => {
    if (loading) {
      return (
        <div className="space-y-4">
          <SkeletonMetric />
          <SkeletonMetric />
          <SkeletonMetric />
          <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-800">
            <div className="flex items-center justify-between">
              <div className="h-3 w-24 bg-zinc-100 dark:bg-zinc-800 rounded animate-pulse"></div>
              <div className="h-3 w-12 bg-zinc-100 dark:bg-zinc-800 rounded animate-pulse"></div>
            </div>
          </div>
        </div>
      )
    }

    if (error || !data) {
      return (
        <div className="text-center py-8">
          <AlertTriangle className="w-8 h-8 text-amber-500 mx-auto mb-3" />
          <p className="text-sm text-amber-700 dark:text-amber-300 mb-3">
            Unable to load system metrics
          </p>
          <button 
            onClick={fetchSystemMetrics}
            className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200 font-medium transition-colors"
          >
            Try Again
          </button>
        </div>
      )
    }

    return (
      <div className="space-y-4">
        <MetricBar 
          label="CPU Usage" 
          value={data.cpu_usage_pct} 
          colorClass="bg-gradient-to-r from-blue-500 to-blue-600 dark:from-blue-400 dark:to-blue-500" 
        />
        <MetricBar 
          label="Memory Usage" 
          value={data.memory_usage_pct} 
          colorClass="bg-gradient-to-r from-purple-500 to-purple-600 dark:from-purple-400 dark:to-purple-500" 
        />
        <MetricBar 
          label="Disk Usage" 
          value={data.disk_usage_pct} 
          colorClass="bg-gradient-to-r from-amber-500 to-amber-600 dark:from-amber-400 dark:to-amber-500" 
        />
        <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-800">
          <div className="flex items-center justify-between">
            <span className="text-caption text-zinc-600 dark:text-zinc-400">API Response Time</span>
            <span className="text-caption font-medium text-zinc-900 dark:text-zinc-100">{data.api_response_time_ms} ms</span>
          </div>
        </div>
      </div>
    )
  }, [loading, error, data, fetchSystemMetrics])

  return (
    <Link href="/system/health">
      <div className="bg-white dark:bg-[#0F0F12] rounded-xl padding-card flex flex-col border border-gray-200 dark:border-[#1F1F23] h-full shadow-card transition-smooth hover:shadow-card-hover">
        <h2 className="text-heading-md text-gray-900 dark:text-white mb-6 text-left flex items-center gap-3">
          <Gauge className="w-4 h-4 text-zinc-900 dark:text-zinc-50" />
          System Resource Usage
        </h2>
        <div className="flex-grow">
          {renderContent}
        </div>
      </div>
    </Link>
  )
})

SystemHealthCard.displayName = 'SystemHealthCard'

export default SystemHealthCard
