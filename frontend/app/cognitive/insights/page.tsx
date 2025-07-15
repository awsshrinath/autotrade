"use client"

import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../components/ui/card'
import { Button } from '../../../components/ui/button'
import { Badge } from '../../../components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../../components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../../components/ui/tabs'
import { Brain, TrendingUp, AlertTriangle, Target, Activity, Zap, RefreshCw, FileText, Trash2 } from 'lucide-react'
import { cn } from '../../../lib/utils'
import apiClient, { handleApiError } from '@/lib/api-error-handler'

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

interface LogSummary {
  summary: string
  key_insights: string[]
  error_count: number
  warning_count: number
  timestamp: string
  log_sources: string[]
  recommendations: string[]
}

interface MarketSentiment {
  sentiment: string
  confidence: number
  factors: string[]
  timestamp: string
  recommendation: string
}

interface CognitiveStatus {
  service_status: string
  openai_available: boolean
  models: {
    primary: string
    fallback: string
  }
  cache_stats: {
    size: number
    hit_rate: number
  }
  last_updated: string
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
  const [logSummary, setLogSummary] = useState<LogSummary | null>(null)
  const [marketSentiment, setMarketSentiment] = useState<MarketSentiment | null>(null)
  const [cognitiveStatus, setCognitiveStatus] = useState<CognitiveStatus | null>(null)
  const [summary] = useState<CognitiveSummary | null>(null)
  const [health] = useState<CognitiveHealth | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [summaryLoading, setSummaryLoading] = useState(false)
  const [sentimentLoading, setSentimentLoading] = useState(false)
  const [selectedTimeframe, setSelectedTimeframe] = useState('1h')
  const [selectedType, setSelectedType] = useState('all')
  const [logSource, setLogSource] = useState('all')

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

  const logSources = [
    { value: 'all', label: 'All Sources' },
    { value: 'gcs', label: 'GCS Logs' },
    { value: 'firestore', label: 'Firestore Logs' },
    { value: 'kubernetes', label: 'Kubernetes Logs' }
  ]

  const fetchCognitiveStatus = useCallback(async () => {
    try {
      // Use enhanced API client with fallback disabled in production
      const isProduction = process.env.NEXT_PUBLIC_ENV === 'production'
      const options = { useFallback: !isProduction }
      
      const data = await apiClient.get<CognitiveStatus>('/api/v1/cognitive/summary', options)
      setCognitiveStatus(data)
    } catch (error) {
      console.error('Failed to fetch cognitive status:', error)
      
      // In production mode, show appropriate error message
      if (process.env.NEXT_PUBLIC_ENV === 'production') {
        console.warn(handleApiError(error, 'Cognitive analysis'))
        setCognitiveStatus(null)
      }
    }
  }, [])

  const fetchLogSummary = useCallback(async () => {
    try {
      setSummaryLoading(true)
      const params = new URLSearchParams({
        timeframe: selectedTimeframe,
        ...(logSource !== 'all' && { source: logSource })
      })
      
      // Use enhanced API client with fallback disabled in production
      const isProduction = process.env.NEXT_PUBLIC_ENV === 'production'
      const options = { useFallback: !isProduction }
      
      const data = await apiClient.get<LogSummary>(`/api/v1/cognitive/logs/summary?${params}`, options)
      setLogSummary(data)
      
    } catch (error) {
      console.error('Failed to fetch log summary:', error)
      
      // In production mode, show appropriate error message
      if (process.env.NEXT_PUBLIC_ENV === 'production') {
        console.warn(handleApiError(error, 'Log analysis'))
        setLogSummary(null)
      }
    } finally {
      setSummaryLoading(false)
    }
  }, [selectedTimeframe, logSource])

  const fetchMarketSentiment = useCallback(async () => {
    try {
      setSentimentLoading(true)
      
      // Use enhanced API client with fallback disabled in production
      const isProduction = process.env.NEXT_PUBLIC_ENV === 'production'
      const options = { useFallback: !isProduction }
      
      const data = await apiClient.get<MarketSentiment>('/api/v1/cognitive/market/sentiment', options)
      setMarketSentiment(data)
      
    } catch (error) {
      console.error('Failed to fetch market sentiment:', error)
      
      // In production mode, show appropriate error message
      if (process.env.NEXT_PUBLIC_ENV === 'production') {
        console.warn(handleApiError(error, 'Market sentiment analysis'))
        setMarketSentiment(null)
      }
    } finally {
      setSentimentLoading(false)
    }
  }, [])

  const clearCache = useCallback(async () => {
    try {
      const options = { useFallback: false } // Never use fallback for cache actions
      await apiClient.post('/api/v1/cognitive/cache/clear', {}, options)
      
      // Refresh data after clearing cache
      await Promise.all([fetchCognitiveStatus(), fetchLogSummary(), fetchMarketSentiment()])
    } catch (error) {
      console.error('Failed to clear cache:', error)
      console.warn(handleApiError(error, 'Cache management'))
    }
  }, [fetchCognitiveStatus, fetchLogSummary, fetchMarketSentiment])

  const fetchData = useCallback(async () => {
    try {
      setLoading(true)
      
      // Fetch new AI-powered data
      await Promise.all([
        fetchCognitiveStatus(),
        fetchLogSummary(), 
        fetchMarketSentiment()
      ])

      // Legacy endpoints for trade insights (keep existing mock data for now)
      const insights = [
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
      ]
      setInsights(insights)

    } catch (error) {
      console.error('Failed to fetch cognitive data:', error)
    } finally {
      setLoading(false)
    }
  }, [fetchCognitiveStatus, fetchLogSummary, fetchMarketSentiment, selectedTimeframe, selectedType])

  const refreshData = async () => {
    setRefreshing(true)
    await fetchData()
    setRefreshing(false)
  }

  useEffect(() => {
    fetchData()
  }, [selectedTimeframe, selectedType, logSource, fetchData])

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
          
          <Select value={logSource} onValueChange={setLogSource}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {logSources.map(source => (
                <SelectItem key={source.value} value={source.value}>
                  {source.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        
        <div className="flex gap-2">
          <Button onClick={clearCache} variant="outline" size="sm">
            <Trash2 className="w-4 h-4 mr-2" />
            Clear Cache
          </Button>
          <Button onClick={refreshData} disabled={refreshing} variant="outline">
            <RefreshCw className={cn("w-4 h-4 mr-2", refreshing && "animate-spin")} />
            Refresh
          </Button>
        </div>
      </div>

      {/* AI-Powered Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Cognitive Service Status */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">AI Service</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <Badge className={cognitiveStatus?.service_status === 'healthy' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                {cognitiveStatus?.service_status || 'Unknown'}
              </Badge>
              <span className="text-sm text-muted-foreground">
                {cognitiveStatus?.openai_available ? 'OpenAI Ready' : 'Offline'}
              </span>
            </div>
            {cognitiveStatus && (
              <div className="text-xs text-muted-foreground mt-1">
                {cognitiveStatus.models.primary} / {cognitiveStatus.models.fallback}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Market Sentiment */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Market Sentiment</CardTitle>
          </CardHeader>
          <CardContent>
            {sentimentLoading ? (
              <div className="animate-pulse">
                <div className="h-6 bg-gray-200 rounded mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-2/3"></div>
              </div>
            ) : marketSentiment ? (
              <>
                <Badge className={getSignalColor(marketSentiment.sentiment)}>
                  {marketSentiment.sentiment}
                </Badge>
                <div className="text-sm text-muted-foreground mt-1">
                  Confidence: {(marketSentiment.confidence * 100).toFixed(0)}%
                </div>
              </>
            ) : (
              <div className="text-sm text-muted-foreground">Loading...</div>
            )}
          </CardContent>
        </Card>

        {/* Log Summary Stats */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">System Health</CardTitle>
          </CardHeader>
          <CardContent>
            {summaryLoading ? (
              <div className="animate-pulse">
                <div className="h-6 bg-gray-200 rounded mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-2/3"></div>
              </div>
            ) : logSummary ? (
              <>
                <div className="flex items-center gap-2">
                  <span className={cn("text-lg font-bold", logSummary.error_count > 0 ? "text-red-600" : "text-green-600")}>
                    {logSummary.error_count}
                  </span>
                  <span className="text-sm text-muted-foreground">errors</span>
                </div>
                <div className="text-sm text-muted-foreground">
                  {logSummary.warning_count} warnings
                </div>
              </>
            ) : (
              <div className="text-sm text-muted-foreground">Loading...</div>
            )}
          </CardContent>
        </Card>

        {/* Cache Performance */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Cache Stats</CardTitle>
          </CardHeader>
          <CardContent>
            {cognitiveStatus ? (
              <>
                <div className="text-2xl font-bold">{cognitiveStatus.cache_stats.size}</div>
                <div className="text-sm text-muted-foreground">
                  Hit Rate: {(cognitiveStatus.cache_stats.hit_rate * 100).toFixed(1)}%
                </div>
              </>
            ) : (
              <div className="text-sm text-muted-foreground">Loading...</div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="summary" className="space-y-4">
        <TabsList>
          <TabsTrigger value="summary" className="flex items-center gap-2">
            <FileText className="w-4 h-4" />
            AI Log Summary
          </TabsTrigger>
          <TabsTrigger value="sentiment" className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            Market Sentiment
          </TabsTrigger>
          <TabsTrigger value="insights" className="flex items-center gap-2">
            <Brain className="w-4 h-4" />
            Trade Insights
          </TabsTrigger>
          <TabsTrigger value="health" className="flex items-center gap-2">
            <Activity className="w-4 h-4" />
            System Health
          </TabsTrigger>
        </TabsList>

        {/* AI Log Summary Tab */}
        <TabsContent value="summary" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>AI-Powered Log Analysis</CardTitle>
              <CardDescription>
                Intelligent summary and insights from system logs using GPT analysis
              </CardDescription>
            </CardHeader>
            <CardContent>
              {summaryLoading ? (
                <div className="space-y-4">
                  <div className="animate-pulse">
                    <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                    <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
                    <div className="h-20 bg-gray-200 rounded mb-4"></div>
                  </div>
                </div>
              ) : logSummary ? (
                <div className="space-y-6">
                  {/* Summary Overview */}
                  <div>
                    <h4 className="font-medium mb-2">System Overview</h4>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {logSummary.summary}
                    </p>
                  </div>

                  {/* Key Insights */}
                  <div>
                    <h4 className="font-medium mb-3">Key Insights</h4>
                    <div className="space-y-2">
                      {logSummary.key_insights.map((insight, index) => (
                        <div key={index} className="flex items-start gap-2">
                          <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                          <span className="text-sm">{insight}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Recommendations */}
                  {logSummary.recommendations.length > 0 && (
                    <div>
                      <h4 className="font-medium mb-3">AI Recommendations</h4>
                      <div className="space-y-2">
                        {logSummary.recommendations.map((rec, index) => (
                          <div key={index} className="flex items-start gap-2">
                            <Zap className="w-4 h-4 text-yellow-500 mt-0.5 flex-shrink-0" />
                            <span className="text-sm">{rec}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Metadata */}
                  <div className="border-t pt-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <div className="font-medium">Log Sources</div>
                        <div className="text-muted-foreground">
                          {logSummary.log_sources.join(', ')}
                        </div>
                      </div>
                      <div>
                        <div className="font-medium">Errors</div>
                        <div className={cn("font-medium", logSummary.error_count > 0 ? "text-red-600" : "text-green-600")}>
                          {logSummary.error_count}
                        </div>
                      </div>
                      <div>
                        <div className="font-medium">Warnings</div>
                        <div className="text-yellow-600 font-medium">{logSummary.warning_count}</div>
                      </div>
                      <div>
                        <div className="font-medium">Generated</div>
                        <div className="text-muted-foreground">
                          {formatTime(logSummary.timestamp).split(',')[1]}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No log summary available. Click refresh to generate analysis.
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Market Sentiment Tab */}
        <TabsContent value="sentiment" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>AI Market Sentiment Analysis</CardTitle>
              <CardDescription>
                Real-time market sentiment analysis powered by GPT models
              </CardDescription>
            </CardHeader>
            <CardContent>
              {sentimentLoading ? (
                <div className="space-y-4">
                  <div className="animate-pulse">
                    <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
                    <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                    <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
                    <div className="h-16 bg-gray-200 rounded"></div>
                  </div>
                </div>
              ) : marketSentiment ? (
                <div className="space-y-6">
                  {/* Sentiment Overview */}
                  <div className="flex items-center gap-4">
                    <div>
                      <h4 className="font-medium mb-1">Current Sentiment</h4>
                      <Badge className={cn(getSignalColor(marketSentiment.sentiment), "text-base px-3 py-1")}>
                        {marketSentiment.sentiment.toUpperCase()}
                      </Badge>
                    </div>
                    <div>
                      <h4 className="font-medium mb-1">Confidence</h4>
                      <div className={cn("text-2xl font-bold", getConfidenceColor(marketSentiment.confidence))}>
                        {(marketSentiment.confidence * 100).toFixed(0)}%
                      </div>
                    </div>
                  </div>

                  {/* Key Factors */}
                  <div>
                    <h4 className="font-medium mb-3">Contributing Factors</h4>
                    <div className="space-y-2">
                      {marketSentiment.factors.map((factor, index) => (
                        <div key={index} className="flex items-start gap-2">
                          <div className="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0"></div>
                          <span className="text-sm">{factor}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* AI Recommendation */}
                  <div className="bg-muted/50 p-4 rounded-lg">
                    <h4 className="font-medium mb-2 flex items-center gap-2">
                      <Brain className="w-4 h-4" />
                      AI Recommendation
                    </h4>
                    <p className="text-sm">{marketSentiment.recommendation}</p>
                  </div>

                  {/* Timestamp */}
                  <div className="text-sm text-muted-foreground">
                    Last updated: {formatTime(marketSentiment.timestamp)}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No market sentiment data available. Click refresh to analyze current market conditions.
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

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


      </Tabs>
    </div>
  )
}