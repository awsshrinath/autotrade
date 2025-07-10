import { notFound } from 'next/navigation'

export default function CognitiveCatchAllPage() {
  // This will trigger the not-found.tsx page for invalid cognitive routes
  notFound()
} 