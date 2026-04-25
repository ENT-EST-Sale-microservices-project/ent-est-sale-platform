import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/context/auth-context'
import { useNavigate } from 'react-router-dom'
import {
  BookOpen, Users, Clock, ShieldCheck, CloudUpload, GraduationCap,
  Loader2, MessageSquare, ArrowRight, CalendarDays, ClipboardList,
  TrendingUp, Activity,
} from 'lucide-react'

type ForumThread = {
  thread_id: string
  title: string
  author_name: string
  module_code: string
  created_at: string
}

export function DashboardPage() {
  const { username, roles, hasAnyRole, apiFetch } = useAuth()
  const navigate = useNavigate()
  const [data, setData] = useState<Record<string, any>>({})
  const [loading, setLoading] = useState(true)
  const [recentThreads, setRecentThreads] = useState<ForumThread[]>([])

  useEffect(() => {
    async function loadStats() {
      try {
        const res = await apiFetch<Record<string, any>>('/api/stats')
        setData(res)
      } catch (e) {
        console.error('Failed to load stats', e)
      } finally {
        setLoading(false)
      }
    }
    async function loadActivity() {
      try {
        const threads = await apiFetch<ForumThread[]>('/api/forum/threads')
        setRecentThreads(threads.slice(0, 5))
      } catch {
        // graceful fallback — forum may not be up
      }
    }
    loadStats()
    loadActivity()
  }, [apiFetch])

  const stats = []

  if (hasAnyRole(['admin'])) {
    stats.push(
      {
        title: 'Total Users', value: loading ? '—' : data.total_users ?? 0,
        icon: Users, desc: 'Registered accounts', color: 'text-blue-500', bg: 'bg-blue-500/10',
        border: 'border-blue-500/20',
      },
      {
        title: 'System Status', value: loading ? '—' : data.system_status ?? 'Unknown',
        icon: ShieldCheck, desc: 'All services running', color: 'text-emerald-500', bg: 'bg-emerald-500/10',
        border: 'border-emerald-500/20',
      },
      {
        title: 'Activity', value: loading ? '—' : recentThreads.length,
        icon: Activity, desc: 'Recent forum threads', color: 'text-purple-500', bg: 'bg-purple-500/10',
        border: 'border-purple-500/20',
      },
    )
  } else if (hasAnyRole(['teacher'])) {
    stats.push(
      {
        title: 'My Courses', value: loading ? '—' : data.total_courses ?? 0,
        icon: BookOpen, desc: 'Published courses', color: 'text-blue-500', bg: 'bg-blue-500/10',
        border: 'border-blue-500/20',
      },
      {
        title: 'Published Assignments', value: loading ? '—' : data.total_students ?? 0,
        icon: ClipboardList, desc: 'Active assignments', color: 'text-amber-500', bg: 'bg-amber-500/10',
        border: 'border-amber-500/20',
      },
      {
        title: 'Uploaded Assets', value: loading ? '—' : data.recent_uploads ?? 0,
        icon: CloudUpload, desc: 'Files across all courses', color: 'text-indigo-500', bg: 'bg-indigo-500/10',
        border: 'border-indigo-500/20',
      },
    )
  } else {
    stats.push(
      {
        title: 'Available Courses', value: loading ? '—' : data.enrolled_courses ?? 0,
        icon: BookOpen, desc: 'Open course catalog', color: 'text-blue-500', bg: 'bg-blue-500/10',
        border: 'border-blue-500/20',
      },
      {
        title: 'Upcoming Deadlines', value: loading ? '—' : data.upcoming_deadlines ?? 0,
        icon: Clock, desc: 'Due in next 7 days', color: 'text-orange-500', bg: 'bg-orange-500/10',
        border: 'border-orange-500/20',
      },
      {
        title: 'Academic Progress', value: loading ? '—' : data.completed_credits ?? 0,
        icon: GraduationCap, desc: 'Completed submissions', color: 'text-emerald-500', bg: 'bg-emerald-500/10',
        border: 'border-emerald-500/20',
      },
    )
  }

  type QuickAction = { icon: React.ComponentType<{className?:string}>; label: string; desc: string; path: string; color: string; bg: string }
  const quickActions: QuickAction[] = []
  if (hasAnyRole(['admin'])) {
    quickActions.push(
      { icon: ShieldCheck, label: 'Manage Users', desc: 'Add or update roles', path: '/app/admin', color: 'text-blue-500', bg: 'bg-blue-500/10' },
      { icon: CalendarDays, label: 'View Calendar', desc: 'Schedule & events', path: '/app/calendar', color: 'text-purple-500', bg: 'bg-purple-500/10' },
      { icon: ClipboardList, label: 'Assignments', desc: 'Manage exams & work', path: '/app/exams', color: 'text-amber-500', bg: 'bg-amber-500/10' },
    )
  }
  if (hasAnyRole(['teacher'])) {
    quickActions.push(
      { icon: CloudUpload, label: 'Upload Material', desc: 'Add assets to courses', path: '/app/teacher', color: 'text-indigo-500', bg: 'bg-indigo-500/10' },
      { icon: ClipboardList, label: 'Publish Assignment', desc: 'Create exams & work', path: '/app/exams', color: 'text-amber-500', bg: 'bg-amber-500/10' },
      { icon: CalendarDays, label: 'Update Calendar', desc: 'Add course events', path: '/app/calendar', color: 'text-purple-500', bg: 'bg-purple-500/10' },
    )
  }
  if (hasAnyRole(['student'])) {
    quickActions.push(
      { icon: BookOpen, label: 'Browse Catalog', desc: 'Find course materials', path: '/app/student', color: 'text-blue-500', bg: 'bg-blue-500/10' },
      { icon: ClipboardList, label: 'Submit Work', desc: 'View & submit assignments', path: '/app/exams', color: 'text-amber-500', bg: 'bg-amber-500/10' },
      { icon: MessageSquare, label: 'Open Forum', desc: 'Ask questions & discuss', path: '/app/forum', color: 'text-pink-500', bg: 'bg-pink-500/10' },
    )
  }

  const greeting = () => {
    const h = new Date().getHours()
    if (h < 12) return 'Good morning'
    if (h < 18) return 'Good afternoon'
    return 'Good evening'
  }

  return (
    <div className="space-y-8">
      {/* Hero header */}
      <div className="relative overflow-hidden rounded-2xl border border-border/40 bg-gradient-to-br from-primary/8 via-background to-accent/5 p-6 shadow-sm">
        <div className="absolute inset-0 bg-grid-white/[0.02] pointer-events-none" />
        <div className="relative">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-primary">{greeting()},</p>
              <h2 className="text-3xl font-bold tracking-tight mt-0.5">{username}</h2>
              <p className="text-muted-foreground mt-1 text-sm">
                Your academic workspace is ready — here's what's happening today.
              </p>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {roles.filter(r => ['admin', 'teacher', 'student'].includes(r)).map(role => (
                <Badge
                  key={role}
                  variant={role === 'admin' ? 'destructive' : role === 'teacher' ? 'default' : 'secondary'}
                  className="capitalize px-3 py-1 text-xs font-semibold"
                >
                  {role}
                </Badge>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {stats.map((stat, i) => (
          <Card
            key={i}
            className={`border ${stat.border} bg-card/80 backdrop-blur-sm transition-all duration-200 hover:shadow-md hover:-translate-y-0.5`}
          >
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">{stat.title}</CardTitle>
              <div className={`rounded-xl p-2.5 ${stat.bg}`}>
                <stat.icon className={`size-4 ${stat.color}`} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex items-end gap-2">
                {loading ? (
                  <Loader2 className="size-6 animate-spin text-muted-foreground" />
                ) : (
                  <p className="text-3xl font-bold tracking-tight">{stat.value}</p>
                )}
              </div>
              <p className="text-xs text-muted-foreground mt-1.5 flex items-center gap-1">
                <TrendingUp className="size-3 text-emerald-500" />
                {stat.desc}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-7">
        {/* Activity Feed */}
        <Card className="lg:col-span-4 border-border/50 bg-card/80 backdrop-blur-sm shadow-sm">
          <CardHeader className="pb-3 border-b border-border/40">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-base">Recent Activity</CardTitle>
                <CardDescription className="text-xs mt-0.5">
                  Latest forum threads across the platform.
                </CardDescription>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="gap-1.5 text-xs text-muted-foreground hover:text-foreground"
                onClick={() => navigate('/app/forum')}
              >
                View all <ArrowRight className="size-3" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="pt-3">
            {recentThreads.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-[200px] rounded-xl border border-dashed border-border/60 bg-muted/20 text-center">
                <MessageSquare className="size-8 text-muted-foreground/40 mb-2" />
                <p className="text-sm font-medium text-muted-foreground">No forum activity yet</p>
                <p className="text-xs text-muted-foreground/70 mt-1">Start a thread in the Forum.</p>
                <Button
                  size="sm"
                  variant="outline"
                  className="mt-4 text-xs"
                  onClick={() => navigate('/app/forum')}
                >
                  Go to Forum
                </Button>
              </div>
            ) : (
              <div className="space-y-1">
                {recentThreads.map(t => (
                  <button
                    key={t.thread_id}
                    onClick={() => navigate('/app/forum')}
                    className="w-full flex items-start gap-3 p-3 rounded-xl hover:bg-muted/50 transition-colors text-left group"
                  >
                    <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary text-xs font-bold">
                      {t.author_name.slice(0, 2).toUpperCase()}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium line-clamp-1 group-hover:text-primary transition-colors">{t.title}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-xs text-muted-foreground">{t.author_name}</span>
                        <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-4">{t.module_code}</Badge>
                      </div>
                    </div>
                    <span className="text-[10px] text-muted-foreground shrink-0 mt-0.5">
                      {new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' }).format(new Date(t.created_at))}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card className="lg:col-span-3 border-border/50 bg-card/80 backdrop-blur-sm shadow-sm">
          <CardHeader className="pb-3 border-b border-border/40">
            <CardTitle className="text-base">Quick Actions</CardTitle>
            <CardDescription className="text-xs mt-0.5">
              Common tasks for your role.
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-3 space-y-2">
            {quickActions.map((action) => (
              <button
                key={action.path}
                onClick={() => navigate(action.path)}
                className="w-full flex items-center gap-3 rounded-xl border border-border/50 p-3.5 hover:bg-muted/60 hover:border-border transition-all duration-150 group text-left"
              >
                <div className={`shrink-0 flex size-9 items-center justify-center rounded-lg ${action.bg}`}>
                  <action.icon className={`size-4 ${action.color}`} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold group-hover:text-primary transition-colors">{action.label}</p>
                  <p className="text-xs text-muted-foreground">{action.desc}</p>
                </div>
                <ArrowRight className="size-3.5 text-muted-foreground/50 group-hover:text-primary group-hover:translate-x-0.5 transition-all shrink-0" />
              </button>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
