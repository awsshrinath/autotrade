"use client"

import React, { Component, ErrorInfo, ReactNode } from 'react'
import { AlertTriangle, RefreshCw, Home, Bug } from 'lucide-react'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
  showDetails?: boolean
  level?: 'page' | 'component' | 'critical'
}

interface State {
  hasError: boolean
  error?: Error
  errorInfo?: ErrorInfo
  errorId: string
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = {
      hasError: false,
      errorId: Math.random().toString(36).substr(2, 9)
    }
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorId: Math.random().toString(36).substr(2, 9)
    }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
    
    this.setState({
      error,
      errorInfo
    })

    // Call custom error handler if provided
    this.props.onError?.(error, errorInfo)

    // Log to monitoring service in production
    if (process.env.NODE_ENV === 'production') {
      // TODO: Send to error tracking service (Sentry, LogRocket, etc.)
      this.logErrorToService(error, errorInfo)
    }
  }

  private logErrorToService = (error: Error, errorInfo: ErrorInfo) => {
    // Integration point for error tracking services
    console.log('Logging error to monitoring service:', {
      errorId: this.state.errorId,
      error: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString()
    })
  }

  private handleReload = () => {
    window.location.reload()
  }

  private handleReset = () => {
    this.setState({
      hasError: false,
      error: undefined,
      errorInfo: undefined,
      errorId: Math.random().toString(36).substr(2, 9)
    })
  }

  private handleGoHome = () => {
    window.location.href = '/dashboard'
  }

  private renderErrorDetails = () => {
    if (!this.props.showDetails || !this.state.error) return null

    return (
      <details className="mt-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border">
        <summary className="cursor-pointer text-sm font-medium text-gray-700 dark:text-gray-300 flex items-center gap-2">
          <Bug className="w-4 h-4" />
          Technical Details (Error ID: {this.state.errorId})
        </summary>
        <div className="mt-3 text-xs text-gray-600 dark:text-gray-400 space-y-2">
          <div>
            <strong>Error:</strong>
            <pre className="mt-1 p-2 bg-red-50 dark:bg-red-900/20 rounded text-red-800 dark:text-red-200 overflow-x-auto">
              {this.state.error.message}
            </pre>
          </div>
          {this.state.error.stack && (
            <div>
              <strong>Stack Trace:</strong>
              <pre className="mt-1 p-2 bg-gray-100 dark:bg-gray-700 rounded text-xs overflow-x-auto max-h-32">
                {this.state.error.stack}
              </pre>
            </div>
          )}
        </div>
      </details>
    )
  }

  private renderFallbackUI = () => {
    const { level = 'component' } = this.props

    if (level === 'critical') {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 p-4">
          <Card className="w-full max-w-md border-red-200 dark:border-red-800">
            <CardHeader className="text-center">
              <div className="mx-auto w-12 h-12 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mb-4">
                <AlertTriangle className="w-6 h-6 text-red-600 dark:text-red-400" />
              </div>
              <CardTitle className="text-red-900 dark:text-red-100">Critical Error</CardTitle>
              <CardDescription className="text-red-700 dark:text-red-300">
                A critical error has occurred. The application needs to be reloaded.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-col gap-2">
                <Button onClick={this.handleReload} className="w-full">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Reload Application
                </Button>
                <Button variant="outline" onClick={this.handleGoHome} className="w-full">
                  <Home className="w-4 h-4 mr-2" />
                  Go to Dashboard
                </Button>
              </div>
              {this.renderErrorDetails()}
            </CardContent>
          </Card>
        </div>
      )
    }

    if (level === 'page') {
      return (
        <div className="flex items-center justify-center min-h-96 p-8">
          <Card className="w-full max-w-lg border-red-200 dark:border-red-800">
            <CardHeader className="text-center">
              <div className="mx-auto w-10 h-10 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center mb-3">
                <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />
              </div>
              <CardTitle className="text-red-900 dark:text-red-100">Page Error</CardTitle>
              <CardDescription className="text-red-700 dark:text-red-300">
                This page encountered an error and couldn't load properly.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex gap-2">
                <Button onClick={this.handleReset} size="sm" className="flex-1">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Try Again
                </Button>
                <Button variant="outline" onClick={this.handleGoHome} size="sm" className="flex-1">
                  <Home className="w-4 h-4 mr-2" />
                  Go Back
                </Button>
              </div>
              {this.renderErrorDetails()}
            </CardContent>
          </Card>
        </div>
      )
    }

    // Component level error
    return (
      <Card className="border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/10">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center flex-shrink-0">
              <AlertTriangle className="w-4 h-4 text-red-600 dark:text-red-400" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-sm font-medium text-red-900 dark:text-red-100">
                Component Error
              </h3>
              <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                This component failed to load. Please try refreshing the page.
              </p>
              <div className="flex gap-2 mt-3">
                <Button onClick={this.handleReset} size="sm" variant="outline">
                  <RefreshCw className="w-3 h-3 mr-1" />
                  Retry
                </Button>
              </div>
            </div>
          </div>
          {this.renderErrorDetails()}
        </CardContent>
      </Card>
    )
  }

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback
      }

      // Default fallback UI based on level
      return this.renderFallbackUI()
    }

    return this.props.children
  }
}

export default ErrorBoundary

// Specialized error boundaries for different use cases
export const PageErrorBoundary = ({ children, onError }: { children: ReactNode, onError?: (error: Error, errorInfo: ErrorInfo) => void }) => (
  <ErrorBoundary level="page" onError={onError} showDetails={process.env.NODE_ENV === 'development'}>
    {children}
  </ErrorBoundary>
)

export const ComponentErrorBoundary = ({ children, onError }: { children: ReactNode, onError?: (error: Error, errorInfo: ErrorInfo) => void }) => (
  <ErrorBoundary level="component" onError={onError}>
    {children}
  </ErrorBoundary>
)

export const CriticalErrorBoundary = ({ children, onError }: { children: ReactNode, onError?: (error: Error, errorInfo: ErrorInfo) => void }) => (
  <ErrorBoundary level="critical" onError={onError} showDetails={process.env.NODE_ENV === 'development'}>
    {children}
  </ErrorBoundary>
) 