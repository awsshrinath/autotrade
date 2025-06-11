"use client"

import { useState, useEffect } from "react"
import { Activity, Brain, Cpu, LineChart, Shield, BarChart2, Loader2 } from "lucide-react"
import SystemStatusCard from "./system-status-card"
import AIMetricsCard from "./ai-metrics-card"
import SystemHealthCard from "./system-health-card"

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

export default function Content() {
  const [pnlData, setPnlData] = useState<PnlSummary | null>(null)
  const [riskData, setRiskData] = useState<RiskSummary | null>(null)
  const [strategyData, setStrategyData] = useState<StrategySummary | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const [pnlRes, riskRes, strategyRes] = await Promise.all([
          fetch("http://localhost:8000/api/trade/summary/daily"),
          fetch("http://localhost:8000/api/trade/summary/positions"),
          fetch("http://localhost:8000/api/trade/summary/strategy"),
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
    }
    fetchData()
  }, [])


  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <SystemStatusCard />
        <AIMetricsCard />
        <SystemHealthCard />
      </div>

      <div className="bg-white dark:bg-[#0F0F12] rounded-xl p-6 flex flex-col border border-gray-200 dark:border-[#1F1F23]">
        <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4 text-left flex items-center gap-2">
          <LineChart className="w-3.5 h-3.5 text-zinc-900 dark:text-zinc-50" />
          Analytics Overview
        </h2>
        {loading ? (
            <div className="flex items-center justify-center h-24">
                <Loader2 className="w-6 h-6 animate-spin text-zinc-500" />
            </div>
        ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-zinc-50 dark:bg-zinc-900/70 p-4 rounded-lg border border-zinc-100 dark:border-zinc-800">
                <div className="flex items-center gap-2 mb-2">
                <BarChart2 className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                <h3 className="text-sm font-medium text-zinc-900 dark:text-zinc-100">P&L Analysis</h3>
                </div>
                <p className="text-xs text-zinc-600 dark:text-zinc-400">
                Daily profit: <span className="text-emerald-600 dark:text-emerald-400 font-medium">
                    {pnlData ? `₹${pnlData.total_pnl.toLocaleString()}` : 'N/A'}
                </span>
                </p>
                <p className="text-xs text-zinc-600 dark:text-zinc-400">
                Win rate: <span className="font-medium">{pnlData ? `${pnlData.win_rate.toFixed(1)}%` : 'N/A'}</span>
                </p>
            </div>
            <div className="bg-zinc-50 dark:bg-zinc-900/70 p-4 rounded-lg border border-zinc-100 dark:border-zinc-800">
                <div className="flex items-center gap-2 mb-2">
                <Shield className="w-4 h-4 text-red-600 dark:text-red-400" />
                <h3 className="text-sm font-medium text-zinc-900 dark:text-zinc-100">Risk Monitor</h3>
                </div>
                <p className="text-xs text-zinc-600 dark:text-zinc-400">
                Current exposure: <span className="font-medium">
                    {riskData ? `₹${riskData.total_exposure.toLocaleString()}` : 'N/A'}
                </span>
                </p>
                <p className="text-xs text-zinc-600 dark:text-zinc-400">
                Margin used: <span className="font-medium">{riskData ? `${riskData.margin_usage_pct.toFixed(1)}%` : 'N/A'}</span>
                </p>
            </div>
            <div className="bg-zinc-50 dark:bg-zinc-900/70 p-4 rounded-lg border border-zinc-100 dark:border-zinc-800">
                <div className="flex items-center gap-2 mb-2">
                <LineChart className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                <h3 className="text-sm font-medium text-zinc-900 dark:text-zinc-100">Strategy Performance</h3>
                </div>
                <p className="text-xs text-zinc-600 dark:text-zinc-400">
                Top strategy: <span className="font-medium">{strategyData?.top_strategy?.name || 'N/A'}</span>
                </p>
                <p className="text-xs text-zinc-600 dark:text-zinc-400">
                Active strategies: <span className="font-medium">{strategyData?.active_strategies || 'N/A'}</span>
                </p>
            </div>
            </div>
        )}
      </div>

      <div className="bg-white dark:bg-[#0F0F12] rounded-xl p-6 flex flex-col border border-gray-200 dark:border-[#1F1F23]">
        <h2 className="text-lg font-bold text-gray-900 dark:text-white mb-4 text-left flex items-center gap-2">
          <Activity className="w-3.5 h-3.5 text-zinc-900 dark:text-zinc-50" />
          Quick Actions
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button className="bg-zinc-900 dark:bg-zinc-50 text-zinc-50 dark:text-zinc-900 py-3 px-4 rounded-lg text-sm font-medium hover:bg-zinc-800 dark:hover:bg-zinc-200 transition-colors flex items-center justify-center gap-2">
            <Activity className="w-4 h-4" />
            View Live Trades
          </button>
          <button className="bg-zinc-900 dark:bg-zinc-50 text-zinc-50 dark:text-zinc-900 py-3 px-4 rounded-lg text-sm font-medium hover:bg-zinc-800 dark:hover:bg-zinc-200 transition-colors flex items-center justify-center gap-2">
            <Brain className="w-4 h-4" />
            AI Insights
          </button>
          <button className="bg-zinc-900 dark:bg-zinc-50 text-zinc-50 dark:text-zinc-900 py-3 px-4 rounded-lg text-sm font-medium hover:bg-zinc-800 dark:hover:bg-zinc-200 transition-colors flex items-center justify-center gap-2">
            <Shield className="w-4 h-4" />
            Risk Analysis
          </button>
          <button className="bg-zinc-900 dark:bg-zinc-50 text-zinc-50 dark:text-zinc-900 py-3 px-4 rounded-lg text-sm font-medium hover:bg-zinc-800 dark:hover:bg-zinc-200 transition-colors flex items-center justify-center gap-2">
            <Cpu className="w-4 h-4" />
            System Status
          </button>
        </div>
      </div>
    </div>
  )
}
