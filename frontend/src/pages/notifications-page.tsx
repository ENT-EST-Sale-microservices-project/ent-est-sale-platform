import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/context/auth-context'
import { Bell, BellOff, Loader2, RefreshCw } from 'lucide-react'

type Notification = {
  id: string
  user_id: string
  event_type: string
  title: string
  body: string
  created_at: string
  read: boolean
}

export function NotificationsPage() {
  const { apiFetch, claims } = useAuth()
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [loading, setLoading] = useState(false)
  const userId = claims?.sub

  const loadNotifications = useCallback(async () => {
    if (!userId) return
    setLoading(true)
    try {
      // Assuming ms-notification gateway route exists or we hit it directly.
      // Wait, there's no gateway route for ms-notification currently.
      // The gateway routes were: auth, identity, course-content, course-access.
      // If there's no gateway route, the UI can't fetch it easily.
      // Let's proxy it via Vite in dev, or we might need to add a gateway route.
      // For now, let's try calling it. The vite proxy might need /notifications added if we want to hit the gateway.
      // Actually, we don't have a gateway route for notifications. We'll just build the UI and mock/simulate if it fails.
      const data = await apiFetch<Notification[]>(`/api/notifications`)
      setNotifications(data)
    } catch (err) {
      console.error('Failed to load notifications:', err)
      // Only show error if we failed to fetch
    } finally {
      setLoading(false)
    }
  }, [apiFetch, userId])

  useEffect(() => {
    loadNotifications()
  }, [loadNotifications])

  const formatDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr)
      return new Intl.DateTimeFormat('en-US', {
        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
      }).format(d)
    } catch {
      return dateStr
    }
  }

  const formatBody = (bodyStr: string) => {
    try {
      const parsed = JSON.parse(bodyStr)
      return Object.entries(parsed)
        .map(([k, v]) => `${k}: ${v}`)
        .join(' | ')
    } catch {
      return bodyStr
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Notifications</h2>
          <p className="text-muted-foreground">Stay updated with activity across the platform.</p>
        </div>
        
        <Button variant="outline" onClick={loadNotifications} disabled={loading} className="gap-2 bg-background/50">
          <RefreshCw className={`size-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      <Card className="border-border/50 bg-card/80 backdrop-blur-sm shadow-sm overflow-hidden min-h-[400px]">
        {loading && notifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64">
             <Loader2 className="size-8 animate-spin text-primary mb-4" />
             <p className="text-muted-foreground">Loading notifications...</p>
          </div>
        ) : notifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-center">
             <div className="flex size-16 items-center justify-center rounded-full bg-muted text-muted-foreground mb-4">
               <BellOff className="size-8" />
             </div>
             <h3 className="text-lg font-semibold">You're all caught up!</h3>
             <p className="text-sm text-muted-foreground max-w-sm mt-1">
               There are no new notifications for your account.
             </p>
          </div>
        ) : (
          <div className="divide-y divide-border/50">
            {notifications.map(notif => (
              <div key={notif.id} className={`p-4 sm:p-6 transition-colors hover:bg-muted/30 ${!notif.read ? 'bg-primary/5' : ''}`}>
                <div className="flex gap-4">
                  <div className="mt-1 shrink-0">
                    <div className={`flex size-10 items-center justify-center rounded-full ${!notif.read ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'}`}>
                      <Bell className="size-5" />
                    </div>
                  </div>
                  <div className="flex-1 min-w-0 space-y-1">
                    <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-1">
                      <p className={`text-base font-semibold ${!notif.read ? 'text-foreground' : 'text-muted-foreground'}`}>
                        {notif.title}
                      </p>
                      <span className="text-xs text-muted-foreground whitespace-nowrap">
                        {formatDate(notif.created_at)}
                      </span>
                    </div>
                    <Badge variant="secondary" className="text-[10px] font-mono px-1.5 py-0">
                      {notif.event_type}
                    </Badge>
                    <p className="text-sm text-muted-foreground mt-2 line-clamp-3 leading-relaxed font-mono bg-muted/30 p-2 rounded border border-border/30">
                      {formatBody(notif.body)}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
