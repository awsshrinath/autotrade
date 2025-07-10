"use client"

import { useState, useEffect, memo, useMemo, useCallback } from "react"
import Link from "next/link"
import { CheckCircle, Cpu, AlertTriangle, Loader2 } from "lucide-react"
import { SkeletonMetric } from "@/components/ui/skeleton"
import { useApiError } from "@/components/error-context"
import apiClient from "@/lib/api-error-handler"

interface ComponentStatus {
  name: string
  status: string
}

interface SystemStatus {
  status: string
  components: ComponentStatus[]
}

const SystemStatusCard = memo(() => {
  const [data, setData] = useState<SystemStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { handleApiError } = useApiError()

  const fetchSystemStatus = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const result = await apiClient.get<SystemStatus>('/api/system/health', {
        retry: {
          maxRetries: 2,
          retryDelay: 1000,
          exponentialBackoff: true,
          retryCondition: (error) => error.status >= 500 || error.status === 0
        }
      })
      
      setData(result)
    } catch (e: any) {
      handleApiError(e, 'System Status')
      setError('Failed to load system status')
    } finally {
      setLoading(false)
    }
  }, [handleApiError])

  useEffect(() => {
    fetchSystemStatus()
  }, [fetchSystemStatus])

  const StatusBadge = memo(({ status }: { status: string }) => {
    const isOnline = status.toLowerCase() === 'online' || status.toLowerCase() === 'active';
    return (
      <span className={`text-caption font-semibold ${
        isOnline 
        ? "text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20" 
        : "text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20"
      } px-2.5 py-1 rounded-full transition-smooth`}>
        {status}
      </span>
    )
  })
  StatusBadge.displayName = 'StatusBadge'

  const componentsList = useMemo(() => {
    if (!data?.components) return []
    
    return data.components.map((component) => (
      <div key={component.name} className="flex items-center justify-between group">
        <div className="flex items-center gap-3">
          <div className="p-1.5 rounded-lg bg-emerald-100 dark:bg-emerald-900/30 transition-smooth group-hover:bg-emerald-200 dark:group-hover:bg-emerald-900/50">
            <CheckCircle className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
          </div>
          <span className="text-body-sm font-medium text-zinc-900 dark:text-zinc-100">{component.name}</span>
        </div>
        <StatusBadge status={component.status} />
      </div>
    ))
  }, [data?.components])

  const renderContent = useMemo(() => {
    if (loading) {
      return (
        <div className="space-y-4">
          <SkeletonMetric />
          <SkeletonMetric />
          <SkeletonMetric />
          <SkeletonMetric />
          <SkeletonMetric />
        </div>
      )
    }

    if (error || !data) {
      return (
        <div className="text-center py-8">
          <AlertTriangle className="w-8 h-8 text-amber-500 mx-auto mb-3" />
          <p className="text-sm text-amber-700 dark:text-amber-300 mb-3">
            Unable to load system status
          </p>
          <button 
            onClick={fetchSystemStatus}
            className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200 font-medium transition-colors"
          >
            Try Again
          </button>
        </div>
      )
    }

    return (
      <div className="space-y-4">
        {componentsList}
      </div>
    )
  }, [loading, error, data, componentsList, fetchSystemStatus])
  
  return (
    <Link href="/system/health">
      <div className="bg-white dark:bg-[#0F0F12] rounded-xl padding-card flex flex-col border border-gray-200 dark:border-[#1F1F23] h-full shadow-card transition-smooth hover:shadow-card-hover">
      <h2 className="text-heading-md text-gray-900 dark:text-white mb-6 text-left flex items-center gap-3">
        <Cpu className="w-4 h-4 text-zinc-900 dark:text-zinc-50" />
        System Status
      </h2>
      <div className="flex-grow">
        {renderContent}
      </div>
    </div>
    </Link>
  )
})

SystemStatusCard.displayName = 'SystemStatusCard'

export default SystemStatusCard
