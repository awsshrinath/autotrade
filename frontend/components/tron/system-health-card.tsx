"use client"

import { useState, useEffect } from "react"
import { Gauge, Loader2 } from "lucide-react"

interface SystemMetrics {
  cpu_usage_pct: number
  memory_usage_pct: number
  disk_usage_pct: number
  api_response_time_ms: number
}

export default function SystemHealthCard() {
  const [data, setData] = useState<SystemMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchSystemMetrics = async () => {
      try {
        setLoading(true)
        const response = await fetch("http://localhost:8000/api/system/metrics")
        if (!response.ok) {
          throw new Error("Network response was not ok")
        }
        const result: SystemMetrics = await response.json()
        setData(result)
      } catch (e: any) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    }

    fetchSystemMetrics()
  }, [])

  const MetricBar = ({ label, value, colorClass }: { label: string, value: number, colorClass: string }) => (
    <div>
      <div className="flex items-center justify-between text-xs mb-1">
        <span className="text-zinc-600 dark:text-zinc-400">{label}</span>
        <span className="text-zinc-900 dark:text-zinc-100">{value.toFixed(1)}%</span>
      </div>
      <div className="h-2 bg-zinc-100 dark:bg-zinc-800 rounded-full overflow-hidden">
        <div className={`h-full ${colorClass} rounded-full`} style={{ width: `${value}%` }} />
      </div>
    </div>
  )

  const renderContent = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-full">
          <Loader2 className="w-6 h-6 animate-spin text-zinc-500" />
        </div>
      )
    }

    if (error || !data) {
      return (
        <div className="text-center text-red-500">
          <p>Error loading system metrics.</p>
          <p className="text-xs">{error}</p>
        </div>
      )
    }

    return (
      <div className="space-y-3">
        <MetricBar label="CPU Usage" value={data.cpu_usage_pct} colorClass="bg-blue-500" />
        <MetricBar label="Memory Usage" value={data.memory_usage_pct} colorClass="bg-purple-500" />
        <MetricBar label="Disk Usage" value={data.disk_usage_pct} colorClass="bg-amber-500" />
        <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-800">
             <div className="flex items-center justify-between">
                <span className="text-xs text-zinc-600 dark:text-zinc-400">API Response Time</span>
                <span className="text-xs font-medium text-zinc-900 dark:text-zinc-100">{data.api_response_time_ms} ms</span>
            </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-[#0F0F12] rounded-xl p-6 flex flex-col border border-gray-200 dark:border-[#1F1F23]">
      <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4 text-left flex items-center gap-2">
        <Gauge className="w-3.5 h-3.5 text-zinc-900 dark:text-zinc-50" />
        System Resource Usage
      </h2>
      <div className="flex-grow">
        {renderContent()}
      </div>
    </div>
  )
}
