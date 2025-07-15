"use client"

import { useState, useEffect, useCallback, useMemo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../components/ui/card'
import { Button } from '../../../components/ui/button'
import { Badge } from '../../../components/ui/badge'
import { AlertTriangle, TrendingUp, TrendingDown, X, Target, Pause, RefreshCw } from 'lucide-react'
import { cn } from '../../../lib/utils'
import { SkeletonAnalyticsCard, SkeletonDashboard } from '../../../components/ui/skeleton'
import { useApiError } from '../../../components/error-context'
import apiClient from '../../../lib/api-error-handler'

interface Position {
  id: string
  symbol: string
  strategy: string
  side: 'LONG' | 'SHORT'
  quantity: number
  entry_price: number
  current_price: number
  pnl: number
  pnl_percentage: number
  timestamp: string
  status: 'OPEN' | 'CLOSED'
}

interface LiveTrade {
  id: string
  symbol: string
  side: 'BUY' | 'SELL'
  quantity: number
  price: number
  timestamp: string
  status: 'FILLED' | 'PENDING' | 'CANCELLED'
  strategy: string
}

export default function LiveTradesPage() {
  const [positions, setPositions] = useState<Position[]>([])
  const [recentTrades, setRecentTrades] = useState<LiveTrade[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [totalPnL, setTotalPnL] = useState(0)
  const [totalExposure, setTotalExposure] = useState(0)
  const [refreshing, setRefreshing] = useState(false)
  const { handleApiError } = useApiError()

  // Fetch live positions
  const fetchPositions = useCallback(async () => {
    try {
      const data = await apiClient.get<{ positions: Position[]; total_pnl: number; total_exposure: number; }>('/api/v1/trade/positions/live', {
        retry: {
          maxRetries: 2,
          retryDelay: 1000,
          exponentialBackoff: true
        }
      })
      setPositions(data.positions || [])
      setTotalPnL(data.total_pnl || 0)
      setTotalExposure(data.total_exposure || 0)
    } catch (error: unknown) {
      handleApiError(error, 'Positions')
      throw error
    }
  }, [handleApiError])

  // Fetch recent trades
  const fetchRecentTrades = useCallback(async () => {
    try {
      const data = await apiClient.get<{ trades: LiveTrade[] }>('/api/v1/trade/recent?limit=10', {
        retry: {
          maxRetries: 2,
          retryDelay: 1000,
          exponentialBackoff: true
        }
      })
      setRecentTrades(data.trades || [])
    } catch (error: unknown) {
      handleApiError(error, 'Recent Trades')
      throw error
    }
  }, [handleApiError])

  const fetchAllData = useCallback(async (showLoader = true) => {
    try {
      if (showLoader) setLoading(true)
      else setRefreshing(true)
      setError(null)
      
      await Promise.all([fetchPositions(), fetchRecentTrades()])
    } catch (err: unknown) {
      setError('Failed to load trading data')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [fetchPositions, fetchRecentTrades])

  // Emergency Controls
  const closeAllPositions = useCallback(async () => {
    try {
      await apiClient.post('/api/v1/trade/emergency/close-all')
      alert('All positions closed successfully')
      fetchPositions()
    } catch (error: unknown) {
      handleApiError(error, 'Close All Positions')
      alert('Failed to close positions')
    }
  }, [fetchPositions, handleApiError])

  const moveAllToBreakeven = useCallback(async () => {
    try {
      await apiClient.post('/api/v1/trade/emergency/breakeven')
      alert('All positions moved to breakeven')
      fetchPositions()
    } catch (error: unknown) {
      handleApiError(error, 'Move to Breakeven')
      alert('Failed to move to breakeven')
    }
  }, [fetchPositions, handleApiError])

  const closePosition = useCallback(async (positionId: string) => {
    try {
      await apiClient.post(`/api/v1/trade/position/${positionId}/close`)
      fetchPositions()
    } catch (error: unknown) {
      handleApiError(error, 'Close Position')
    }
  }, [fetchPositions, handleApiError])

  // Auto-refresh effect
  useEffect(() => {
    fetchAllData()

    let interval: NodeJS.Timeout
    if (autoRefresh) {
      interval = setInterval(() => {
        fetchAllData(false) // Don't show loading spinner for auto-refresh
      }, 5000) // Refresh every 5 seconds
    }

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [autoRefresh, fetchAllData])

  const formatCurrency = useMemo(() => (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2
    }).format(amount)
  }, [])

  const formatPercentage = useMemo(() => (percentage: number) => {
    return `${percentage >= 0 ? '+' : ''}${percentage.toFixed(2)}%`
  }, [])

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div className="space-y-2">
            <div className="h-8 w-64 bg-zinc-100 dark:bg-zinc-800 rounded animate-pulse"></div>
            <div className="h-4 w-96 bg-zinc-100 dark:bg-zinc-800 rounded animate-pulse"></div>
          </div>
          <div className="h-10 w-32 bg-zinc-100 dark:bg-zinc-800 rounded animate-pulse"></div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <SkeletonAnalyticsCard key={i} />
          ))}
        </div>
        
        <SkeletonDashboard />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-4">
        <AlertTriangle className="w-12 h-12 text-amber-500" />
        <div className="text-center">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Unable to load trading data</h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{error}</p>
        </div>
        <Button onClick={() => fetchAllData()} className="gap-2">
          <RefreshCw className="w-4 h-4" />
          Try Again
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header with Summary */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-display-sm font-bold">Live Trading Monitor</h1>
          <p className="text-body text-muted-foreground">Real-time position tracking and trade management</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => fetchAllData(false)}
            disabled={refreshing}
            className="gap-2"
          >
            <RefreshCw className={cn("w-4 h-4", refreshing && "animate-spin")} />
            Refresh
          </Button>
          <Button
            variant={autoRefresh ? "default" : "outline"}
            onClick={() => setAutoRefresh(!autoRefresh)}
            className="gap-2"
          >
            <Pause className="w-4 h-4" />
            {autoRefresh ? 'Auto-Refresh On' : 'Auto-Refresh Off'}
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="shadow-card hover:shadow-card-hover transition-smooth">
          <CardHeader className="pb-2">
            <CardTitle className="text-body-sm font-medium">Total P&L</CardTitle>
          </CardHeader>
          <CardContent>
            <div className={cn("text-heading-lg font-bold", totalPnL >= 0 ? "text-green-600" : "text-red-600")}>
              {formatCurrency(totalPnL)}
            </div>
          </CardContent>
        </Card>

        <Card className="shadow-card hover:shadow-card-hover transition-smooth">
          <CardHeader className="pb-2">
            <CardTitle className="text-body-sm font-medium">Total Exposure</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-heading-lg font-bold">{formatCurrency(totalExposure)}</div>
          </CardContent>
        </Card>

        <Card className="shadow-card hover:shadow-card-hover transition-smooth">
          <CardHeader className="pb-2">
            <CardTitle className="text-body-sm font-medium">Open Positions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-heading-lg font-bold">{positions.length}</div>
          </CardContent>
        </Card>

        <Card className="shadow-card hover:shadow-card-hover transition-smooth">
          <CardHeader className="pb-2">
            <CardTitle className="text-body-sm font-medium">Recent Trades</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-heading-lg font-bold">{recentTrades.length}</div>
          </CardContent>
        </Card>
      </div>

      {/* Emergency Controls */}
      <Card className="border-amber-200/50 bg-gradient-to-r from-amber-50/30 to-orange-50/30 dark:border-amber-800/30 dark:from-amber-950/20 dark:to-orange-950/20 shadow-card">
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-2 text-amber-700 dark:text-amber-400">
            <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400" />
            Emergency Controls
          </CardTitle>
          <CardDescription className="text-amber-700/80 dark:text-amber-300/80">
            Use these controls carefully - they affect all open positions
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col sm:flex-row gap-3">
          <Button 
            onClick={closeAllPositions}
            className="bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white shadow-md hover:shadow-lg transition-smooth border-0"
          >
            <X className="w-4 h-4 mr-2" />
            Close All Positions
          </Button>
          <Button 
            variant="outline" 
            onClick={moveAllToBreakeven}
            className="border-amber-300 text-amber-700 hover:bg-amber-50 dark:border-amber-600 dark:text-amber-400 dark:hover:bg-amber-950/20 transition-smooth"
          >
            <Target className="w-4 h-4 mr-2" />
            Move All to Breakeven
          </Button>
        </CardContent>
      </Card>

      {/* Live Positions */}
      <Card className="shadow-card">
        <CardHeader>
          <CardTitle>Open Positions</CardTitle>
          <CardDescription>Real-time tracking of all open positions</CardDescription>
        </CardHeader>
        <CardContent>
          {positions.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-4xl mb-4">📊</div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">No open positions</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">All positions are currently closed</p>
            </div>
          ) : (
            <div className="space-y-4">
              {positions.map((position) => (
                <div key={position.id} className="flex items-center justify-between p-4 border rounded-lg transition-smooth hover:bg-zinc-50 dark:hover:bg-zinc-900/50">
                  <div className="flex items-center gap-4">
                    <div>
                      <div className="font-semibold">{position.symbol}</div>
                      <div className="text-caption text-muted-foreground">{position.strategy}</div>
                    </div>
                    <Badge variant={position.side === 'LONG' ? 'default' : 'secondary'}>
                      {position.side}
                    </Badge>
                    <div className="text-body-sm">
                      <div>Qty: {position.quantity}</div>
                      <div>Entry: ₹{position.entry_price}</div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="font-semibold">₹{position.current_price}</div>
                      <div className={cn("text-body-sm flex items-center gap-1", 
                        position.pnl >= 0 ? "text-green-600" : "text-red-600"
                      )}>
                        {position.pnl >= 0 ? 
                          <TrendingUp className="w-3 h-3" /> : 
                          <TrendingDown className="w-3 h-3" />
                        }
                        {formatCurrency(position.pnl)} ({formatPercentage(position.pnl_percentage)})
                      </div>
                    </div>
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => closePosition(position.id)}
                    >
                      Close
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent Trades */}
      <Card className="shadow-card">
        <CardHeader>
          <CardTitle>Recent Trades</CardTitle>
          <CardDescription>Latest trade executions</CardDescription>
        </CardHeader>
        <CardContent>
          {recentTrades.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-4xl mb-4">📈</div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">No recent trades</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">Trade executions will appear here</p>
            </div>
          ) : (
            <div className="space-y-2">
              {recentTrades.map((trade) => (
                <div key={trade.id} className="flex items-center justify-between p-3 border rounded transition-smooth hover:bg-zinc-50 dark:hover:bg-zinc-900/50">
                  <div className="flex items-center gap-4">
                    <Badge variant={trade.side === 'BUY' ? 'default' : 'secondary'}>
                      {trade.side}
                    </Badge>
                    <div>
                      <div className="font-medium">{trade.symbol}</div>
                      <div className="text-caption text-muted-foreground">{trade.strategy}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium">{trade.quantity} @ ₹{trade.price}</div>
                    <div className="text-caption text-muted-foreground">
                      {new Date(trade.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}