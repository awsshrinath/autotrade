"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { CheckCircle, Cpu, AlertTriangle, Loader2 } from "lucide-react"

interface ComponentStatus {
  name: string
  status: string
}

interface SystemStatus {
  status: string
  components: ComponentStatus[]
}

export default function SystemStatusCard() {
  const [data, setData] = useState<SystemStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchSystemStatus = async () => {
      try {
        setLoading(true)
        const response = await fetch(`/api/system/health`)
        if (!response.ok) {
          throw new Error("Failed to fetch")
        }
        const result: SystemStatus = await response.json()
        setData(result)
      } catch (e: any) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    }

    fetchSystemStatus()
  }, [])

  const StatusBadge = ({ status }: { status: string }) => {
    const isOnline = status.toLowerCase() === 'online' || status.toLowerCase() === 'active';
    return (
      <span className={`text-xs font-medium ${
        isOnline 
        ? "text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20" 
        : "text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/20"
      } px-2 py-1 rounded-full`}>
        {status}
      </span>
    )
  }

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
          <p>Error loading system status.</p>
          <p className="text-xs">{error}</p>
        </div>
      )
    }

    return (
      <div className="space-y-4">
        {data.components.map((component) => (
            <div key={component.name} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div className="p-1.5 rounded-lg bg-emerald-100 dark:bg-emerald-900/30">
                        <CheckCircle className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                    </div>
                    <span className="text-sm font-medium text-zinc-900 dark:text-zinc-100">{component.name}</span>
                </div>
                <StatusBadge status={component.status} />
            </div>
        ))}
      </div>
    )
  }
  
  return (
    <Link href="/system/health">
      <div className="bg-white dark:bg-[#0F0F12] rounded-xl p-6 flex flex-col border border-gray-200 dark:border-[#1F1F23] h-full">
      <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4 text-left flex items-center gap-2">
        <Cpu className="w-3.5 h-3.5 text-zinc-900 dark:text-zinc-50" />
        System Status
      </h2>
      <div className="flex-grow">
        {renderContent()}
      </div>
    </div>
    </Link>
  )
}
