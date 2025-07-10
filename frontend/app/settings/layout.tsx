import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "Settings | Trading Dashboard",
  description: "Configure your dashboard preferences and system settings",
}

export default function SettingsLayout({
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