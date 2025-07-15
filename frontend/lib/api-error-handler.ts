// Enhanced API client with error handling, retry logic, and fallback data integration
import { shouldUseFallback, notifyFallbackUsage } from './fallback-data'

export interface ApiError extends Error {
  status?: number
  code?: string
  data?: unknown
}

export interface RetryOptions {
  maxRetries?: number
  retryDelay?: number
  exponentialBackoff?: boolean
  retryCondition?: (error: ApiError) => boolean
}

export interface RequestOptions {
  retry?: RetryOptions
  timeout?: number
  headers?: Record<string, string>
  useFallback?: boolean
}

class ApiClient {
  private baseURL: string = ''

  constructor(baseURL: string = '') {
    this.baseURL = baseURL || process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001'
  }

  private async sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  private createError(response: Response, message?: string): ApiError {
    const error = new Error(message || `HTTP ${response.status}`) as ApiError
    error.status = response.status
    error.code = response.status >= 500 ? 'SERVER_ERROR' : 'CLIENT_ERROR'
    return error
  }

  private async makeRequest<T>(
    url: string, 
    options: RequestInit & RequestOptions = {}
  ): Promise<T> {
    const {
      retry = {},
      timeout = 10000,
      useFallback = process.env.NEXT_PUBLIC_ENV !== 'production',
      ...fetchOptions
    } = options

    const {
      maxRetries = 3,
      retryDelay = 1000,
      exponentialBackoff = true,
      retryCondition = (error: ApiError) => 
        !error.status || error.status >= 500 || error.status === 0
    } = retry

    let lastError: ApiError | null = null

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        // Create timeout promise
        const timeoutPromise = new Promise<never>((_, reject) => {
          setTimeout(() => {
            const error = new Error('Request timeout') as ApiError
            error.code = 'TIMEOUT'
            error.status = 0
            reject(error)
          }, timeout)
        })

        // Make the actual request
        const requestPromise = fetch(this.baseURL + url, {
          ...fetchOptions,
          headers: {
            'Content-Type': 'application/json',
            ...fetchOptions.headers
          }
        })

        const response = await Promise.race([requestPromise, timeoutPromise])

        if (!response.ok) {
          throw this.createError(response, `Request failed: ${response.statusText}`)
        }

        const data = await response.json()
        return data
      } catch (error: unknown) {
        // Use type guard for error
        if (typeof error === 'object' && error !== null && 'status' in error) {
          lastError = error as ApiError
        } else {
          lastError = new Error('Unknown error') as ApiError
        }

        // Don't retry on client errors (4xx) except 408 (timeout)
        if (
          typeof error === 'object' && error !== null && 'status' in error &&
          typeof (error as any).status === 'number' &&
          (error as any).status >= 400 && (error as any).status < 500 && (error as any).status !== 408
        ) {
          break
        }

        // Check if we should retry
        if (attempt < maxRetries && lastError && retryCondition(lastError)) {
          const delay = exponentialBackoff 
            ? retryDelay * Math.pow(2, attempt)
            : retryDelay
          
          console.warn(`Request failed, retrying in ${delay}ms... (${attempt + 1}/${maxRetries + 1})`)
          await this.sleep(delay)
          continue
        }

        break
      }
    }

         // If we get here, all retries failed
     // Try fallback data if enabled and appropriate
     if (useFallback && lastError && shouldUseFallback(lastError)) {
       const fallbackResult = this.getFallbackData<T>(url)
       if (fallbackResult) {
         notifyFallbackUsage(url)
         return fallbackResult
       }
     }

     throw lastError || new Error('Request failed')
  }

  private getFallbackData<T>(_url: string): T | null {
    // FALLBACK DATA COMPLETELY DISABLED
    // Always return null so that components show "No data available"
    return null
  }

  async get<T>(url: string, options: RequestOptions = {}): Promise<T> {
    return this.makeRequest<T>(url, {
      ...options,
      method: 'GET'
    })
  }

  async post<T>(url: string, data?: unknown, options: RequestOptions = {}): Promise<T> {
    return this.makeRequest<T>(url, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined
    })
  }

  async put<T>(url: string, data?: unknown, options: RequestOptions = {}): Promise<T> {
    return this.makeRequest<T>(url, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined
    })
  }

  async delete<T>(url: string, options: RequestOptions = {}): Promise<T> {
    return this.makeRequest<T>(url, {
      ...options,
      method: 'DELETE'
    })
  }

  async patch<T>(url: string, data?: unknown, options: RequestOptions = {}): Promise<T> {
    return this.makeRequest<T>(url, {
      ...options,
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined
    })
  }
}

// Create a default client instance
const apiClient = new ApiClient()

// Enhanced utility function with fallback integration
export async function fetchWithRetry<T>(
  url: string,
  options: RequestOptions = {}
): Promise<{ data: T; isFallback: boolean }> {
  try {
    const data = await apiClient.get<T>(url, options)
    return { data, isFallback: false }
  } catch (error: unknown) {
    if (typeof error === 'object' && error !== null && shouldUseFallback(error as ApiError)) {
      const fallbackResult = apiClient['getFallbackData']<T>(url)
      if (fallbackResult) {
        notifyFallbackUsage(url)
        return { data: fallbackResult, isFallback: true }
      }
    }
    throw error
  }
}

// Convenience methods for common error scenarios
export function isNetworkError(error: ApiError | Error | { status?: number; code?: string }): boolean {
  if (typeof error === 'object' && error !== null) {
    if ('status' in error && typeof (error as any).status === 'number') {
      if (!(error as any).status) return true
    }
    if ('code' in error && ((error as any).code === 'NETWORK_ERROR' || (error as any).code === 'TIMEOUT')) {
      return true
    }
  }
  return false
}

export function isServerError(error: ApiError | Error | { status?: number }): boolean {
  return typeof error === 'object' && error !== null && 'status' in error && typeof (error as any).status === 'number' && (error as any).status >= 500
}

export function isClientError(error: ApiError | Error | { status?: number }): boolean {
  return typeof error === 'object' && error !== null && 'status' in error && typeof (error as any).status === 'number' && (error as any).status >= 400 && (error as any).status < 500
}

export function getErrorMessage(error: ApiError | Error | { message?: string; status?: number }): string {
  if (typeof error === 'object' && error !== null) {
    if ('message' in error && typeof (error as any).message === 'string') {
      return (error as any).message
    }
    if ('status' in error && typeof (error as any).status === 'number') {
      return `HTTP ${(error as any).status}`
    }
  }
  return 'An unexpected error occurred'
}

// Enhanced error boundary integration
export function handleApiError(error: ApiError | Error | { message?: string; status?: number }, context: string = 'API'): string {
  const message = getErrorMessage(error)
  
  if (isNetworkError(error)) {
    return `Network error in ${context}. Using cached data where available.`
  }
  
  if (isServerError(error)) {
    return `${context} service temporarily unavailable. Please try again later.`
  }

  if (isClientError(error)) {
    return `${context} request failed: ${message}`
  }

  return `${context} error: ${message}`
}

export default apiClient