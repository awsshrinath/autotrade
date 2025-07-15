"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Home, ArrowLeft, Search } from "lucide-react"

export default function NotFound() {
  const router = useRouter()

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-[#0F0F12] flex items-center justify-center px-4">
      <div className="max-w-lg w-full text-center">
        <div className="mb-8">
          <div className="text-6xl font-bold text-gray-400 dark:text-gray-600 mb-4">404</div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
            Page Not Found
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mb-8">
            The page you&apos;re looking for doesn&apos;t exist or has been moved.
          </p>
        </div>

        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Button 
              onClick={() => router.back()}
              variant="outline" 
              className="flex items-center gap-2 border-gray-200 dark:border-[#1F1F23] text-gray-700 dark:text-gray-300"
            >
              <ArrowLeft className="w-4 h-4" />
              Go Back
            </Button>
            
            <Link href="/dashboard">
              <Button className="flex items-center gap-2 w-full sm:w-auto bg-blue-600 hover:bg-blue-700 text-white">
                <Home className="w-4 h-4" />
                Dashboard
              </Button>
            </Link>
            
            <Link href="/help">
              <Button variant="outline" className="flex items-center gap-2 border-gray-200 dark:border-[#1F1F23] text-gray-700 dark:text-gray-300">
                <Search className="w-4 h-4" />
                Get Help
              </Button>
            </Link>
          </div>

          <div className="pt-6 border-t border-gray-200 dark:border-gray-800">
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
              Popular destinations:
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
              <Link 
                href="/system/trades" 
                className="text-blue-600 dark:text-blue-400 hover:underline p-2 rounded hover:bg-blue-50 dark:hover:bg-blue-950 transition-colors"
              >
                📊 Live Trades
              </Link>
              <Link 
                href="/cognitive/insights" 
                className="text-blue-600 dark:text-blue-400 hover:underline p-2 rounded hover:bg-blue-50 dark:hover:bg-blue-950 transition-colors"
              >
                🧠 AI Insights
              </Link>
              <Link 
                href="/analytics/pnl" 
                className="text-blue-600 dark:text-blue-400 hover:underline p-2 rounded hover:bg-blue-50 dark:hover:bg-blue-950 transition-colors"
              >
                💰 P&L Analysis
              </Link>
              <Link 
                href="/system/health" 
                className="text-blue-600 dark:text-blue-400 hover:underline p-2 rounded hover:bg-blue-50 dark:hover:bg-blue-950 transition-colors"
              >
                ⚡ System Health
              </Link>
              <Link 
                href="/analytics/risk" 
                className="text-blue-600 dark:text-blue-400 hover:underline p-2 rounded hover:bg-blue-50 dark:hover:bg-blue-950 transition-colors"
              >
                🛡️ Risk Monitor
              </Link>
              <Link 
                href="/system/logs" 
                className="text-blue-600 dark:text-blue-400 hover:underline p-2 rounded hover:bg-blue-50 dark:hover:bg-blue-950 transition-colors"
              >
                📋 Logs
              </Link>
              <Link 
                href="/analytics/strategy" 
                className="text-blue-600 dark:text-blue-400 hover:underline p-2 rounded hover:bg-blue-50 dark:hover:bg-blue-950 transition-colors"
              >
                📈 Strategy Performance
              </Link>
              <Link 
                href="/settings" 
                className="text-blue-600 dark:text-blue-400 hover:underline p-2 rounded hover:bg-blue-50 dark:hover:bg-blue-950 transition-colors"
              >
                ⚙️ Settings
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
} 