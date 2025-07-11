import type React from "react"
import { Inter } from "next/font/google"
import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import { AuthProvider } from "@/components/auth/auth-provider"
import { CriticalErrorBoundary } from "@/components/error-boundary"
import { ErrorProvider } from "@/components/error-context"
import { Toaster } from "@/components/ui/toaster"

const inter = Inter({ 
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
})

export const metadata = {
  title: "Tron Dashboard",
  description: "A modern trading dashboard with theme switching",
  generator: "v0.dev",
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <CriticalErrorBoundary>
          <ErrorProvider>
            <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false} disableTransitionOnChange>
              <AuthProvider>{children}</AuthProvider>
              <Toaster />
            </ThemeProvider>
          </ErrorProvider>
        </CriticalErrorBoundary>
      </body>
    </html>
  )
}
