"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../components/ui/card'
import { Button } from '../../../components/ui/button'
import { Badge } from '../../../components/ui/badge'
import { AlertTriangle, TrendingUp, TrendingDown, X, Target, Pause } from 'lucide-react'
import { cn } from '../../../lib/utils'

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
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [totalPnL, setTotalPnL] = useState(0)
  const [totalExposure, setTotalExposure] = useState(0)

  // Fetch live positions
  const fetchPositions = async () => {
    try {
      const response = await fetch('/api/v1/trade/positions/live')
      if (response.ok) {
        const data = await response.json()
        setPositions(data.positions || [])
        setTotalPnL(data.total_pnl || 0)
        setTotalExposure(data.total_exposure || 0)
      }
    } catch (error) {
      console.error('Failed to fetch positions:', error)
    }
  }

  // Fetch recent trades
  const fetchRecentTrades = async () => {
    try {
      const response = await fetch('/api/v1/trade/recent?limit=10')
      if (response.ok) {
        const data = await response.json()
        setRecentTrades(data.trades || [])
      }
    } catch (error) {
      console.error('Failed to fetch recent trades:', error)
    }
  }

  // Emergency Controls
  const closeAllPositions = async () => {
    try {
      const response = await fetch('/api/v1/trade/emergency/close-all', {
        method: 'POST'
      })
      if (response.ok) {
        alert('All positions closed successfully')
        fetchPositions()
      }
    } catch (error) {
      console.error('Failed to close all positions:', error)
      alert('Failed to close positions')
    }
  }

  const moveAllToBreakeven = async () => {
    try {
      const response = await fetch('/api/v1/trade/emergency/breakeven', {
        method: 'POST'
      })
      if (response.ok) {
        alert('All positions moved to breakeven')
        fetchPositions()
      }
    } catch (error) {
      console.error('Failed to move to breakeven:', error)
      alert('Failed to move to breakeven')
    }
  }

  const closePosition = async (positionId: string) => {
    try {
      const response = await fetch(`/api/v1/trade/position/${positionId}/close`, {
        method: 'POST'
      })
      if (response.ok) {
        fetchPositions()
      }
    } catch (error) {
      console.error('Failed to close position:', error)
    }
  }

  // Auto-refresh effect
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      await Promise.all([fetchPositions(), fetchRecentTrades()])
      setLoading(false)
    }

    fetchData()

    let interval: NodeJS.Timeout
    if (autoRefresh) {
      interval = setInterval(() => {
        fetchPositions()
        fetchRecentTrades()
      }, 5000) // Refresh every 5 seconds
    }

    return () => {
      if (interval) clearInterval(interval)
    }
  }, [autoRefresh])

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2
    }).format(amount)
  }

  const formatPercentage = (percentage: number) => {
    return `${percentage >= 0 ? '+' : ''}${percentage.toFixed(2)}%`
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header with Summary */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Live Trading Monitor</h1>
          <p className="text-muted-foreground">Real-time position tracking and trade management</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant={autoRefresh ? "default" : "outline"}
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            <Pause className="w-4 h-4 mr-2" />
            {autoRefresh ? 'Auto-Refresh On' : 'Auto-Refresh Off'}
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total P&L</CardTitle>
          </CardHeader>
          <CardContent>
            <div className={cn("text-2xl font-bold", totalPnL >= 0 ? "text-green-600" : "text-red-600")}>
              {formatCurrency(totalPnL)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Exposure</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(totalExposure)}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Open Positions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{positions.length}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Recent Trades</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{recentTrades.length}</div>
          </CardContent>
        </Card>
      </div>

      {/* Emergency Controls */}
      <Card className="border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-red-600">
            <AlertTriangle className="w-5 h-5" />
            Emergency Controls
          </CardTitle>
          <CardDescription>Use these controls carefully - they affect all open positions</CardDescription>
        </CardHeader>
        <CardContent className="flex gap-4">
          <Button 
            variant="destructive" 
            onClick={closeAllPositions}
            className="bg-red-600 hover:bg-red-700"
          >
            <X className="w-4 h-4 mr-2" />
            Close All Positions
          </Button>
          <Button 
            variant="outline" 
            onClick={moveAllToBreakeven}
            className="border-orange-500 text-orange-600 hover:bg-orange-50"
          >
            <Target className="w-4 h-4 mr-2" />
            Move All to Breakeven
          </Button>
        </CardContent>
      </Card>

      {/* Live Positions */}
      <Card>
        <CardHeader>
          <CardTitle>Open Positions</CardTitle>
          <CardDescription>Real-time tracking of all open positions</CardDescription>
        </CardHeader>
        <CardContent>
          {positions.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No open positions
            </div>
          ) : (
            <div className="space-y-4">
              {positions.map((position) => (
                <div key={position.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center gap-4">
                    <div>
                      <div className="font-semibold">{position.symbol}</div>
                      <div className="text-sm text-muted-foreground">{position.strategy}</div>
                    </div>
                    <Badge variant={position.side === 'LONG' ? 'default' : 'secondary'}>
                      {position.side}
                    </Badge>
                    <div className="text-sm">
                      <div>Qty: {position.quantity}</div>
                      <div>Entry: ₹{position.entry_price}</div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="font-semibold">₹{position.current_price}</div>
                      <div className={cn("text-sm flex items-center gap-1", 
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
      <Card>
        <CardHeader>
          <CardTitle>Recent Trades</CardTitle>
          <CardDescription>Latest trade executions</CardDescription>
        </CardHeader>
        <CardContent>
          {recentTrades.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No recent trades
            </div>
          ) : (
            <div className="space-y-2">
              {recentTrades.map((trade) => (
                <div key={trade.id} className="flex items-center justify-between p-3 border rounded">
                  <div className="flex items-center gap-4">
                    <Badge variant={trade.side === 'BUY' ? 'default' : 'secondary'}>
                      {trade.side}
                    </Badge>
                    <div>
                      <div className="font-medium">{trade.symbol}</div>
                      <div className="text-sm text-muted-foreground">{trade.strategy}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium">{trade.quantity} @ ₹{trade.price}</div>
                    <div className="text-sm text-muted-foreground">
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