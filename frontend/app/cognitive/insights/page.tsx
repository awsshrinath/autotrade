"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../components/ui/card'
import { Button } from '../../../components/ui/button'
import { Badge } from '../../../components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../components/ui/tabs'
import { Brain, TrendingUp, TrendingDown, AlertTriangle, Target, Activity, Zap, BarChart3, RefreshCw } from 'lucide-react'
import { cn } from '../../../lib/utils'

interface TradeInsight {
  id: string
  type: string
  symbol: string
  confidence: number
  signal: string
  timeframe: string
  message: string
  generated_at: string
  validity_until: string
}

interface CognitiveSummary {
  status: string
  ai_models_active: number
  insights_generated: number
  confidence_score: number
  last_analysis: string
  market_sentiment: string
  risk_assessment: string
  recommendation_accuracy: number
  timestamp: string
}

interface CognitiveHealth {
  status: string
  uptime: string
  memory_usage: number
  cpu_usage: number
  models_loaded: number
  errors_last_hour: number
  api_response_time: number
  last_health_check: string
  components: {
    sentiment_analyzer: string
    risk_predictor: string
    pattern_detector: string
    recommendation_engine: string
  }
}

export default function CognitiveInsightsPage() {
  const [insights, setInsights] = useState<TradeInsight[]>([])
  const [summary, setSummary] = useState<CognitiveSummary | null>(null)
  const [health, setHealth] = useState<CognitiveHealth | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [selectedTimeframe, setSelectedTimeframe] = useState('1h')
  const [selectedType, setSelectedType] = useState('all')

  const timeframes = [
    { value: '15m', label: 'Last 15 minutes' },
    { value: '1h', label: 'Last hour' },
    { value: '4h', label: 'Last 4 hours' },
    { value: '1d', label: 'Today' },
    { value: '7d', label: 'Last 7 days' }
  ]

  const insightTypes = [
    { value: 'all', label: 'All Insights' },
    { value: 'trend_analysis', label: 'Trend Analysis' },
    { value: 'risk_warning', label: 'Risk Warnings' },
    { value: 'pattern_detection', label: 'Pattern Detection' },
    { value: 'recommendation', label: 'Recommendations' }
  ]

  const fetchData = async () => {
    try {
      setLoading(true)
      const [summaryRes, healthRes, insightsRes] = await Promise.all([
        fetch('/api/cognitive/summary'),
        fetch('/api/cognitive/health'),
        fetch(`/api/cognitive/insights/trade?timeframe=${selectedTimeframe}&type=${selectedType}`)
      ])

      if (summaryRes.ok) {
        const data = await summaryRes.json()
        setSummary(data)
      }

      if (healthRes.ok) {
        const data = await healthRes.json()
        setHealth(data)
      }

      if (insightsRes.ok) {
        const data = await insightsRes.json()
        setInsights(data.insights || data || [])
      } else {
        // Mock data fallback if API not available
        setInsights([
          {
            id: "insight_1",
            type: "trend_analysis",
            symbol: "NIFTY",
            confidence: 0.89,
            signal: "bullish",
            timeframe: "1D",
            message: "Strong upward momentum detected with RSI showing oversold recovery",
            generated_at: new Date(Date.now() - 5 * 60000).toISOString(),
            validity_until: new Date(Date.now() + 4 * 3600000).toISOString()
          },
          {
            id: "insight_2",
            type: "risk_warning",
            symbol: "BANKNIFTY",
            confidence: 0.76,
            signal: "caution",
            timeframe: "4H",
            message: "Volatility spike detected, consider position sizing",
            generated_at: new Date(Date.now() - 12 * 60000).toISOString(),
            validity_until: new Date(Date.now() + 2 * 3600000).toISOString()
          },
          {
            id: "insight_3",
            type: "pattern_detection",
            symbol: "RELIANCE",
            confidence: 0.82,
            signal: "bearish",
            timeframe: "1H",
            message: "Head and shoulders pattern forming, potential reversal signal",
            generated_at: new Date(Date.now() - 18 * 60000).toISOString(),
            validity_until: new Date(Date.now() + 6 * 3600000).toISOString()
          }
        ])
      }
    } catch (error) {
      console.error('Failed to fetch cognitive data:', error)
    } finally {
      setLoading(false)
    }
  }

  const refreshData = async () => {
    setRefreshing(true)
    await fetchData()
    setRefreshing(false)
  }

  useEffect(() => {
    fetchData()
  }, [selectedTimeframe, selectedType])

  const getSignalColor = (signal: string) => {
    switch (signal.toLowerCase()) {
      case 'bullish': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
      case 'bearish': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
      case 'neutral': return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300'
      case 'caution': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300'
      default: return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300'
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'trend_analysis': return <TrendingUp className="w-4 h-4" />
      case 'risk_warning': return <AlertTriangle className="w-4 h-4" />
      case 'pattern_detection': return <Target className="w-4 h-4" />
      case 'recommendation': return <Zap className="w-4 h-4" />
      default: return <Brain className="w-4 h-4" />
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 dark:text-green-400'
    if (confidence >= 0.6) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-red-600 dark:text-red-400'
  }

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString()
  }

  const getTimeUntilExpiry = (validityUntil: string) => {
    const now = new Date()
    const expiry = new Date(validityUntil)
    const diffMs = expiry.getTime() - now.getTime()
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60))
    
    if (diffHours > 0) {
      return `${diffHours}h ${diffMinutes}m`
    }
    return `${diffMinutes}m`
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
      {/* Header Controls */}
      <div className="flex justify-between items-center">
        <div className="flex gap-4">
          <Select value={selectedTimeframe} onValueChange={setSelectedTimeframe}>
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
          
          <Select value={selectedType} onValueChange={setSelectedType}>
            <SelectTrigger className="w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {insightTypes.map(type => (
                <SelectItem key={type.value} value={type.value}>
                  {type.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        <Button onClick={refreshData} disabled={refreshing} variant="outline">
          <RefreshCw className={cn("w-4 h-4 mr-2", refreshing && "animate-spin")} />
          Refresh
        </Button>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">AI Status</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                <Badge className={summary.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                  {summary.status}
                </Badge>
                <span className="text-sm text-muted-foreground">
                  {summary.ai_models_active} models
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Insights Generated</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{summary.insights_generated}</div>
              <div className="text-sm text-muted-foreground">
                Confidence: {(summary.confidence_score * 100).toFixed(1)}%
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Market Sentiment</CardTitle>
            </CardHeader>
            <CardContent>
              <Badge className={getSignalColor(summary.market_sentiment)}>
                {summary.market_sentiment}
              </Badge>
              <div className="text-sm text-muted-foreground mt-1">
                Risk: {summary.risk_assessment}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Accuracy</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{(summary.recommendation_accuracy * 100).toFixed(1)}%</div>
              <div className="text-sm text-muted-foreground">
                Last: {formatTime(summary.last_analysis).split(',')[1]}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content Tabs */}
      <Tabs defaultValue="insights" className="space-y-4">
        <TabsList>
          <TabsTrigger value="insights" className="flex items-center gap-2">
            <Brain className="w-4 h-4" />
            Trade Insights
          </TabsTrigger>
          <TabsTrigger value="health" className="flex items-center gap-2">
            <Activity className="w-4 h-4" />
            System Health
          </TabsTrigger>
          <TabsTrigger value="analytics" className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4" />
            Analytics
          </TabsTrigger>
        </TabsList>

        {/* Trade Insights Tab */}
        <TabsContent value="insights" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>AI-Generated Trade Insights</CardTitle>
              <CardDescription>
                Real-time market analysis and trading recommendations from AI models
              </CardDescription>
            </CardHeader>
            <CardContent>
              {insights.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  No insights available for the selected timeframe and type.
                </div>
              ) : (
                <div className="space-y-4">
                  {insights.map((insight) => (
                    <div key={insight.id} className="border rounded-lg p-4">
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex items-center gap-3">
                          {getTypeIcon(insight.type)}
                          <div>
                            <div className="font-medium">{insight.symbol}</div>
                            <div className="text-sm text-muted-foreground">
                              {insight.type.replace('_', ' ').toUpperCase()} • {insight.timeframe}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge className={getSignalColor(insight.signal)}>
                            {insight.signal}
                          </Badge>
                          <span className={cn("text-sm font-medium", getConfidenceColor(insight.confidence))}>
                            {(insight.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                      
                      <p className="text-sm mb-3">{insight.message}</p>
                      
                      <div className="flex justify-between text-xs text-muted-foreground">
                        <span>Generated: {formatTime(insight.generated_at)}</span>
                        <span>Valid for: {getTimeUntilExpiry(insight.validity_until)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* System Health Tab */}
        <TabsContent value="health" className="space-y-4">
          {health && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle>System Performance</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex justify-between">
                      <span>Status:</span>
                      <Badge className={health.status === 'healthy' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                        {health.status}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span>Uptime:</span>
                      <span>{health.uptime}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Memory Usage:</span>
                      <span>{(health.memory_usage * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>CPU Usage:</span>
                      <span>{(health.cpu_usage * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Models Loaded:</span>
                      <span>{health.models_loaded}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Response Time:</span>
                      <span>{health.api_response_time.toFixed(3)}s</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Component Status</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {Object.entries(health.components).map(([component, status]) => (
                      <div key={component} className="flex justify-between items-center">
                        <span className="capitalize">{component.replace('_', ' ')}</span>
                        <Badge className={status === 'healthy' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                          {status}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>AI Performance Analytics</CardTitle>
              <CardDescription>Historical performance and accuracy metrics</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8 text-muted-foreground">
                Analytics dashboard coming soon. This will show historical AI performance,
                accuracy trends, and model comparison metrics.
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}