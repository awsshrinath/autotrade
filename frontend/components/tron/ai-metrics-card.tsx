"use client"

import { useState, useEffect } from "react"
import { Brain, Loader2 } from "lucide-react"

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

export default function AIMetricsCard() {
  const [data, setData] = useState<CognitiveSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchCognitiveSummary = async () => {
      try {
        setLoading(true)
        const response = await fetch("http://localhost:8000/api/cognitive/summary")
        if (!response.ok) {
          throw new Error("Network response was not ok")
        }
        const result: CognitiveSummary = await response.json()
        setData(result)
      } catch (e: any) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    }

    fetchCognitiveSummary()
  }, [])
  
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
          <p>Error loading AI metrics.</p>
          <p className="text-xs">{error}</p>
        </div>
      )
    }

    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-zinc-50 dark:bg-zinc-900/70 p-4 rounded-lg border border-zinc-100 dark:border-zinc-800">
            <div className="text-2xl font-bold text-zinc-900 dark:text-zinc-100 mb-1">
              {data.thought_summary.total_thoughts.toLocaleString()}
            </div>
            <div className="text-xs text-zinc-600 dark:text-zinc-400">Total Thoughts</div>
          </div>
          <div className="bg-zinc-50 dark:bg-zinc-900/70 p-4 rounded-lg border border-zinc-100 dark:border-zinc-800">
            <div className="text-2xl font-bold text-zinc-900 dark:text-zinc-100 mb-1">
              {data.memory_summary.total_memories.toLocaleString()}
            </div>
            <div className="text-xs text-zinc-600 dark:text-zinc-400">Total Memories</div>
          </div>
        </div>

        <div className="space-y-2">
          <div>
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-zinc-600 dark:text-zinc-400">Memory Utilization</span>
              <span className="text-zinc-900 dark:text-zinc-100">{data.memory_summary.utilization_pct.toFixed(1)}%</span>
            </div>
            <div className="h-1.5 bg-zinc-100 dark:bg-zinc-800 rounded-full overflow-hidden">
              <div className="h-full bg-blue-600 dark:bg-blue-400 rounded-full" style={{ width: `${data.memory_summary.utilization_pct}%` }} />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-zinc-600 dark:text-zinc-400">Confidence Level</span>
              <span className="text-zinc-900 dark:text-zinc-100">{data.system_status.confidence_level.toFixed(1)}%</span>
            </div>
            <div className="h-1.5 bg-zinc-100 dark:bg-zinc-800 rounded-full overflow-hidden">
              <div className="h-full bg-purple-600 dark:bg-purple-400 rounded-full" style={{ width: `${data.system_status.confidence_level}%` }} />
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-[#0F0F12] rounded-xl p-6 flex flex-col border border-gray-200 dark:border-[#1F1F23]">
      <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4 text-left flex items-center gap-2">
        <Brain className="w-3.5 h-3.5 text-zinc-900 dark:text-zinc-50" />
        AI Thought & Memory
      </h2>
      <div className="flex-grow">
        {renderContent()}
      </div>
    </div>
  )
}
