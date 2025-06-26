"use client"

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card'
import { Button } from '../ui/button'
import { Input } from '../ui/input'
import { Label } from '../ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select'
import { Badge } from '../ui/badge'
import { TrendingUp, TrendingDown, DollarSign, Target, StopCircle } from 'lucide-react'
import { cn } from '../../lib/utils'

interface TradeFormData {
  symbol: string
  side: 'BUY' | 'SELL'
  quantity: number
  orderType: 'MARKET' | 'LIMIT'
  price?: number
  stopLoss?: number
  target?: number
  strategy: string
}

interface TradingInterfaceProps {
  onTradeSubmit?: (trade: TradeFormData) => void
}

export default function TradingInterface({ onTradeSubmit }: TradingInterfaceProps) {
  const [formData, setFormData] = useState<TradeFormData>({
    symbol: '',
    side: 'BUY',
    quantity: 0,
    orderType: 'MARKET',
    strategy: 'manual'
  })
  const [loading, setLoading] = useState(false)
  const [lastTrade, setLastTrade] = useState<any>(null)

  const strategies = [
    { value: 'manual', label: 'Manual Trading' },
    { value: 'momentum', label: 'Momentum Strategy' },
    { value: 'mean_reversion', label: 'Mean Reversion' },
    { value: 'breakout', label: 'Breakout Strategy' },
    { value: 'scalping', label: 'Scalping' }
  ]

  const popularSymbols = [
    'NIFTY', 'BANKNIFTY', 'RELIANCE', 'TCS', 'INFY', 'HDFC', 'SBIN', 'ITC'
  ]

  const handleInputChange = (field: keyof TradeFormData, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleSubmitTrade = async () => {
    if (!formData.symbol || !formData.quantity) {
      alert('Please fill in all required fields')
      return
    }

    setLoading(true)
    try {
      const payload = {
        symbol: formData.symbol.toUpperCase(),
        side: formData.side,
        quantity: formData.quantity,
        order_type: formData.orderType,
        price: formData.orderType === 'LIMIT' ? formData.price : undefined,
        stop_loss: formData.stopLoss,
        target: formData.target,
        strategy: formData.strategy
      }

      const response = await fetch('http://localhost:8000/api/v1/trade/manual', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      })

      if (response.ok) {
        const result = await response.json()
        setLastTrade(result)
        alert(`Trade submitted successfully! Order ID: ${result.order_id}`)
        
        // Reset form
        setFormData({
          symbol: '',
          side: 'BUY',
          quantity: 0,
          orderType: 'MARKET',
          strategy: 'manual'
        })

        if (onTradeSubmit) {
          onTradeSubmit(formData)
        }
      } else {
        const error = await response.json()
        alert(`Trade failed: ${error.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Trade submission error:', error)
      alert('Failed to submit trade')
    } finally {
      setLoading(false)
    }
  }

  const calculateNotionalValue = () => {
    const price = formData.price || 0
    return formData.quantity * price
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <DollarSign className="w-5 h-5" />
            Manual Trading Interface
          </CardTitle>
          <CardDescription>
            Execute manual trades with advanced order management
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Symbol Selection */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="symbol">Symbol *</Label>
              <Input
                id="symbol"
                placeholder="Enter symbol (e.g., NIFTY, RELIANCE)"
                value={formData.symbol}
                onChange={(e) => handleInputChange('symbol', e.target.value)}
                className="uppercase"
              />
              <div className="flex flex-wrap gap-1 mt-2">
                {popularSymbols.map(symbol => (
                  <Badge 
                    key={symbol}
                    variant="outline" 
                    className="cursor-pointer hover:bg-primary hover:text-primary-foreground"
                    onClick={() => handleInputChange('symbol', symbol)}
                  >
                    {symbol}
                  </Badge>
                ))}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="strategy">Strategy</Label>
              <Select 
                value={formData.strategy} 
                onValueChange={(value) => handleInputChange('strategy', value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select strategy" />
                </SelectTrigger>
                <SelectContent>
                  {strategies.map(strategy => (
                    <SelectItem key={strategy.value} value={strategy.value}>
                      {strategy.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Side and Order Type */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Order Side *</Label>
              <div className="flex gap-2">
                <Button
                  variant={formData.side === 'BUY' ? 'default' : 'outline'}
                  onClick={() => handleInputChange('side', 'BUY')}
                  className={cn(
                    "flex-1",
                    formData.side === 'BUY' && "bg-green-600 hover:bg-green-700"
                  )}
                >
                  <TrendingUp className="w-4 h-4 mr-2" />
                  BUY
                </Button>
                <Button
                  variant={formData.side === 'SELL' ? 'default' : 'outline'}
                  onClick={() => handleInputChange('side', 'SELL')}
                  className={cn(
                    "flex-1",
                    formData.side === 'SELL' && "bg-red-600 hover:bg-red-700"
                  )}
                >
                  <TrendingDown className="w-4 h-4 mr-2" />
                  SELL
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Order Type</Label>
              <Select 
                value={formData.orderType} 
                onValueChange={(value: 'MARKET' | 'LIMIT') => handleInputChange('orderType', value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="MARKET">Market Order</SelectItem>
                  <SelectItem value="LIMIT">Limit Order</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Quantity and Price */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="quantity">Quantity *</Label>
              <Input
                id="quantity"
                type="number"
                placeholder="Enter quantity"
                value={formData.quantity || ''}
                onChange={(e) => handleInputChange('quantity', parseInt(e.target.value) || 0)}
              />
            </div>

            {formData.orderType === 'LIMIT' && (
              <div className="space-y-2">
                <Label htmlFor="price">Price *</Label>
                <Input
                  id="price"
                  type="number"
                  step="0.01"
                  placeholder="Enter limit price"
                  value={formData.price || ''}
                  onChange={(e) => handleInputChange('price', parseFloat(e.target.value) || 0)}
                />
              </div>
            )}
          </div>

          {/* Risk Management */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="stopLoss">Stop Loss</Label>
              <div className="relative">
                <StopCircle className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  id="stopLoss"
                  type="number"
                  step="0.01"
                  placeholder="Stop loss price"
                  value={formData.stopLoss || ''}
                  onChange={(e) => handleInputChange('stopLoss', parseFloat(e.target.value) || undefined)}
                  className="pl-10"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="target">Target</Label>
              <div className="relative">
                <Target className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  id="target"
                  type="number"
                  step="0.01"
                  placeholder="Target price"
                  value={formData.target || ''}
                  onChange={(e) => handleInputChange('target', parseFloat(e.target.value) || undefined)}
                  className="pl-10"
                />
              </div>
            </div>
          </div>

          {/* Order Summary */}
          {formData.symbol && formData.quantity && (
            <Card className="bg-muted/50">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Order Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex justify-between">
                  <span>Symbol:</span>
                  <span className="font-medium">{formData.symbol.toUpperCase()}</span>
                </div>
                <div className="flex justify-between">
                  <span>Side:</span>
                  <Badge variant={formData.side === 'BUY' ? 'default' : 'secondary'}>
                    {formData.side}
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span>Quantity:</span>
                  <span className="font-medium">{formData.quantity}</span>
                </div>
                <div className="flex justify-between">
                  <span>Order Type:</span>
                  <span className="font-medium">{formData.orderType}</span>
                </div>
                {formData.orderType === 'LIMIT' && formData.price && (
                  <>
                    <div className="flex justify-between">
                      <span>Price:</span>
                      <span className="font-medium">₹{formData.price}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Notional Value:</span>
                      <span className="font-medium">₹{calculateNotionalValue().toLocaleString()}</span>
                    </div>
                  </>
                )}
                {formData.stopLoss && (
                  <div className="flex justify-between">
                    <span>Stop Loss:</span>
                    <span className="font-medium text-red-600">₹{formData.stopLoss}</span>
                  </div>
                )}
                {formData.target && (
                  <div className="flex justify-between">
                    <span>Target:</span>
                    <span className="font-medium text-green-600">₹{formData.target}</span>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Submit Button */}
          <Button 
            onClick={handleSubmitTrade}
            disabled={loading || !formData.symbol || !formData.quantity}
            className="w-full"
            size="lg"
          >
            {loading ? 'Submitting...' : `Submit ${formData.side} Order`}
          </Button>

          {/* Last Trade Result */}
          {lastTrade && (
            <Card className="border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg text-green-600">Trade Submitted Successfully</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-1 text-sm">
                  <div>Order ID: <span className="font-medium">{lastTrade.order_id}</span></div>
                  <div>Status: <span className="font-medium">{lastTrade.status}</span></div>
                  <div>Timestamp: <span className="font-medium">{new Date(lastTrade.timestamp).toLocaleString()}</span></div>
                </div>
              </CardContent>
            </Card>
          )}
        </CardContent>
      </Card>
    </div>
  )
}