"use client"

import { lazy, Suspense } from "react"
import Layout from "./layout"
import { SkeletonCard } from "@/components/ui/skeleton"

// Lazy load heavy components
const Content = lazy(() => import("./content"))
const TradingInterface = lazy(() => import("./trading-interface"))

// Loading fallback components
const ContentFallback = () => (
  <div className="space-y-6">
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <SkeletonCard />
      <SkeletonCard />
      <SkeletonCard />
    </div>
    <SkeletonCard />
    <SkeletonCard />
  </div>
)

const TradingInterfaceFallback = () => (
  <SkeletonCard />
)

export default function Dashboard() {
  return (
    <Layout>
      <div className="space-y-6">
        <Suspense fallback={<ContentFallback />}>
          <Content />
        </Suspense>
        <Suspense fallback={<TradingInterfaceFallback />}>
          <TradingInterface />
        </Suspense>
      </div>
    </Layout>
  )
}
