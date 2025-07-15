"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card"
import { Button } from "../../components/ui/button"
import { Badge } from "../../components/ui/badge"
import { 
  Settings, 
  User, 
  Shield, 
  Save,
  RefreshCw
} from "lucide-react"

export default function SettingsPage() {
  const [isDarkMode, setIsDarkMode] = useState(true)
  const [notifications, setNotifications] = useState(true)
  const [autoRefresh, setAutoRefresh] = useState(true)

  const settingsCategories = [
    {
      title: "User Preferences",
      icon: User,
      settings: [
        {
          name: "Dark Mode",
          description: "Toggle between light and dark themes",
          value: isDarkMode,
          type: "toggle",
          action: () => setIsDarkMode(!isDarkMode)
        },
        {
          name: "Notifications",
          description: "Enable system notifications and alerts",
          value: notifications,
          type: "toggle", 
          action: () => setNotifications(!notifications)
        },
        {
          name: "Auto Refresh",
          description: "Automatically refresh dashboard data",
          value: autoRefresh,
          type: "toggle",
          action: () => setAutoRefresh(!autoRefresh)
        }
      ]
    },
    {
      title: "System Configuration",
      icon: Shield,
      settings: [
        {
          name: "API Endpoints",
          description: "Configure backend API connections",
          value: "Connected",
          type: "status"
        },
        {
          name: "Refresh Interval",
          description: "Data refresh frequency (seconds)",
          value: "30",
          type: "input"
        },
        {
          name: "Log Retention",
          description: "Days to retain system logs",
          value: "30",
          type: "input"
        }
      ]
    },
    {
      title: "Security",
      icon: Shield,
      settings: [
        {
          name: "API Authentication",
          description: "Current authentication status", 
          value: "Active",
          type: "status"
        },
        {
          name: "Session Timeout",
          description: "Auto logout after inactivity (minutes)",
          value: "60",
          type: "input"
        }
      ]
    }
  ]

  interface Setting {
    name: string;
    description: string;
    value: string | number | boolean;
    type: string;
    action?: () => void;
  }
  const SettingItem = ({ setting }: { setting: Setting }) => (
    <div className="flex items-center justify-between py-3 border-b border-gray-100 dark:border-[#1F1F23] last:border-0">
      <div className="flex-1">
        <h4 className="text-body-medium font-semibold text-gray-900 dark:text-white">
          {setting.name}
        </h4>
        <p className="text-caption text-gray-600 dark:text-gray-400 mt-1">
          {setting.description}
        </p>
      </div>
      <div className="flex items-center gap-3">
        {setting.type === "toggle" && (
          <button
            onClick={setting.action}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              setting.value 
                ? "bg-blue-600" 
                : "bg-gray-200 dark:bg-gray-700"
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                setting.value ? "translate-x-6" : "translate-x-1"
              }`}
            />
          </button>
        )}
        {setting.type === "status" && (
          <Badge 
            variant={setting.value === "Connected" || setting.value === "Active" ? "default" : "secondary"}
            className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
          >
            {setting.value}
          </Badge>
        )}
        {setting.type === "input" && (
          <input
            type="text"
            defaultValue={String(setting.value)}
            className="w-20 px-2 py-1 text-sm border border-gray-200 dark:border-[#1F1F23] rounded bg-white dark:bg-[#0F0F12] text-gray-900 dark:text-white"
          />
        )}
      </div>
    </div>
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="h-8 w-8 bg-gray-100 dark:bg-[#1F1F23] rounded-lg flex items-center justify-center">
          <Settings className="h-4 w-4 text-gray-600 dark:text-gray-400" />
        </div>
        <div>
          <h1 className="text-heading-large font-bold text-gray-900 dark:text-white">
            Settings
          </h1>
          <p className="text-body-medium text-gray-600 dark:text-gray-400">
            Configure your dashboard preferences and system settings
          </p>
        </div>
      </div>

      <div className="grid gap-6">
        {settingsCategories.map((category, index) => {
          const IconComponent = category.icon
          return (
            <Card key={index} className="bg-white dark:bg-[#0F0F12] border-gray-200 dark:border-[#1F1F23]">
              <CardHeader>
                <CardTitle className="flex items-center gap-3 text-gray-900 dark:text-white">
                  <IconComponent className="h-5 w-5" />
                  {category.title}
                </CardTitle>
                <CardDescription className="text-gray-600 dark:text-gray-400">
                  Manage your {category.title.toLowerCase()} settings
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {category.settings.map((setting, settingIndex) => (
                    <SettingItem key={settingIndex} setting={setting} />
                  ))}
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      <div className="flex justify-end gap-3 pt-6 border-t border-gray-200 dark:border-[#1F1F23]">
        <Button 
          variant="outline" 
          className="border-gray-200 dark:border-[#1F1F23] text-gray-700 dark:text-gray-300"
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Reset to Defaults
        </Button>
        <Button className="bg-blue-600 hover:bg-blue-700 text-white">
          <Save className="h-4 w-4 mr-2" />
          Save Changes
        </Button>
      </div>
    </div>
  )
} 