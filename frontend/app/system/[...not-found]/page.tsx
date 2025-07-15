import { notFound } from 'next/navigation'

export default function SystemCatchAllPage() {
  // This will trigger the not-found.tsx page for invalid system routes
  notFound()
} 