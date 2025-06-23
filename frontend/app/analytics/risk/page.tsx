"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../components/ui/card'
import { Badge } from '../../../components/ui/badge'
import { Button } from '../../../components/ui/button'
import { Progress } from '../../../components/ui/progress'
import { AlertTriangle, Shield, TrendingDown, Activity, Bell, BellOff } from 'lucide-react'
import { cn } from '../../../lib/utils'

interface RiskMetric {
  name: string
  value: number
  threshold: number
  status: 'safe' | 'warning' | 'danger'
  description: string
}

interface RiskAlert {
  id: string
  type: 'position_size' | 'drawdown' | 'exposure' | 'correlation'
  message: string
  severity: 'low' | 'medium' | 'high'
  timestamp: string
  acknowledged: boolean
}

interface PortfolioRisk {
  total_exposure: number
  max_exposure_limit: number
  current_drawdown: number
  max_drawdown_limit: number
  value_at_risk_1d: number
  value_at_risk_5d: number
  correlation_risk: number
  concentration_risk: number
}

export default function RiskMonitorPage() {
  const [riskMetrics, setRiskMetrics] = useState<RiskMetric[]>([])
  const [alerts, setAlerts] = useState<RiskAlert[]>([])
  const [portfolioRisk, setPortfolioRisk] = useState<PortfolioRisk | null>(null)
  const [loading, setLoading] = useState(true)
  const [alertsEnabled, setAlertsEnabled] = useState(true)

  // Fetch risk data
  const fetchRiskData = async () => {
    try {
      const [metricsRes, alertsRes, portfolioRes] = await Promise.all([
        fetch('http://localhost:8000/api/v1/risk/metrics'),
        fetch('http://localhost:8000/api/v1/risk/alerts'),
        fetch('http://localhost:8000/api/v1/risk/portfolio')
      ])

      if (metricsRes.ok) {
        const data = await metricsRes.json()
        setRiskMetrics(data.metrics || [])
      }

      if (alertsRes.ok) {
        const data = await alertsRes.json()
        setAlerts(data.alerts || [])
      }

      if (portfolioRes.ok) {
        const data = await portfolioRes.json()
        setPortfolioRisk(data)
      }
    } catch (error) {
      console.error('Failed to fetch risk data:', error)
    } finally {
      setLoading(false)
    }
  }

  // Acknowledge alert
  const acknowledgeAlert = async (alertId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/risk/alerts/${alertId}/acknowledge`, {
        method: 'POST'
      })
      if (response.ok) {
        setAlerts(prev => prev.map(alert => 
          alert.id === alertId ? { ...alert, acknowledged: true } : alert
        ))
      }
    } catch (error) {
      console.error('Failed to acknowledge alert:', error)
    }
  }

  // Toggle alert notifications
  const toggleAlerts = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/risk/alerts/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: !alertsEnabled })
      })
      if (response.ok) {
        setAlertsEnabled(!alertsEnabled)
      }
    } catch (error) {
      console.error('Failed to toggle alerts:', error)
    }
  }

  useEffect(() => {
    fetchRiskData()
    
    // Auto-refresh every 10 seconds
    const interval = setInterval(fetchRiskData, 10000)
    return () => clearInterval(interval)
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'safe': return 'text-green-600'
      case 'warning': return 'text-yellow-600'
      case 'danger': return 'text-red-600'
      default: return 'text-gray-600'
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'safe': return <Badge className="bg-green-100 text-green-800">Safe</Badge>
      case 'warning': return <Badge className="bg-yellow-100 text-yellow-800">Warning</Badge>
      case 'danger': return <Badge className="bg-red-100 text-red-800">Danger</Badge>
      default: return <Badge variant="secondary">Unknown</Badge>
    }
  }

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'high': return <AlertTriangle className="w-4 h-4 text-red-600" />
      case 'medium': return <Activity className="w-4 h-4 text-yellow-600" />
      case 'low': return <Shield className="w-4 h-4 text-blue-600" />
      default: return <Shield className="w-4 h-4" />
    }
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0
    }).format(amount)
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
          <h1 className="text-3xl font-bold">Risk Monitor</h1>
          <p className="text-muted-foreground">Real-time risk analysis and monitoring</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant={alertsEnabled ? "default" : "outline"}
            onClick={toggleAlerts}
          >
            {alertsEnabled ? <Bell className="w-4 h-4 mr-2" /> : <BellOff className="w-4 h-4 mr-2" />}
            {alertsEnabled ? 'Alerts On' : 'Alerts Off'}
          </Button>
        </div>
      </div>

      {/* Active Alerts */}
      {alerts.filter(alert => !alert.acknowledged).length > 0 && (
        <Card className="border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="w-5 h-5" />
              Active Risk Alerts ({alerts.filter(alert => !alert.acknowledged).length})
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {alerts.filter(alert => !alert.acknowledged).map((alert) => (
              <div key={alert.id} className="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-lg">
                <div className="flex items-center gap-3">
                  {getSeverityIcon(alert.severity)}
                  <div>
                    <div className="font-medium">{alert.message}</div>
                    <div className="text-sm text-muted-foreground">
                      {new Date(alert.timestamp).toLocaleString()}
                    </div>
                  </div>
                </div>
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={() => acknowledgeAlert(alert.id)}
                >
                  Acknowledge
                </Button>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Portfolio Risk Summary */}
      {portfolioRisk && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Portfolio Exposure</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="text-2xl font-bold">
                  {formatCurrency(portfolioRisk.total_exposure)}
                </div>
                <Progress 
                  value={(portfolioRisk.total_exposure / portfolioRisk.max_exposure_limit) * 100} 
                  className="h-2"
                />
                <div className="text-xs text-muted-foreground">
                  Limit: {formatCurrency(portfolioRisk.max_exposure_limit)}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Current Drawdown</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className={cn("text-2xl font-bold", 
                  portfolioRisk.current_drawdown > portfolioRisk.max_drawdown_limit ? "text-red-600" : "text-green-600"
                )}>
                  {portfolioRisk.current_drawdown.toFixed(2)}%
                </div>
                <Progress 
                  value={(portfolioRisk.current_drawdown / portfolioRisk.max_drawdown_limit) * 100} 
                  className="h-2"
                />
                <div className="text-xs text-muted-foreground">
                  Max Limit: {portfolioRisk.max_drawdown_limit}%
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Value at Risk (1D)</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="text-2xl font-bold text-red-600">
                  {formatCurrency(portfolioRisk.value_at_risk_1d)}
                </div>
                <div className="text-xs text-muted-foreground">
                  95% confidence level
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Concentration Risk</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className={cn("text-2xl font-bold",
                  portfolioRisk.concentration_risk > 0.3 ? "text-red-600" : 
                  portfolioRisk.concentration_risk > 0.2 ? "text-yellow-600" : "text-green-600"
                )}>
                  {(portfolioRisk.concentration_risk * 100).toFixed(1)}%
                </div>
                <div className="text-xs text-muted-foreground">
                  Largest position weight
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Risk Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Risk Metrics</CardTitle>
          <CardDescription>Key risk indicators and their current status</CardDescription>
        </CardHeader>
        <CardContent>
          {riskMetrics.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No risk metrics available
            </div>
          ) : (
            <div className="space-y-4">
              {riskMetrics.map((metric, index) => (
                <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold">{metric.name}</h3>
                      {getStatusBadge(metric.status)}
                    </div>
                    <p className="text-sm text-muted-foreground mb-3">{metric.description}</p>
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Current: <span className={getStatusColor(metric.status)}>{metric.value}</span></span>
                        <span>Threshold: {metric.threshold}</span>
                      </div>
                      <Progress 
                        value={(metric.value / metric.threshold) * 100} 
                        className="h-2"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Historical Alerts */}
      <Card>
        <CardHeader>
          <CardTitle>Alert History</CardTitle>
          <CardDescription>Recent risk alerts and their status</CardDescription>
        </CardHeader>
        <CardContent>
          {alerts.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No alerts to display
            </div>
          ) : (
            <div className="space-y-3">
              {alerts.map((alert) => (
                <div key={alert.id} className={cn(
                  "flex items-center justify-between p-3 border rounded-lg",
                  alert.acknowledged ? "opacity-60" : ""
                )}>
                  <div className="flex items-center gap-3">
                    {getSeverityIcon(alert.severity)}
                    <div>
                      <div className="font-medium">{alert.message}</div>
                      <div className="text-sm text-muted-foreground">
                        {new Date(alert.timestamp).toLocaleString()}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={alert.acknowledged ? "secondary" : "default"}>
                      {alert.acknowledged ? "Acknowledged" : "Active"}
                    </Badge>
                    {!alert.acknowledged && (
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => acknowledgeAlert(alert.id)}
                      >
                        Acknowledge
                      </Button>
                    )}
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