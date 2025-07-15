"use client"

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../components/ui/card'
import { Button } from '../../../components/ui/button'
import { Badge } from '../../../components/ui/badge'
import { Progress } from '../../../components/ui/progress'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { CheckCircle, AlertCircle, XCircle, Server, Database, Cloud, Cpu, MemoryStick, HardDrive, Wifi, RefreshCw } from 'lucide-react'
import { cn } from '../../../lib/utils'
import apiClient, { handleApiError } from '@/lib/api-error-handler'

interface ServiceStatus {
  name: string
  status: 'healthy' | 'warning' | 'error'
  uptime: number
  last_check: string
  response_time: number
  error_count: number
  description: string
  endpoint?: string
}

interface SystemMetric {
  timestamp: string
  cpu_usage: number
  memory_usage: number
  disk_usage: number
  network_io: number
}

interface ResourceUsage {
  cpu: {
    current: number
    average: number
    peak: number
  }
  memory: {
    used: number
    total: number
    percentage: number
  }
  disk: {
    used: number
    total: number
    percentage: number
  }
  network: {
    bytes_in: number
    bytes_out: number
  }
}

export default function SystemHealthPage() {
  const [services, setServices] = useState<ServiceStatus[]>([])
  const [metrics, setMetrics] = useState<SystemMetric[]>([])
  const [resources, setResources] = useState<ResourceUsage | null>(null)
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

  // Fetch system health data
  const fetchHealthData = async () => {
    try {
      // Use enhanced API client with fallback disabled in production
      const isProduction = process.env.NEXT_PUBLIC_ENV === 'production'
      const options = { useFallback: !isProduction }
      
      const [servicesData, metricsData, resourcesData] = await Promise.all([
        apiClient.get<{services: ServiceStatus[]}>('/api/v1/system/health/services', options),
        apiClient.get<{metrics: SystemMetric[]}>('/api/v1/system/health/metrics', options),
        apiClient.get<{resources: ResourceUsage}>('/api/v1/system/health/resources', options)
      ])

      setServices(servicesData.services || [])
      setMetrics(metricsData.metrics || [])
      setResources(resourcesData.resources)
      setLastUpdate(new Date())
      
    } catch (error) {
      console.error('Failed to fetch health data:', error)
      
      // In production mode, show appropriate error message and reset data
      if (process.env.NEXT_PUBLIC_ENV === 'production') {
        console.warn(handleApiError(error, 'System health monitoring'))
        setServices([])
        setMetrics([])
        setResources(null)
      }
    } finally {
      setLoading(false)
    }
  }

  // Restart service
  const restartService = async (serviceName: string) => {
    try {
      const options = { useFallback: false } // Never use fallback for service actions
      await apiClient.post(`/api/v1/system/health/services/${serviceName}/restart`, {}, options)
      
      alert(`${serviceName} restart initiated`)
      fetchHealthData()
      }
    } catch (error) {
      console.error('Failed to restart service:', error)
      alert('Failed to restart service')
    }
  }

  useEffect(() => {
    fetchHealthData()
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchHealthData, 30000)
    return () => clearInterval(interval)
  }, [])

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="w-4 h-4 text-green-600" />
      case 'warning': return <AlertCircle className="w-4 h-4 text-yellow-600" />
      case 'error': return <XCircle className="w-4 h-4 text-red-600" />
      default: return <AlertCircle className="w-4 h-4 text-gray-600" />
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'healthy': return <Badge className="bg-green-100 text-green-800">Healthy</Badge>
      case 'warning': return <Badge className="bg-yellow-100 text-yellow-800">Warning</Badge>
      case 'error': return <Badge className="bg-red-100 text-red-800">Error</Badge>
      default: return <Badge variant="secondary">Unknown</Badge>
    }
  }

  const getServiceIcon = (serviceName: string) => {
    if (serviceName.includes('database') || serviceName.includes('db')) {
      return <Database className="w-5 h-5" />
    }
    if (serviceName.includes('api') || serviceName.includes('backend')) {
      return <Server className="w-5 h-5" />
    }
    if (serviceName.includes('cloud') || serviceName.includes('gcp')) {
      return <Cloud className="w-5 h-5" />
    }
    return <Server className="w-5 h-5" />
  }

  const formatBytes = (bytes: number) => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
    if (bytes === 0) return '0 Bytes'
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
  }

  const formatUptime = (hours: number) => {
    const days = Math.floor(hours / 24)
    const remainingHours = Math.floor(hours % 24)
    if (days > 0) {
      return `${days}d ${remainingHours}h`
    }
    return `${remainingHours}h`
  }

  const getOverallHealth = () => {
    const healthyCount = services.filter(s => s.status === 'healthy').length
    const totalCount = services.length
    if (totalCount === 0) return 'unknown'
    if (healthyCount === totalCount) return 'healthy'
    if (services.some(s => s.status === 'error')) return 'error'
    return 'warning'
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
          <h1 className="text-3xl font-bold">System Health</h1>
          <p className="text-muted-foreground">
            Comprehensive system monitoring and health checks
          </p>
        </div>
        <div className="flex gap-2 items-center">
          <span className="text-sm text-muted-foreground">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </span>
          <Button variant="outline" onClick={fetchHealthData}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Overall Status */}
      <Card className={cn(
        "border-2",
        getOverallHealth() === 'healthy' ? "border-green-200 bg-green-50" :
        getOverallHealth() === 'warning' ? "border-yellow-200 bg-yellow-50" :
        getOverallHealth() === 'error' ? "border-red-200 bg-red-50" : "border-gray-200"
      )}>
        <CardHeader>
          <div className="flex items-center gap-3">
            {getStatusIcon(getOverallHealth())}
            <div>
              <CardTitle className="text-lg">System Status</CardTitle>
              <CardDescription>
                {services.filter(s => s.status === 'healthy').length} of {services.length} services healthy
              </CardDescription>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Resource Usage */}
      {resources && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Cpu className="w-4 h-4" />
                CPU Usage
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="text-2xl font-bold">{resources.cpu.current.toFixed(1)}%</div>
                <Progress value={resources.cpu.current} className="h-2" />
                <div className="text-xs text-muted-foreground">
                  Avg: {resources.cpu.average.toFixed(1)}% | Peak: {resources.cpu.peak.toFixed(1)}%
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <MemoryStick className="w-4 h-4" />
                Memory Usage
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="text-2xl font-bold">{resources.memory.percentage.toFixed(1)}%</div>
                <Progress value={resources.memory.percentage} className="h-2" />
                <div className="text-xs text-muted-foreground">
                  {formatBytes(resources.memory.used)} / {formatBytes(resources.memory.total)}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <HardDrive className="w-4 h-4" />
                Disk Usage
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="text-2xl font-bold">{resources.disk.percentage.toFixed(1)}%</div>
                <Progress value={resources.disk.percentage} className="h-2" />
                <div className="text-xs text-muted-foreground">
                  {formatBytes(resources.disk.used)} / {formatBytes(resources.disk.total)}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Wifi className="w-4 h-4" />
                Network I/O
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="text-sm">
                  <div className="flex justify-between">
                    <span>In:</span>
                    <span className="font-medium">{formatBytes(resources.network.bytes_in)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Out:</span>
                    <span className="font-medium">{formatBytes(resources.network.bytes_out)}</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Performance Metrics Chart */}
      <Card>
        <CardHeader>
          <CardTitle>Performance Metrics</CardTitle>
          <CardDescription>Real-time system performance over time</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={metrics}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="timestamp" 
                  tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                />
                <YAxis />
                <Tooltip 
                  labelFormatter={(value) => new Date(value).toLocaleString()}
                  formatter={(value: number, name: string) => [
                    `${value.toFixed(1)}%`,
                    name.replace('_', ' ').toUpperCase()
                  ]}
                />
                <Line type="monotone" dataKey="cpu_usage" stroke="#8884d8" strokeWidth={2} />
                <Line type="monotone" dataKey="memory_usage" stroke="#82ca9d" strokeWidth={2} />
                <Line type="monotone" dataKey="disk_usage" stroke="#ffc658" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Service Status */}
      <Card>
        <CardHeader>
          <CardTitle>Service Status</CardTitle>
          <CardDescription>Health status of all system services</CardDescription>
        </CardHeader>
        <CardContent>
          {services.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No services to monitor
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {services.map((service) => (
                <div key={service.name} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center gap-4">
                    {getServiceIcon(service.name)}
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold">{service.name}</h3>
                        {getStatusBadge(service.status)}
                      </div>
                      <p className="text-sm text-muted-foreground mb-2">{service.description}</p>
                      <div className="flex gap-4 text-xs text-muted-foreground">
                        <span>Uptime: {formatUptime(service.uptime)}</span>
                        <span>Response: {service.response_time}ms</span>
                        {service.error_count > 0 && (
                          <span className="text-red-600">Errors: {service.error_count}</span>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    {getStatusIcon(service.status)}
                    {service.status === 'error' && (
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => restartService(service.name)}
                      >
                        Restart
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Common system maintenance tasks</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button variant="outline" className="h-auto p-4">
              <div className="text-center">
                <RefreshCw className="w-6 h-6 mx-auto mb-2" />
                <div className="font-medium">Restart All Services</div>
                <div className="text-xs text-muted-foreground mt-1">
                  Restart all failed services
                </div>
              </div>
            </Button>
            
            <Button variant="outline" className="h-auto p-4">
              <div className="text-center">
                <Database className="w-6 h-6 mx-auto mb-2" />
                <div className="font-medium">Clear Cache</div>
                <div className="text-xs text-muted-foreground mt-1">
                  Clear system cache and logs
                </div>
              </div>
            </Button>
            
            <Button variant="outline" className="h-auto p-4">
              <div className="text-center">
                <Server className="w-6 h-6 mx-auto mb-2" />
                <div className="font-medium">System Diagnostics</div>
                <div className="text-xs text-muted-foreground mt-1">
                  Run comprehensive health check
                </div>
              </div>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}