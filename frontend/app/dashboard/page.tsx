"use client"

import Dashboard from "@/components/tron/dashboard"
import ProtectedRoute from "@/components/auth/protected-route"
import { PageErrorBoundary } from "@/components/error-boundary"

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <PageErrorBoundary>
        <Dashboard />
      </PageErrorBoundary>
    </ProtectedRoute>
  )
}
