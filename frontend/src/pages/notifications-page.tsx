import { useState, useEffect, useCallback } from 'react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/context/auth-context'
import {
  Bell, BellOff, BookOpen, CheckCheck, CheckCircle, ClipboardList,
  FileText, GraduationCap, Loader2, MessageSquare, RefreshCw,
  ShieldCheck, Star, Trash2, UploadCloud, UserCheck, CalendarDays,
} from 'lucide-react'

type Notification = {
  id: string
  user_id: string
  event_type: string
  title: string
  body: string
  created_at: string
  read: boolean
}

type Payload = Record<string, string | number | null>

function describeNotification(eventType: string, payload: Payload): string {
  switch (eventType) {
    case 'grade.published.v1': {
      const grade = payload.grade ?? '—'
      const max = payload.max_grade ?? '—'
      return `Your submission has been graded: ${grade} / ${max} points.`
    }
    case 'assignment.submitted.v1':
      return 'Your submission was received and is pending review by the teacher.'
    case 'assignment.published.v1': {
      const title = payload.title ? `"${payload.title}"` : 'A new assignment'
      const mod = payload.module_code ? ` in module ${payload.module_code}` : ''
      const due = payload.due_date
        ? ` — due ${new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(String(payload.due_date)))}`
        : ''
      return `${title}${mod} has been published${due}.`
    }
    case 'user.created.v1': {
      const name = payload.preferred_username || payload.email || 'you'
      return `Account created for ${name}. Welcome to ENT EST Salé!`
    }
    case 'user.role.assigned.v1': {
      const roles = payload.roles ? String(payload.roles) : 'new roles'
      return `Your account roles have been updated to: ${roles}.`
    }
    case 'course.created.v1': {
      const title = payload.title ? `"${payload.title}"` : 'A new course'
      const mod = payload.module_code ? ` (${payload.module_code})` : ''
      return `${title}${mod} is now available in the course catalog.`
    }
    case 'course.updated.v1': {
      const title = payload.title ? `"${payload.title}"` : 'A course'
      return `${title} has been updated with new information.`
    }
    case 'course.deleted.v1': {
      const title = payload.title ? `"${payload.title}"` : 'A course'
      return `${title} has been removed from the catalog.`
    }
    case 'asset.uploaded.v1': {
      const file = payload.file_name ? `"${payload.file_name}"` : 'A new file'
      return `${file} has been added to course materials.`
    }
    case 'calendar.event.created.v1': {
      const title = payload.title ? `"${payload.title}"` : 'A calendar event'
      const mod = payload.module_code && payload.module_code !== 'all' ? ` for ${payload.module_code}` : ''
      return `${title}${mod} has been added to the calendar.`
    }
    case 'forum.thread.created.v1': {
      const title = payload.title ? `"${payload.title}"` : 'A new thread'
      const mod = payload.module_code ? ` in ${payload.module_code}` : ''
      return `${title}${mod} was posted in the forum.`
    }
    case 'forum.message.posted.v1':
      return 'A new reply was posted in a forum thread you follow.'
    case 'notification.test.v1':
      return 'This is a test notification to verify the system is working correctly.'
    default:
      return 'You have a new platform update.'
  }
}

type EventMeta = {
  icon: React.ComponentType<{ className?: string }>
  color: string
  bg: string
  category: string
}

function getEventMeta(eventType: string): EventMeta {
  if (eventType.startsWith('grade.'))
    return { icon: Star, color: 'text-yellow-600 dark:text-yellow-400', bg: 'bg-yellow-500/15', category: 'Grade' }
  if (eventType.startsWith('assignment.submitted'))
    return { icon: CheckCircle, color: 'text-green-600 dark:text-green-400', bg: 'bg-green-500/15', category: 'Submission' }
  if (eventType.startsWith('assignment.'))
    return { icon: ClipboardList, color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-500/15', category: 'Assignment' }
  if (eventType.startsWith('course.deleted'))
    return { icon: Trash2, color: 'text-red-600 dark:text-red-400', bg: 'bg-red-500/15', category: 'Course' }
  if (eventType.startsWith('asset.'))
    return { icon: UploadCloud, color: 'text-purple-600 dark:text-purple-400', bg: 'bg-purple-500/15', category: 'Material' }
  if (eventType.startsWith('course.'))
    return { icon: BookOpen, color: 'text-indigo-600 dark:text-indigo-400', bg: 'bg-indigo-500/15', category: 'Course' }
  if (eventType.startsWith('user.role'))
    return { icon: ShieldCheck, color: 'text-orange-600 dark:text-orange-400', bg: 'bg-orange-500/15', category: 'Role' }
  if (eventType.startsWith('user.'))
    return { icon: UserCheck, color: 'text-teal-600 dark:text-teal-400', bg: 'bg-teal-500/15', category: 'Account' }
  if (eventType.startsWith('calendar.'))
    return { icon: CalendarDays, color: 'text-cyan-600 dark:text-cyan-400', bg: 'bg-cyan-500/15', category: 'Calendar' }
  if (eventType.startsWith('forum.'))
    return { icon: MessageSquare, color: 'text-pink-600 dark:text-pink-400', bg: 'bg-pink-500/15', category: 'Forum' }
  if (eventType.startsWith('grade.'))
    return { icon: GraduationCap, color: 'text-amber-600 dark:text-amber-400', bg: 'bg-amber-500/15', category: 'Grade' }
  return { icon: Bell, color: 'text-muted-foreground', bg: 'bg-muted', category: 'Update' }
}

function timeAgo(dateStr: string): string {
  try {
    const diff = Date.now() - new Date(dateStr).getTime()
    const mins = Math.floor(diff / 60000)
    if (mins < 1) return 'just now'
    if (mins < 60) return `${mins}m ago`
    const hrs = Math.floor(mins / 60)
    if (hrs < 24) return `${hrs}h ago`
    const days = Math.floor(hrs / 24)
    if (days < 7) return `${days}d ago`
    return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' }).format(new Date(dateStr))
  } catch {
    return dateStr
  }
}

export function NotificationsPage() {
  const { apiFetch } = useAuth()
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [loading, setLoading] = useState(false)
  const [markingRead, setMarkingRead] = useState(false)
  const [markingOneId, setMarkingOneId] = useState<string | null>(null)

  const loadNotifications = useCallback(async () => {
    setLoading(true)
    try {
      const data = await apiFetch<Notification[]>('/api/notifications')
      setNotifications(data)
    } catch (err) {
      console.error('Failed to load notifications:', err)
    } finally {
      setLoading(false)
    }
  }, [apiFetch])

  useEffect(() => {
    loadNotifications()
  }, [loadNotifications])

  async function markOneRead(notifId: string) {
    setMarkingOneId(notifId)
    try {
      await apiFetch(`/api/notifications/${notifId}/read`, { method: 'PATCH' })
      setNotifications(prev => prev.map(n => n.id === notifId ? { ...n, read: true } : n))
    } catch (err) {
      console.error('Failed to mark notification read:', err)
    } finally {
      setMarkingOneId(null)
    }
  }

  async function markAllRead() {
    setMarkingRead(true)
    try {
      await apiFetch('/api/notifications/read-all', { method: 'PATCH' })
      setNotifications(prev => prev.map(n => ({ ...n, read: true })))
    } catch (err) {
      console.error('Failed to mark read:', err)
    } finally {
      setMarkingRead(false)
    }
  }

  const unreadCount = notifications.filter(n => !n.read).length

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Notifications</h2>
          <p className="text-muted-foreground">Stay updated with activity across the platform.</p>
        </div>
        <div className="flex items-center gap-2">
          {unreadCount > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={markAllRead}
              disabled={markingRead}
              className="gap-2 text-xs"
            >
              {markingRead ? <Loader2 className="size-3.5 animate-spin" /> : <CheckCheck className="size-3.5" />}
              Mark all read
              <Badge variant="secondary" className="ml-0.5 px-1.5 py-0 text-[10px] h-4">{unreadCount}</Badge>
            </Button>
          )}
          <Button variant="outline" size="sm" onClick={loadNotifications} disabled={loading} className="gap-2 text-xs">
            <RefreshCw className={`size-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      <Card className="border-border/50 bg-card/80 backdrop-blur-sm shadow-sm overflow-hidden">
        {loading && notifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64">
            <Loader2 className="size-8 animate-spin text-primary mb-3" />
            <p className="text-sm text-muted-foreground">Loading notifications...</p>
          </div>
        ) : notifications.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-center">
            <div className="flex size-16 items-center justify-center rounded-full bg-muted mb-3">
              <BellOff className="size-7 text-muted-foreground" />
            </div>
            <h3 className="text-base font-semibold">You're all caught up!</h3>
            <p className="text-sm text-muted-foreground max-w-xs mt-1">
              There are no notifications for your account yet.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-border/40">
            {notifications.map(notif => {
              const meta = getEventMeta(notif.event_type)
              const Icon = meta.icon
              let payload: Payload = {}
              try { payload = JSON.parse(notif.body) } catch { /* plain text body */ }
              const message = describeNotification(notif.event_type, payload)

              return (
                <div
                  key={notif.id}
                  onClick={() => { if (!notif.read && markingOneId !== notif.id) markOneRead(notif.id) }}
                  className={`flex gap-4 px-5 py-4 transition-colors ${
                    !notif.read
                      ? 'bg-primary/[0.04] border-l-2 border-primary cursor-pointer hover:bg-primary/[0.08]'
                      : 'hover:bg-muted/25'
                  } ${markingOneId === notif.id ? 'opacity-60' : ''}`}
                >
                  <div className={`mt-0.5 shrink-0 flex size-10 items-center justify-center rounded-full ${meta.bg}`}>
                    <Icon className={`size-5 ${meta.color}`} />
                  </div>

                  <div className="flex-1 min-w-0 space-y-1">
                    <div className="flex items-start justify-between gap-3">
                      <p className={`text-sm font-semibold leading-snug ${!notif.read ? 'text-foreground' : 'text-muted-foreground'}`}>
                        {notif.title}
                      </p>
                      <div className="flex items-center gap-2 shrink-0">
                        {!notif.read && (
                          markingOneId === notif.id
                            ? <Loader2 className="size-3.5 animate-spin text-primary" />
                            : <span className="size-2 rounded-full bg-primary" />
                        )}
                        <span className="text-[11px] text-muted-foreground whitespace-nowrap mt-0.5">
                          {timeAgo(notif.created_at)}
                        </span>
                      </div>
                    </div>

                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {message}
                    </p>

                    <Badge
                      variant="outline"
                      className={`text-[10px] px-1.5 py-0 border-0 ${meta.bg} ${meta.color} font-medium`}
                    >
                      {meta.category}
                    </Badge>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </Card>
    </div>
  )
}
