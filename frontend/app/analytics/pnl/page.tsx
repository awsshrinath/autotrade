"use client"

import { useState, useEffect, memo, useMemo, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../components/ui/card'
import { Button } from '../../../components/ui/button'
import { Badge } from '../../../components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../components/ui/select'
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { TrendingUp, TrendingDown, DollarSign, Calendar, Download } from 'lucide-react'
import { cn } from '../../../lib/utils'

interface PnLData {
  date: string
  daily_pnl: number
  cumulative_pnl: number
  trades_count: number
  win_rate: number
}

interface StrategyPnL {
  strategy: string
  pnl: number
  trades: number
  win_rate: number
  avg_trade: number
}

interface PerformanceMetrics {
  total_pnl: number
  total_trades: number
  win_rate: number
  avg_trade_pnl: number
  max_drawdown: number
  sharpe_ratio: number
  sortino_ratio: number
  profit_factor: number
  largest_win: number
  largest_loss: number
}

export default function PnLAnalysisPage() {
  const [pnlData, setPnlData] = useState<PnLData[]>([])
  const [strategyData, setStrategyData] = useState<StrategyPnL[]>([])
  const [metrics, setMetrics] = useState<PerformanceMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [timeframe, setTimeframe] = useState('7d')
  const [chartType, setChartType] = useState<'line' | 'area' | 'bar'>('area')

  const timeframes = [
    { value: '1d', label: 'Today' },
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' },
    { value: '90d', label: 'Last 90 Days' },
    { value: 'ytd', label: 'Year to Date' },
    { value: 'all', label: 'All Time' }
  ]

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d']

  // Fetch P&L data
  const fetchPnLData = async () => {
    try {
      setLoading(true)
      const [pnlRes, strategyRes, metricsRes] = await Promise.all([
        fetch(`/api/v1/analytics/pnl/daily?timeframe=${timeframe}`),
        fetch(`/api/v1/analytics/pnl/strategy?timeframe=${timeframe}`),
        fetch(`/api/v1/analytics/metrics?timeframe=${timeframe}`)
      ])

      if (pnlRes.ok) {
        const data = await pnlRes.json()
        setPnlData(data.pnl_data || [])
      }

      if (strategyRes.ok) {
        const data = await strategyRes.json()
        setStrategyData(data.strategies || [])
      }

      if (metricsRes.ok) {
        const data = await metricsRes.json()
        setMetrics(data.metrics)
      }
    } catch (error) {
      console.error('Failed to fetch P&L data:', error)
    } finally {
      setLoading(false)
    }
  }

  const exportData = async () => {
    try {
      const response = await fetch(`/api/v1/analytics/export?timeframe=${timeframe}`)
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `pnl_analysis_${timeframe}.csv`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      }
    } catch (error) {
      console.error('Failed to export data:', error)
    }
  }

  useEffect(() => {
    fetchPnLData()
  }, [timeframe])

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0
    }).format(amount)
  }

  const formatPercentage = (percentage: number) => {
    return `${percentage >= 0 ? '+' : ''}${percentage.toFixed(2)}%`
  }

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-background border rounded-lg p-3 shadow-lg">
          <p className="font-medium">{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className={cn("text-sm", 
              entry.value >= 0 ? "text-green-600" : "text-red-600"
            )}>
              {entry.name}: {formatCurrency(entry.value)}
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  const renderChart = () => {
    const chartProps = {
      data: pnlData,
      margin: { top: 5, right: 30, left: 20, bottom: 5 }
    }

    switch (chartType) {
      case 'line':
        return (
          <LineChart {...chartProps}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip content={<CustomTooltip />} />
            <Line 
              type="monotone" 
              dataKey="cumulative_pnl" 
              stroke="#8884d8" 
              strokeWidth={2}
              dot={{ r: 4 }}
            />
          </LineChart>
        )
      case 'area':
        return (
          <AreaChart {...chartProps}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip content={<CustomTooltip />} />
            <Area 
              type="monotone" 
              dataKey="cumulative_pnl" 
              stroke="#8884d8" 
              fill="#8884d8" 
              fillOpacity={0.3}
            />
          </AreaChart>
        )
      case 'bar':
        return (
          <BarChart {...chartProps}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="daily_pnl" fill="#8884d8" />
          </BarChart>
        )
    }
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
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">P&L Analysis</h1>
          <p className="text-muted-foreground">Comprehensive profit and loss analytics</p>
        </div>
        <div className="flex gap-2">
          <Select value={timeframe} onValueChange={setTimeframe}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {timeframes.map(tf => (
                <SelectItem key={tf.value} value={tf.value}>
                  {tf.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={exportData}>
            <Download className="w-4 h-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Performance Metrics */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Total P&L</CardTitle>
            </CardHeader>
            <CardContent>
              <div className={cn("text-2xl font-bold", 
                metrics.total_pnl >= 0 ? "text-green-600" : "text-red-600"
              )}>
                {formatCurrency(metrics.total_pnl)}
              </div>
              <div className="flex items-center gap-1 text-sm text-muted-foreground">
                {metrics.total_pnl >= 0 ? 
                  <TrendingUp className="w-3 h-3" /> : 
                  <TrendingDown className="w-3 h-3" />
                }
                {metrics.total_trades} trades
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Win Rate</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metrics.win_rate.toFixed(1)}%</div>
              <div className="text-sm text-muted-foreground">
                Avg: {formatCurrency(metrics.avg_trade_pnl)}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Sharpe Ratio</CardTitle>
            </CardHeader>
            <CardContent>
              <div className={cn("text-2xl font-bold",
                metrics.sharpe_ratio > 1 ? "text-green-600" : 
                metrics.sharpe_ratio > 0 ? "text-yellow-600" : "text-red-600"
              )}>
                {metrics.sharpe_ratio.toFixed(2)}
              </div>
              <div className="text-sm text-muted-foreground">
                Sortino: {metrics.sortino_ratio.toFixed(2)}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Max Drawdown</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">
                {formatPercentage(metrics.max_drawdown)}
              </div>
              <div className="text-sm text-muted-foreground">
                PF: {metrics.profit_factor.toFixed(2)}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* P&L Chart */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle>P&L Trend</CardTitle>
              <CardDescription>Historical profit and loss performance</CardDescription>
            </div>
            <div className="flex gap-2">
              <Button
                variant={chartType === 'area' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setChartType('area')}
              >
                Area
              </Button>
              <Button
                variant={chartType === 'line' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setChartType('line')}
              >
                Line
              </Button>
              <Button
                variant={chartType === 'bar' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setChartType('bar')}
              >
                Bar
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              {renderChart()}
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Strategy Performance */}
        <Card>
          <CardHeader>
            <CardTitle>Strategy Performance</CardTitle>
            <CardDescription>P&L breakdown by trading strategy</CardDescription>
          </CardHeader>
          <CardContent>
            {strategyData.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No strategy data available
              </div>
            ) : (
              <div className="space-y-4">
                {strategyData.map((strategy, index) => (
                  <div key={strategy.strategy} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center gap-3">
                      <div 
                        className="w-3 h-3 rounded-full" 
                        style={{ backgroundColor: COLORS[index % COLORS.length] }}
                      />
                      <div>
                        <div className="font-medium">{strategy.strategy}</div>
                        <div className="text-sm text-muted-foreground">
                          {strategy.trades} trades • {strategy.win_rate.toFixed(1)}% win rate
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className={cn("font-medium", 
                        strategy.pnl >= 0 ? "text-green-600" : "text-red-600"
                      )}>
                        {formatCurrency(strategy.pnl)}
                      </div>
                      <div className="text-sm text-muted-foreground">
                        Avg: {formatCurrency(strategy.avg_trade)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Strategy Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>P&L Distribution</CardTitle>
            <CardDescription>Profit contribution by strategy</CardDescription>
          </CardHeader>
          <CardContent>
            {strategyData.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No data available
              </div>
            ) : (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={strategyData}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="pnl"
                      label={({ strategy, pnl }) => `${strategy}: ${formatCurrency(pnl)}`}
                    >
                      {strategyData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => formatCurrency(value as number)} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Trade Statistics */}
      {metrics && (
        <Card>
          <CardHeader>
            <CardTitle>Trade Statistics</CardTitle>
            <CardDescription>Detailed trading performance metrics</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div>
                <h4 className="font-medium text-sm text-muted-foreground mb-2">LARGEST WIN</h4>
                <div className="text-lg font-semibold text-green-600">
                  {formatCurrency(metrics.largest_win)}
                </div>
              </div>
              <div>
                <h4 className="font-medium text-sm text-muted-foreground mb-2">LARGEST LOSS</h4>
                <div className="text-lg font-semibold text-red-600">
                  {formatCurrency(metrics.largest_loss)}
                </div>
              </div>
              <div>
                <h4 className="font-medium text-sm text-muted-foreground mb-2">PROFIT FACTOR</h4>
                <div className={cn("text-lg font-semibold",
                  metrics.profit_factor > 1.5 ? "text-green-600" : 
                  metrics.profit_factor > 1 ? "text-yellow-600" : "text-red-600"
                )}>
                  {metrics.profit_factor.toFixed(2)}
                </div>
              </div>
              <div>
                <h4 className="font-medium text-sm text-muted-foreground mb-2">AVG TRADE</h4>
                <div className={cn("text-lg font-semibold",
                  metrics.avg_trade_pnl >= 0 ? "text-green-600" : "text-red-600"
                )}>
                  {formatCurrency(metrics.avg_trade_pnl)}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}