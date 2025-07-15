import { notFound } from 'next/navigation'

export default function AnalyticsCatchAllPage() {
  // This will trigger the not-found.tsx page for invalid analytics routes
  notFound()
} 