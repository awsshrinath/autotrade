"use client"

import type React from "react"

import { createContext, useContext, useEffect, useState } from "react"
import { useRouter, usePathname } from "next/navigation"

interface User {
  username: string
  role: string
}

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  logout: () => void
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    const checkAuth = () => {
      try {
        const authStatus = localStorage.getItem("isAuthenticated")
        const userData = localStorage.getItem("user")

        if (authStatus === "true" && userData) {
          setUser(JSON.parse(userData))
          setIsAuthenticated(true)
          // If user is authenticated and on login page, redirect to intended destination
          if (pathname === "/login") {
            const redirectPath = localStorage.getItem("redirectPath")
            if (redirectPath && redirectPath !== "/login") {
              localStorage.removeItem("redirectPath")
              router.push(redirectPath)
            } else {
              router.push("/dashboard")
            }
          }
        } else {
          setUser(null)
          setIsAuthenticated(false)
          // More selective redirect logic to prevent 404s
          const publicPaths = ["/", "/login"]
          const isPublicPath = publicPaths.some(path => pathname.startsWith(path))
          
          if (!isPublicPath) {
            // Store the attempted path for redirect after login
            localStorage.setItem("redirectPath", pathname)
            router.push("/login")
          }
        }
      } catch (error) {
        console.error("Auth check error:", error)
        setUser(null)
        setIsAuthenticated(false)
      } finally {
        setIsLoading(false)
      }
    }

    checkAuth()
  }, [pathname, router])

  const logout = () => {
    try {
      localStorage.removeItem("isAuthenticated")
      localStorage.removeItem("user")
      setUser(null)
      setIsAuthenticated(false)
      router.push("/login")
    } catch (error) {
      console.error("Logout error:", error)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0F0F12]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    )
  }

  return <AuthContext.Provider value={{ user, isAuthenticated, logout, isLoading }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
