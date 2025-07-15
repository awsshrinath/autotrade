"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card"
import { Button } from "../../components/ui/button"
import { Badge } from "../../components/ui/badge"
import { 
  HelpCircle, 
  Book, 
  MessageCircle, 
  ExternalLink,
  Search,
  FileText,
  Video,
  Mail,
  Github,
  AlertCircle,
  CheckCircle
} from "lucide-react"

export default function HelpPage() {
  const helpSections = [
    {
      title: "Getting Started",
      icon: Book,
      items: [
        {
          title: "Dashboard Overview",
          description: "Learn about the main dashboard features and navigation",
          type: "guide",
          status: "available"
        },
        {
          title: "Setting Up Your First Trading Strategy",
          description: "Step-by-step guide to create and deploy trading strategies",
          type: "tutorial",
          status: "available"
        },
        {
          title: "Understanding Risk Management",
          description: "How to configure and monitor risk parameters",
          type: "guide", 
          status: "available"
        }
      ]
    },
    {
      title: "Features & Functionality",
      icon: FileText,
      items: [
        {
          title: "Real-time Analytics",
          description: "Monitor trading performance and system metrics",
          type: "documentation",
          status: "available"
        },
        {
          title: "System Health Monitoring", 
          description: "Track system performance and resource usage",
          type: "documentation",
          status: "available"
        },
        {
          title: "Log Analysis",
          description: "Access and analyze system logs and trading data",
          type: "documentation",
          status: "available"
        },
        {
          title: "Cognitive Insights",
          description: "AI-powered analysis and recommendations",
          type: "documentation", 
          status: "beta"
        }
      ]
    },
    {
      title: "Troubleshooting",
      icon: AlertCircle,
      items: [
        {
          title: "Common Issues & Solutions",
          description: "Resolve frequently encountered problems",
          type: "troubleshooting",
          status: "available"
        },
        {
          title: "API Connection Problems",
          description: "Fix connectivity and authentication issues",
          type: "troubleshooting",
          status: "available"
        },
        {
          title: "Performance Optimization", 
          description: "Improve system performance and response times",
          type: "troubleshooting",
          status: "available"
        }
      ]
    }
  ]

  const quickActions = [
    {
      title: "Search Documentation",
      description: "Find specific topics and features",
      icon: Search,
      action: "search"
    },
    {
      title: "Video Tutorials", 
      description: "Watch step-by-step video guides",
      icon: Video,
      action: "tutorials"
    },
    {
      title: "Contact Support",
      description: "Get help from our support team",
      icon: MessageCircle,
      action: "contact"
    },
    {
      title: "Feature Requests",
      description: "Suggest new features or improvements",
      icon: Github,
      action: "feedback"
    }
  ]

  const HelpItem = ({ item }: { item: { title: string; description: string; type: string; status: string } }) => (
    <div className="flex items-center justify-between p-4 border border-gray-200 dark:border-[#1F1F23] rounded-lg hover:bg-gray-50 dark:hover:bg-[#1A1A1F] transition-colors cursor-pointer">
      <div className="flex-1">
        <div className="flex items-center gap-3">
          <h4 className="text-body-medium font-semibold text-gray-900 dark:text-white">
            {item.title}
          </h4>
          <Badge 
            variant={item.status === "available" ? "default" : "secondary"}
            className={
              item.status === "available" 
                ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                : item.status === "beta"
                ? "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
                : "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200"
            }
          >
            {item.status}
          </Badge>
        </div>
        <p className="text-caption text-gray-600 dark:text-gray-400 mt-1">
          {item.description}
        </p>
      </div>
      <ExternalLink className="h-4 w-4 text-gray-400" />
    </div>
  )

  const QuickActionCard = ({ action }: { action: { title: string; description: string; icon: React.ComponentType<any>; action: string } }) => {
    const IconComponent = action.icon
    return (
      <Card className="bg-white dark:bg-[#0F0F12] border-gray-200 dark:border-[#1F1F23] hover:shadow-lg transition-shadow cursor-pointer">
        <CardContent className="p-6">
          <div className="flex items-center gap-3 mb-3">
            <div className="h-10 w-10 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center">
              <IconComponent className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h3 className="text-body-medium font-semibold text-gray-900 dark:text-white">
                {action.title}
              </h3>
            </div>
          </div>
          <p className="text-caption text-gray-600 dark:text-gray-400">
            {action.description}
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="h-8 w-8 bg-gray-100 dark:bg-[#1F1F23] rounded-lg flex items-center justify-center">
          <HelpCircle className="h-4 w-4 text-gray-600 dark:text-gray-400" />
        </div>
        <div>
          <h1 className="text-heading-large font-bold text-gray-900 dark:text-white">
            Help & Documentation
          </h1>
          <p className="text-body-medium text-gray-600 dark:text-gray-400">
            Find guides, tutorials, and support for using the trading dashboard
          </p>
        </div>
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-heading-medium font-semibold text-gray-900 dark:text-white mb-4">
          Quick Actions
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickActions.map((action, index) => (
            <QuickActionCard key={index} action={action} />
          ))}
        </div>
      </div>

      {/* Help Sections */}
      <div className="grid gap-6">
        {helpSections.map((section, index) => {
          const IconComponent = section.icon
          return (
            <Card key={index} className="bg-white dark:bg-[#0F0F12] border-gray-200 dark:border-[#1F1F23]">
              <CardHeader>
                <CardTitle className="flex items-center gap-3 text-gray-900 dark:text-white">
                  <IconComponent className="h-5 w-5" />
                  {section.title}
                </CardTitle>
                <CardDescription className="text-gray-600 dark:text-gray-400">
                  Browse documentation and guides for {section.title.toLowerCase()}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {section.items.map((item, itemIndex) => (
                    <HelpItem key={itemIndex} item={item} />
                  ))}
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Contact Support */}
      <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950 dark:to-indigo-950 border-blue-200 dark:border-blue-800">
        <CardContent className="p-6">
          <div className="flex items-center gap-4">
            <div className="h-12 w-12 bg-blue-600 rounded-lg flex items-center justify-center">
              <Mail className="h-6 w-6 text-white" />
            </div>
            <div className="flex-1">
              <h3 className="text-heading-small font-semibold text-gray-900 dark:text-white">
                Still need help?
              </h3>
              <p className="text-body-medium text-gray-600 dark:text-gray-400">
                Contact our support team for personalized assistance
              </p>
            </div>
            <Button className="bg-blue-600 hover:bg-blue-700 text-white">
              Contact Support
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
} 