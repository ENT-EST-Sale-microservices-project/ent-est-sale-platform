import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuth } from '@/context/auth-context'
import { BookOpen, Users, Clock, ShieldCheck, CloudUpload, GraduationCap, Loader2 } from 'lucide-react'

export function DashboardPage() {
  const { username, roles, hasAnyRole, apiFetch } = useAuth()
  const [data, setData] = useState<Record<string, any>>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadStats() {
      try {
        const res = await apiFetch<Record<string, any>>('/api/stats')
        setData(res)
      } catch (e) {
        console.error("Failed to load stats", e)
      } finally {
        setLoading(false)
      }
    }
    loadStats()
  }, [apiFetch])
  
  const stats = []
  
  if (hasAnyRole(['admin'])) {
    stats.push(
      { title: 'Total Users', value: loading ? <Loader2 className="size-4 animate-spin" /> : data.total_users || 0, icon: Users, desc: 'Registered accounts', color: 'text-blue-500', bg: 'bg-blue-500/10' },
      { title: 'Active Sessions', value: loading ? <Loader2 className="size-4 animate-spin" /> : data.active_sessions || 0, icon: Clock, desc: 'Across all platforms', color: 'text-green-500', bg: 'bg-green-500/10' },
      { title: 'System Status', value: loading ? <Loader2 className="size-4 animate-spin" /> : data.system_status || 'Unknown', icon: ShieldCheck, desc: 'All services running', color: 'text-purple-500', bg: 'bg-purple-500/10' },
    )
  } else if (hasAnyRole(['teacher'])) {
    stats.push(
      { title: 'My Courses', value: loading ? <Loader2 className="size-4 animate-spin" /> : data.total_courses || 0, icon: BookOpen, desc: 'Active courses', color: 'text-blue-500', bg: 'bg-blue-500/10' },
      { title: 'Total Students', value: loading ? <Loader2 className="size-4 animate-spin" /> : data.total_students || 0, icon: Users, desc: 'Across all courses', color: 'text-green-500', bg: 'bg-green-500/10' },
      { title: 'Recent Uploads', value: loading ? <Loader2 className="size-4 animate-spin" /> : data.recent_uploads || 0, icon: CloudUpload, desc: 'Uploaded assets', color: 'text-orange-500', bg: 'bg-orange-500/10' },
    )
  } else {
    stats.push(
      { title: 'Enrolled Courses', value: loading ? <Loader2 className="size-4 animate-spin" /> : data.enrolled_courses || 0, icon: BookOpen, desc: 'Available courses', color: 'text-blue-500', bg: 'bg-blue-500/10' },
      { title: 'Upcoming Deadlines', value: loading ? <Loader2 className="size-4 animate-spin" /> : data.upcoming_deadlines || 0, icon: Clock, desc: 'Within next 7 days', color: 'text-orange-500', bg: 'bg-orange-500/10' },
      { title: 'Completed Credits', value: loading ? <Loader2 className="size-4 animate-spin" /> : data.completed_credits || 0, icon: GraduationCap, desc: 'Overall progress', color: 'text-green-500', bg: 'bg-green-500/10' },
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
        <p className="text-muted-foreground">
          Welcome back to your academic workspace, {username}.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {stats.map((stat, i) => (
          <Card key={i} className="border-border/50 bg-card/80 backdrop-blur-sm transition-all hover:bg-card/90 hover:shadow-md">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{stat.title}</CardTitle>
              <div className={`rounded-md p-2 ${stat.bg}`}>
                <stat.icon className={`size-4 ${stat.color}`} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground mt-1">{stat.desc}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4 border-border/50 bg-card/80 backdrop-blur-sm">
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>
              Your latest interactions across the platform.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex h-[200px] items-center justify-center rounded-md border border-dashed border-border/60 bg-muted/30">
              <p className="text-sm text-muted-foreground text-center">
                Activity feed will appear here.<br/>
                <span className="text-xs opacity-70">(Waiting for Forum/Chat and Exam microservices)</span>
              </p>
            </div>
          </CardContent>
        </Card>
        
        <Card className="col-span-3 border-border/50 bg-card/80 backdrop-blur-sm">
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>
              Common tasks for your role.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4">
             {hasAnyRole(['admin']) && (
               <>
                 <div className="flex items-center gap-4 rounded-lg border border-border/50 p-3 hover:bg-muted/50 transition-colors cursor-pointer">
                    <ShieldCheck className="size-5 text-primary" />
                    <div>
                      <p className="text-sm font-medium">Manage Users</p>
                      <p className="text-xs text-muted-foreground">Add or update roles</p>
                    </div>
                 </div>
               </>
             )}
             {hasAnyRole(['teacher', 'admin']) && (
               <>
                 <div className="flex items-center gap-4 rounded-lg border border-border/50 p-3 hover:bg-muted/50 transition-colors cursor-pointer">
                    <CloudUpload className="size-5 text-primary" />
                    <div>
                      <p className="text-sm font-medium">Upload Material</p>
                      <p className="text-xs text-muted-foreground">Add assets to your courses</p>
                    </div>
                 </div>
               </>
             )}
             {hasAnyRole(['student']) && (
               <>
                 <div className="flex items-center gap-4 rounded-lg border border-border/50 p-3 hover:bg-muted/50 transition-colors cursor-pointer">
                    <BookOpen className="size-5 text-primary" />
                    <div>
                      <p className="text-sm font-medium">Browse Catalog</p>
                      <p className="text-xs text-muted-foreground">Find new course materials</p>
                    </div>
                 </div>
               </>
             )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
