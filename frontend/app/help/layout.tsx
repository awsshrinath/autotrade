import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "Help & Documentation | Trading Dashboard",
  description: "Find guides, tutorials, and support for using the trading dashboard",
}

export default function HelpLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex-1 p-6">
      {children}
    </div>
  )
} 