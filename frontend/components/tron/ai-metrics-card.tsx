"use client"

import { useState, useEffect, memo, useMemo, useCallback } from "react"
import Link from "next/link"
import { Brain, AlertTriangle } from "lucide-react"
import { SkeletonAnalyticsCard, SkeletonMetric } from "@/components/ui/skeleton"
import { useApiError } from "@/components/error-context"
import apiClient from "@/lib/api-error-handler"

interface CognitiveSummary {
  thought_summary: {
    total_thoughts: number
  }
  memory_summary: {
    total_memories: number
    utilization_pct: number
  }
  system_status: {
    confidence_level: number
  }
}

const AIMetricsCard = memo(() => {
  const [data, setData] = useState<CognitiveSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { handleApiError } = useApiError()

  const fetchCognitiveSummary = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      
      const result = await apiClient.get<CognitiveSummary>('/api/cognitive/summary', {
        retry: {
          maxRetries: 2,
          retryDelay: 1000,
          exponentialBackoff: true,
          retryCondition: (error) => (error.status && error.status >= 500) || error.status === 0
        }
      })
      
      setData(result)
    } catch (e: any) {
      handleApiError(e, 'AI Metrics')
      setError('Failed to load AI metrics')
    } finally {
      setLoading(false)
    }
  }, [handleApiError])

  useEffect(() => {
    fetchCognitiveSummary()
  }, [fetchCognitiveSummary])

  const renderContent = useMemo(() => {
    if (loading) {
      return (
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <SkeletonAnalyticsCard />
            <SkeletonAnalyticsCard />
          </div>
          <div className="space-y-3">
            <SkeletonMetric />
            <SkeletonMetric />
          </div>
        </div>
      )
    }

    if (error || !data) {
      return (
        <div className="text-center py-8">
          <AlertTriangle className="w-8 h-8 text-amber-500 mx-auto mb-3" />
          <p className="text-sm text-amber-700 dark:text-amber-300 mb-3">
            Unable to load AI metrics
          </p>
          <button 
            onClick={fetchCognitiveSummary}
            className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200 font-medium transition-colors"
          >
            Try Again
          </button>
        </div>
      )
    }

    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-zinc-50 dark:bg-zinc-900/70 padding-card-sm rounded-lg border border-zinc-100 dark:border-zinc-800 shadow-card transition-smooth hover:bg-zinc-100 dark:hover:bg-zinc-900/90">
            <div className="text-heading-sm font-bold text-zinc-900 dark:text-zinc-100 mb-1">
              {data.thought_summary.total_thoughts.toLocaleString()}
            </div>
            <div className="text-caption text-zinc-600 dark:text-zinc-400">Total Thoughts</div>
          </div>
          <div className="bg-zinc-50 dark:bg-zinc-900/70 padding-card-sm rounded-lg border border-zinc-100 dark:border-zinc-800 shadow-card transition-smooth hover:bg-zinc-100 dark:hover:bg-zinc-900/90">
            <div className="text-heading-sm font-bold text-zinc-900 dark:text-zinc-100 mb-1">
              {data.memory_summary.total_memories.toLocaleString()}
            </div>
            <div className="text-caption text-zinc-600 dark:text-zinc-400">Total Memories</div>
          </div>
        </div>

        <div className="space-y-3">
          <div>
            <div className="flex items-center justify-between text-caption mb-2">
              <span className="text-zinc-600 dark:text-zinc-400">Memory Utilization</span>
              <span className="text-zinc-900 dark:text-zinc-100 font-medium">{data.memory_summary.utilization_pct.toFixed(1)}%</span>
            </div>
            <div className="h-2 bg-zinc-100 dark:bg-zinc-800 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-blue-500 to-blue-600 dark:from-blue-400 dark:to-blue-500 rounded-full transition-all duration-700 ease-out" 
                style={{ width: `${Math.min(data.memory_summary.utilization_pct, 100)}%` }} 
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between text-caption mb-2">
              <span className="text-zinc-600 dark:text-zinc-400">Confidence Level</span>
              <span className="text-zinc-900 dark:text-zinc-100 font-medium">{data.system_status.confidence_level.toFixed(1)}%</span>
            </div>
            <div className="h-2 bg-zinc-100 dark:bg-zinc-800 rounded-full overflow-hidden">
              <div 
                className="h-full bg-gradient-to-r from-purple-500 to-purple-600 dark:from-purple-400 dark:to-purple-500 rounded-full transition-all duration-700 ease-out" 
                style={{ width: `${Math.min(data.system_status.confidence_level, 100)}%` }} 
              />
            </div>
          </div>
        </div>
      </div>
    )
  }, [loading, error, data, fetchCognitiveSummary])

  return (
    <Link href="/cognitive/insights">
      <div className="bg-white dark:bg-[#0F0F12] rounded-xl padding-card flex flex-col border border-gray-200 dark:border-[#1F1F23] h-full shadow-card transition-smooth hover:shadow-card-hover">
        <h2 className="text-heading-md text-gray-900 dark:text-white mb-6 text-left flex items-center gap-3">
          <Brain className="w-4 h-4 text-zinc-900 dark:text-zinc-50" />
          AI Thought & Memory
        </h2>
        <div className="flex-grow">
          {renderContent}
        </div>
      </div>
    </Link>
  )
})

AIMetricsCard.displayName = 'AIMetricsCard'

export default AIMetricsCard
