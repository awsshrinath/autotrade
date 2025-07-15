"use client"

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import { AlertTriangle, CheckCircle, Info, X } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface ErrorNotification {
  id: string
  type: 'error' | 'warning' | 'info' | 'success'
  title: string
  message: string
  action?: {
    label: string
    onClick: () => void
  }
  dismissible?: boolean
  autoHide?: boolean
  duration?: number
  timestamp: number
}

interface ErrorContextType {
  notifications: ErrorNotification[]
  showError: (title: string, message: string, options?: Partial<ErrorNotification>) => string
  showWarning: (title: string, message: string, options?: Partial<ErrorNotification>) => string
  showInfo: (title: string, message: string, options?: Partial<ErrorNotification>) => string
  showSuccess: (title: string, message: string, options?: Partial<ErrorNotification>) => string
  dismissNotification: (id: string) => void
  clearAllNotifications: () => void
}

const ErrorContext = createContext<ErrorContextType | null>(null)

export const useError = () => {
  const context = useContext(ErrorContext)
  if (!context) {
    throw new Error('useError must be used within an ErrorProvider')
  }
  return context
}

interface ErrorProviderProps {
  children: ReactNode
  maxNotifications?: number
}

export const ErrorProvider: React.FC<ErrorProviderProps> = ({ 
  children, 
  maxNotifications = 5 
}) => {
  const [notifications, setNotifications] = useState<ErrorNotification[]>([])

  const generateId = () => Math.random().toString(36).substr(2, 9)

  const addNotification = useCallback((
    type: ErrorNotification['type'],
    title: string,
    message: string,
    options: Partial<ErrorNotification> = {}
  ): string => {
    const id = generateId()
    const notification: ErrorNotification = {
      id,
      type,
      title,
      message,
      dismissible: true,
      autoHide: type === 'success' || type === 'info',
      duration: type === 'success' ? 5000 : type === 'info' ? 7000 : 0,
      timestamp: Date.now(),
      ...options
    }

    setNotifications(prev => {
      const newNotifications = [notification, ...prev]
      // Limit number of notifications
      return newNotifications.slice(0, maxNotifications)
    })

    // Auto-hide if specified
    if (notification.autoHide && notification.duration! > 0) {
      setTimeout(() => {
        dismissNotification(id)
      }, notification.duration)
    }

    return id
  }, [maxNotifications, dismissNotification])

  const showError = useCallback((title: string, message: string, options?: Partial<ErrorNotification>) => {
    return addNotification('error', title, message, options)
  }, [addNotification])

  const showWarning = useCallback((title: string, message: string, options?: Partial<ErrorNotification>) => {
    return addNotification('warning', title, message, options)
  }, [addNotification])

  const showInfo = useCallback((title: string, message: string, options?: Partial<ErrorNotification>) => {
    return addNotification('info', title, message, options)
  }, [addNotification])

  const showSuccess = useCallback((title: string, message: string, options?: Partial<ErrorNotification>) => {
    return addNotification('success', title, message, options)
  }, [addNotification])

  const dismissNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id))
  }, [])

  const clearAllNotifications = useCallback(() => {
    setNotifications([])
  }, [])

  const value: ErrorContextType = {
    notifications,
    showError,
    showWarning,
    showInfo,
    showSuccess,
    dismissNotification,
    clearAllNotifications
  }

  return (
    <ErrorContext.Provider value={value}>
      {children}
      <NotificationContainer />
    </ErrorContext.Provider>
  )
}

const NotificationContainer: React.FC = () => {
  const { notifications, dismissNotification } = useError()

  if (notifications.length === 0) return null

  return (
    <div className="fixed top-4 right-4 z-50 space-y-3 max-w-md">
      {notifications.map((notification) => (
        <NotificationCard 
          key={notification.id} 
          notification={notification} 
          onDismiss={() => dismissNotification(notification.id)} 
        />
      ))}
    </div>
  )
}

interface NotificationCardProps {
  notification: ErrorNotification
  onDismiss: () => void
}

const NotificationCard: React.FC<NotificationCardProps> = ({ notification, onDismiss }) => {
  const getIcon = () => {
    switch (notification.type) {
      case 'error':
        return <AlertTriangle className="w-5 h-5 text-red-500" />
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-amber-500" />
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'info':
      default:
        return <Info className="w-5 h-5 text-blue-500" />
    }
  }

  const getStyles = () => {
    switch (notification.type) {
      case 'error':
        return 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/10'
      case 'warning':
        return 'border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/10'
      case 'success':
        return 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/10'
      case 'info':
      default:
        return 'border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/10'
    }
  }

  return (
    <div 
      className={cn(
        "p-4 rounded-lg border shadow-lg animate-slide-down transition-all duration-300",
        getStyles()
      )}
      role="alert"
    >
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0 mt-0.5">
          {getIcon()}
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            {notification.title}
          </h4>
          <p className="text-sm text-gray-700 dark:text-gray-300 mt-1">
            {notification.message}
          </p>
          {notification.action && (
            <button
              onClick={notification.action.onClick}
              className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200 mt-2 font-medium"
            >
              {notification.action.label}
            </button>
          )}
        </div>
        {notification.dismissible && (
          <button
            onClick={onDismiss}
            className="flex-shrink-0 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
            aria-label="Dismiss notification"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  )
}

// Hook for API error handling
export const useApiError = () => {
  const { showError, showWarning } = useError()

  const handleApiError = useCallback((error: Error | { message?: string; status?: number }, context?: string) => {
    const contextPrefix = context ? `${context}: ` : ''
    
    if (error && typeof error === 'object') {
      // Handle our custom ApiError format
      if ('message' in error && 'status' in error) {
        showError(
          `${contextPrefix}Request Failed`,
          error.message,
          {
            action: error.status >= 500 ? {
              label: 'Retry',
              onClick: () => window.location.reload()
            } : undefined
          }
        )
        return
      }
      
      // Handle network errors
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        showError(
          `${contextPrefix}Connection Error`,
          'Unable to connect to the server. Please check your internet connection.',
          {
            action: {
              label: 'Retry',
              onClick: () => window.location.reload()
            }
          }
        )
        return
      }
    }

    // Fallback for unknown errors
    showError(
      `${contextPrefix}Unexpected Error`,
      'Something went wrong. Please try again.',
      {
        action: {
          label: 'Reload',
          onClick: () => window.location.reload()
        }
      }
    )
  }, [showError])

  return { handleApiError, showError, showWarning }
}

export default ErrorProvider 