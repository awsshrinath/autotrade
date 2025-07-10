"use client"

import { useState, useEffect, memo, useCallback, useMemo } from "react"
import { useRouter } from "next/navigation"
import { Activity, Brain, Cpu, LineChart, Shield, BarChart2, Loader2 } from "lucide-react"
import SystemStatusCard from "./system-status-card"
import AIMetricsCard from "./ai-metrics-card"
import SystemHealthCard from "./system-health-card"
import { SkeletonCard, SkeletonAnalyticsCard, SkeletonButton } from "@/components/ui/skeleton"
import { ComponentErrorBoundary } from "@/components/error-boundary"

// --- Data Interfaces ---
interface PnlSummary {
  total_pnl: number
  win_rate: number
}
interface RiskSummary {
  total_exposure: number
  margin_usage_pct: number
}
interface StrategySummary {
  top_strategy: { name: string }
  active_strategies: number
}

const Content = memo(() => {
  const router = useRouter()
  const [pnlData, setPnlData] = useState<PnlSummary | null>(null)
  const [riskData, setRiskData] = useState<RiskSummary | null>(null)
  const [strategyData, setStrategyData] = useState<StrategySummary | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      const [pnlRes, riskRes, strategyRes] = await Promise.all([
        fetch("/api/trade/summary/daily"),
        fetch("/api/trade/summary/positions"),
        fetch("/api/trade/summary/strategy"),
      ])
      
      if (!pnlRes.ok || !riskRes.ok || !strategyRes.ok) {
          throw new Error("Failed to fetch analytics data")
      }

      const pnl = await pnlRes.json()
      const risk = await riskRes.json()
      const strategy = await strategyRes.json()

      setPnlData(pnl)
      setRiskData(risk)
      setStrategyData(strategy)

    } catch (error) {
      console.error("Error fetching analytics data:", error)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
  }, [fetchData])


  return (
    <div className="space-content">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <ComponentErrorBoundary>
          <SystemStatusCard />
        </ComponentErrorBoundary>
        <ComponentErrorBoundary>
          <AIMetricsCard />
        </ComponentErrorBoundary>
        <ComponentErrorBoundary>
          <SystemHealthCard />
        </ComponentErrorBoundary>
      </div>

      <ComponentErrorBoundary>
        <div className="bg-white dark:bg-[#0F0F12] rounded-xl padding-card flex flex-col border border-gray-200 dark:border-[#1F1F23] shadow-card transition-smooth hover:shadow-card-hover">
          <h2 className="text-heading-md text-gray-900 dark:text-white mb-6 text-left flex items-center gap-3">
            <LineChart className="w-4 h-4 text-zinc-900 dark:text-zinc-50" />
            Analytics Overview
          </h2>
          {loading ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
                  <SkeletonAnalyticsCard />
                  <SkeletonAnalyticsCard />
                  <SkeletonAnalyticsCard />
              </div>
          ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
              <div className="bg-zinc-50 dark:bg-zinc-900/70 padding-card-sm rounded-lg border border-zinc-100 dark:border-zinc-800 shadow-card transition-smooth hover:shadow-card-hover">
                  <div className="flex items-center gap-3 mb-3">
                  <BarChart2 className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                  <h3 className="text-body-sm font-semibold text-zinc-900 dark:text-zinc-100">P&L Analysis</h3>
                  </div>
                  <p className="text-caption text-zinc-600 dark:text-zinc-400 mb-1">
                  Daily profit: <span className="text-emerald-600 dark:text-emerald-400 font-semibold">
                      {pnlData ? `₹${pnlData.total_pnl.toLocaleString()}` : 'N/A'}
                  </span>
                  </p>
                  <p className="text-caption text-zinc-600 dark:text-zinc-400">
                  Win rate: <span className="font-semibold">{pnlData ? `${pnlData.win_rate.toFixed(1)}%` : 'N/A'}</span>
                  </p>
              </div>
              <div className="bg-zinc-50 dark:bg-zinc-900/70 padding-card-sm rounded-lg border border-zinc-100 dark:border-zinc-800 shadow-card transition-smooth hover:shadow-card-hover">
                  <div className="flex items-center gap-3 mb-3">
                  <Shield className="w-4 h-4 text-red-600 dark:text-red-400" />
                  <h3 className="text-body-sm font-semibold text-zinc-900 dark:text-zinc-100">Risk Monitor</h3>
                  </div>
                  <p className="text-caption text-zinc-600 dark:text-zinc-400 mb-1">
                  Current exposure: <span className="font-semibold">
                      {riskData ? `₹${riskData.total_exposure.toLocaleString()}` : 'N/A'}
                  </span>
                  </p>
                  <p className="text-caption text-zinc-600 dark:text-zinc-400">
                  Margin used: <span className="font-semibold">{riskData ? `${riskData.margin_usage_pct.toFixed(1)}%` : 'N/A'}</span>
                  </p>
              </div>
              <div className="bg-zinc-50 dark:bg-zinc-900/70 padding-card-sm rounded-lg border border-zinc-100 dark:border-zinc-800 shadow-card transition-smooth hover:shadow-card-hover">
                  <div className="flex items-center gap-3 mb-3">
                  <LineChart className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                  <h3 className="text-body-sm font-semibold text-zinc-900 dark:text-zinc-100">Strategy Performance</h3>
                  </div>
                  <p className="text-caption text-zinc-600 dark:text-zinc-400 mb-1">
                  Top strategy: <span className="font-semibold">{strategyData?.top_strategy?.name || 'N/A'}</span>
                  </p>
                  <p className="text-caption text-zinc-600 dark:text-zinc-400">
                  Active strategies: <span className="font-semibold">{strategyData?.active_strategies || 'N/A'}</span>
                  </p>
              </div>
              </div>
          )}
        </div>
      </ComponentErrorBoundary>

      <div className="bg-white dark:bg-[#0F0F12] rounded-xl padding-card flex flex-col border border-gray-200 dark:border-[#1F1F23] shadow-card transition-smooth hover:shadow-card-hover">
        <h2 className="text-heading-md text-gray-900 dark:text-white mb-6 text-left flex items-center gap-3">
          <Activity className="w-4 h-4 text-zinc-900 dark:text-zinc-50" />
          Quick Actions
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
          <button 
            onClick={() => router.push('/system/trades')}
            className="bg-zinc-900 dark:bg-zinc-50 text-zinc-50 dark:text-zinc-900 py-4 px-4 rounded-lg text-body-sm font-semibold hover:bg-zinc-800 dark:hover:bg-zinc-200 transition-smooth flex items-center justify-center gap-2 shadow-card hover:shadow-card-hover active:scale-95 touch-target"
          >
            <Activity className="w-4 h-4 flex-shrink-0" />
            <span className="truncate">View Live Trades</span>
          </button>
          <button 
            onClick={() => router.push('/cognitive/insights')}
            className="bg-zinc-900 dark:bg-zinc-50 text-zinc-50 dark:text-zinc-900 py-4 px-4 rounded-lg text-body-sm font-semibold hover:bg-zinc-800 dark:hover:bg-zinc-200 transition-smooth flex items-center justify-center gap-2 shadow-card hover:shadow-card-hover active:scale-95 touch-target"
          >
            <Brain className="w-4 h-4 flex-shrink-0" />
            <span className="truncate">AI Insights</span>
          </button>
          <button 
            onClick={() => router.push('/analytics/risk')}
            className="bg-zinc-900 dark:bg-zinc-50 text-zinc-50 dark:text-zinc-900 py-4 px-4 rounded-lg text-body-sm font-semibold hover:bg-zinc-800 dark:hover:bg-zinc-200 transition-smooth flex items-center justify-center gap-2 shadow-card hover:shadow-card-hover active:scale-95 touch-target"
          >
            <Shield className="w-4 h-4 flex-shrink-0" />
            <span className="truncate">Risk Analysis</span>
          </button>
          <button 
            onClick={() => router.push('/system/health')}
            className="bg-zinc-900 dark:bg-zinc-50 text-zinc-50 dark:text-zinc-900 py-4 px-4 rounded-lg text-body-sm font-semibold hover:bg-zinc-800 dark:hover:bg-zinc-200 transition-smooth flex items-center justify-center gap-2 shadow-card hover:shadow-card-hover active:scale-95 touch-target"
          >
            <Cpu className="w-4 h-4 flex-shrink-0" />
            <span className="truncate">System Status</span>
          </button>
        </div>
      </div>
    </div>
  )
})

Content.displayName = 'Content'

export default Content
