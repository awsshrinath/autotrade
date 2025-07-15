"use client"

import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../components/ui/card'
import { Button } from '../../../components/ui/button'
import { Badge } from '../../../components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../components/ui/select'
import { Progress } from '../../../components/ui/progress'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts'
import { Activity, Target, Shield } from 'lucide-react'
import { cn } from '../../../lib/utils'
import apiClient, { handleApiError } from '@/lib/api-error-handler'

interface Strategy {
  name: string
  status: 'active' | 'paused' | 'stopped'
  total_pnl: number
  daily_pnl: number
  total_trades: number
  win_rate: number
  avg_trade: number
  max_drawdown: number
  sharpe_ratio: number
  current_positions: number
  risk_score: number
  last_trade: string
}

interface StrategyPerformance {
  strategy: string
  date: string
  pnl: number
  trades: number
  win_rate: number
}

interface StrategyComparison {
  metric: string
  [key: string]: string | number
}

export default function StrategyPerformancePage() {
  const [strategies, setStrategies] = useState<Strategy[]>([])
  const [performanceData, setPerformanceData] = useState<StrategyPerformance[]>([])
  const [comparisonData, setComparisonData] = useState<StrategyComparison[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedStrategy, setSelectedStrategy] = useState<string>('all')
  const [timeframe, setTimeframe] = useState('7d')

  const timeframes = [
    { value: '1d', label: 'Today' },
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' },
    { value: '90d', label: 'Last 90 Days' }
  ]

  // Fetch strategy data
  const fetchStrategyData = useCallback(async () => {
    try {
      setLoading(true)
      
      // Use enhanced API client with fallback disabled in production
      const isProduction = process.env.NEXT_PUBLIC_ENV === 'production'
      const options = { useFallback: !isProduction }
      
      const [strategiesData, performanceData, comparisonData] = await Promise.all([
        apiClient.get<{strategies: Strategy[]}>('/api/v1/strategy/all', options),
        apiClient.get<{performance: StrategyPerformance[]}>(`/api/v1/strategy/performance?timeframe=${timeframe}`, options),
        apiClient.get<{comparison: StrategyComparison[]}>('/api/v1/strategy/comparison', options)
      ])

      setStrategies(strategiesData.strategies || [])
      setPerformanceData(performanceData.performance || [])
      setComparisonData(comparisonData.comparison || [])
      
    } catch (error) {
      console.error('Failed to fetch strategy data:', error)
      
      // In production mode, show appropriate error message and reset data
      if (process.env.NEXT_PUBLIC_ENV === 'production') {
        console.warn(handleApiError(error, 'Strategy analysis'))
        setStrategies([])
        setPerformanceData([])
        setComparisonData([])
      }
    } finally {
      setLoading(false)
    }
  }, [timeframe])

  // Toggle strategy status
  const toggleStrategy = async (strategyName: string, action: 'start' | 'pause' | 'stop') => {
    try {
      const options = { useFallback: false } // Never use fallback for strategy actions
      await apiClient.post(`/api/v1/strategy/${strategyName}/${action}`, {}, options)
      fetchStrategyData()
    } catch (error) {
      console.error('Failed to toggle strategy:', error)
      console.warn(handleApiError(error, 'Strategy control'))
    }
  }

  useEffect(() => {
    fetchStrategyData()
  }, [timeframe, fetchStrategyData])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800'
      case 'paused': return 'bg-yellow-100 text-yellow-800'
      case 'stopped': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return <Activity className="w-3 h-3" />
      case 'paused': return <Target className="w-3 h-3" />
      case 'stopped': return <Shield className="w-3 h-3" />
      default: return <Activity className="w-3 h-3" />
    }
  }

  const getRiskColor = (riskScore: number) => {
    if (riskScore <= 3) return 'text-green-600'
    if (riskScore <= 6) return 'text-yellow-600'
    return 'text-red-600'
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0
    }).format(amount)
  }

  // const formatPercentage = (percentage: number) => {
  //   return `${percentage >= 0 ? '+' : ''}${percentage.toFixed(2)}%`
  // }

  const filteredPerformanceData = selectedStrategy === 'all' 
    ? performanceData 
    : performanceData.filter(item => item.strategy === selectedStrategy)

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
          <h1 className="text-3xl font-bold">Strategy Performance</h1>
          <p className="text-muted-foreground">Monitor and analyze trading strategy performance</p>
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
        </div>
      </div>

      {/* Strategy Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {strategies.map((strategy) => (
          <Card key={strategy.name} className="relative">
            <CardHeader className="pb-3">
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-lg">{strategy.name}</CardTitle>
                  <div className="flex items-center gap-2 mt-1">
                    <Badge className={getStatusColor(strategy.status)}>
                      {getStatusIcon(strategy.status)}
                      {strategy.status}
                    </Badge>
                    <span className={cn("text-sm font-medium", getRiskColor(strategy.risk_score))}>
                      Risk: {strategy.risk_score}/10
                    </span>
                  </div>
                </div>
                <div className="flex gap-1">
                  {strategy.status !== 'active' && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => toggleStrategy(strategy.name, 'start')}
                      className="px-2"
                    >
                      Start
                    </Button>
                  )}
                  {strategy.status === 'active' && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => toggleStrategy(strategy.name, 'pause')}
                      className="px-2"
                    >
                      Pause
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => toggleStrategy(strategy.name, 'stop')}
                    className="px-2 text-red-600"
                  >
                    Stop
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* P&L */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-muted-foreground">Total P&L</div>
                  <div className={cn("text-lg font-semibold", 
                    strategy.total_pnl >= 0 ? "text-green-600" : "text-red-600"
                  )}>
                    {formatCurrency(strategy.total_pnl)}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground">Daily P&L</div>
                  <div className={cn("text-lg font-semibold", 
                    strategy.daily_pnl >= 0 ? "text-green-600" : "text-red-600"
                  )}>
                    {formatCurrency(strategy.daily_pnl)}
                  </div>
                </div>
              </div>

              {/* Metrics */}
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Win Rate</span>
                  <span className="font-medium">{strategy.win_rate.toFixed(1)}%</span>
                </div>
                <Progress value={strategy.win_rate} className="h-2" />

                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Trades</span>
                  <span className="font-medium">{strategy.total_trades}</span>
                </div>

                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Avg Trade</span>
                  <span className={cn("font-medium", 
                    strategy.avg_trade >= 0 ? "text-green-600" : "text-red-600"
                  )}>
                    {formatCurrency(strategy.avg_trade)}
                  </span>
                </div>

                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Sharpe Ratio</span>
                  <span className={cn("font-medium",
                    strategy.sharpe_ratio > 1 ? "text-green-600" : 
                    strategy.sharpe_ratio > 0 ? "text-yellow-600" : "text-red-600"
                  )}>
                    {strategy.sharpe_ratio.toFixed(2)}
                  </span>
                </div>

                <div className="flex justify-between">
                  <span className="text-sm text-muted-foreground">Open Positions</span>
                  <span className="font-medium">{strategy.current_positions}</span>
                </div>
              </div>

              {/* Last Trade */}
              <div className="pt-3 border-t">
                <div className="text-xs text-muted-foreground">
                  Last trade: {new Date(strategy.last_trade).toLocaleString()}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Performance Chart */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle>Performance Timeline</CardTitle>
              <CardDescription>Strategy performance over time</CardDescription>
            </div>
            <Select value={selectedStrategy} onValueChange={setSelectedStrategy}>
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Strategies</SelectItem>
                {strategies.map(strategy => (
                  <SelectItem key={strategy.name} value={strategy.name}>
                    {strategy.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={filteredPerformanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip 
                  formatter={(value, name) => [
                    name === 'pnl' ? formatCurrency(value as number) : value,
                    name === 'pnl' ? 'P&L' : name
                  ]}
                />
                <Line 
                  type="monotone" 
                  dataKey="pnl" 
                  stroke="#8884d8" 
                  strokeWidth={2}
                  dot={{ r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Strategy Comparison */}
        <Card>
          <CardHeader>
            <CardTitle>Strategy Comparison</CardTitle>
            <CardDescription>Comparative analysis of strategy metrics</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={comparisonData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="metric" />
                  <PolarRadiusAxis />
                  {strategies.slice(0, 3).map((strategy, index) => (
                    <Radar
                      key={strategy.name}
                      name={strategy.name}
                      dataKey={strategy.name}
                      stroke={`hsl(${index * 120}, 70%, 50%)`}
                      fill={`hsl(${index * 120}, 70%, 50%)`}
                      fillOpacity={0.2}
                    />
                  ))}
                  <Tooltip />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Trade Volume by Strategy */}
        <Card>
          <CardHeader>
            <CardTitle>Trade Volume</CardTitle>
            <CardDescription>Number of trades executed by each strategy</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={strategies}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="total_trades" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Strategy Rankings */}
      <Card>
        <CardHeader>
          <CardTitle>Strategy Rankings</CardTitle>
          <CardDescription>Performance ranking based on key metrics</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* By Total P&L */}
            <div>
              <h4 className="font-medium mb-3">By Total P&L</h4>
              <div className="space-y-2">
                {[...strategies]
                  .sort((a, b) => b.total_pnl - a.total_pnl)
                  .map((strategy, index) => (
                    <div key={strategy.name} className="flex items-center justify-between p-2 border rounded">
                      <div className="flex items-center gap-3">
                        <Badge variant="outline">#{index + 1}</Badge>
                        <span className="font-medium">{strategy.name}</span>
                        <Badge className={getStatusColor(strategy.status)}>
                          {strategy.status}
                        </Badge>
                      </div>
                      <div className={cn("font-semibold", 
                        strategy.total_pnl >= 0 ? "text-green-600" : "text-red-600"
                      )}>
                        {formatCurrency(strategy.total_pnl)}
                      </div>
                    </div>
                  ))}
              </div>
            </div>

            {/* By Win Rate */}
            <div>
              <h4 className="font-medium mb-3">By Win Rate</h4>
              <div className="space-y-2">
                {[...strategies]
                  .sort((a, b) => b.win_rate - a.win_rate)
                  .map((strategy, index) => (
                    <div key={strategy.name} className="flex items-center justify-between p-2 border rounded">
                      <div className="flex items-center gap-3">
                        <Badge variant="outline">#{index + 1}</Badge>
                        <span className="font-medium">{strategy.name}</span>
                      </div>
                      <div className="font-semibold">
                        {strategy.win_rate.toFixed(1)}%
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}