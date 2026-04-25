import { useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/auth-context'
import { useTheme } from '@/context/theme-context'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { GraduationCap, Moon, Sun, Eye, EyeOff, AlertCircle, BookOpen, Users, Bell, CalendarDays, MessageSquare, ClipboardList } from 'lucide-react'

export function LoginPage() {
  const { isAuthenticated, login } = useAuth()
  const { resolved, setTheme } = useTheme()
  const navigate = useNavigate()
  const location = useLocation()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  if (isAuthenticated) return <Navigate to="/app" replace />

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(username, password)
      const from = (location.state as { from?: string } | null)?.from
      navigate(from || '/app', { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed. Check your credentials.')
    } finally {
      setLoading(false)
    }
  }

  const features = [
    {
      icon: BookOpen,
      title: 'Course Management',
      desc: 'Create and browse course materials with one-click downloads',
      color: 'text-blue-400',
      bg: 'bg-blue-400/10 border-blue-400/20',
    },
    {
      icon: ClipboardList,
      title: 'Assignments & Exams',
      desc: 'Publish assignments, submit work, and receive grades',
      color: 'text-amber-400',
      bg: 'bg-amber-400/10 border-amber-400/20',
    },
    {
      icon: MessageSquare,
      title: 'Forum & Live Chat',
      desc: 'Discuss topics and collaborate in real-time with peers',
      color: 'text-pink-400',
      bg: 'bg-pink-400/10 border-pink-400/20',
    },
    {
      icon: CalendarDays,
      title: 'Academic Calendar',
      desc: 'Track course schedules, exams, and important deadlines',
      color: 'text-purple-400',
      bg: 'bg-purple-400/10 border-purple-400/20',
    },
    {
      icon: Bell,
      title: 'Smart Notifications',
      desc: 'Stay informed with real-time platform activity updates',
      color: 'text-emerald-400',
      bg: 'bg-emerald-400/10 border-emerald-400/20',
    },
    {
      icon: Users,
      title: 'Role-Based Access',
      desc: 'Tailored experience for admins, teachers, and students',
      color: 'text-cyan-400',
      bg: 'bg-cyan-400/10 border-cyan-400/20',
    },
  ]

  return (
    <div className="relative flex min-h-screen overflow-hidden">
      {/* Theme toggle */}
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setTheme(resolved === 'dark' ? 'light' : 'dark')}
        className="absolute right-4 top-4 z-20 text-muted-foreground hover:text-foreground"
      >
        {resolved === 'dark' ? <Sun className="size-5" /> : <Moon className="size-5" />}
      </Button>

      {/* Left panel — branding */}
      <div className="relative hidden flex-1 flex-col justify-between overflow-hidden bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-12 lg:flex">
        {/* Background decoration */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary/20 via-transparent to-accent/10 pointer-events-none" />
        <div className="absolute top-0 left-0 w-96 h-96 bg-primary/10 rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2 pointer-events-none" />
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-accent/10 rounded-full blur-3xl translate-x-1/2 translate-y-1/2 pointer-events-none" />

        {/* Header */}
        <div className="relative z-10 flex items-center gap-3">
          <div className="flex size-11 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-primary/60 text-white shadow-xl shadow-primary/30">
            <GraduationCap className="size-6" />
          </div>
          <div>
            <h2 className="text-xl font-bold tracking-tight text-white">ENT EST Salé</h2>
            <p className="text-xs text-slate-400 font-medium">Espace Numérique de Travail</p>
          </div>
        </div>

        {/* Main content */}
        <div className="relative z-10 space-y-8">
          <div className="space-y-3">
            <h3 className="text-3xl font-bold leading-tight text-white">
              Your academic universe,<br />
              <span className="text-primary">all in one place.</span>
            </h3>
            <p className="text-slate-400 text-sm leading-relaxed max-w-md">
              Access courses, collaborate with peers, manage assignments, and stay connected with your academic community — built for EST Salé.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            {features.map((feature) => (
              <div
                key={feature.title}
                className={`flex items-start gap-3 rounded-xl border ${feature.bg} p-3 backdrop-blur-sm`}
              >
                <div className={`shrink-0 rounded-lg p-1.5 ${feature.bg}`}>
                  <feature.icon className={`size-4 ${feature.color}`} />
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-white leading-tight">{feature.title}</p>
                  <p className="text-[10px] text-slate-400 mt-0.5 leading-snug">{feature.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="relative z-10">
          <p className="text-xs text-slate-500">
            © 2025 EST Salé — Academic Digital Platform. Built with FastAPI & React.
          </p>
        </div>
      </div>

      {/* Right panel — login form */}
      <div className="flex flex-1 items-center justify-center p-6 bg-background">
        <div className="w-full max-w-[400px] space-y-6">
          {/* Mobile logo */}
          <div className="flex items-center gap-3 lg:hidden">
            <div className="flex size-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-primary/70 text-primary-foreground shadow-lg">
              <GraduationCap className="size-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold tracking-tight">ENT EST Salé</h2>
              <p className="text-xs text-muted-foreground">Espace Numérique de Travail</p>
            </div>
          </div>

          <Card className="border-border/50 bg-card/95 shadow-2xl backdrop-blur-xl">
            <CardHeader className="space-y-1 pb-4">
              <CardTitle className="text-2xl font-bold">Welcome back</CardTitle>
              <p className="text-sm text-muted-foreground">
                Sign in to access your academic workspace.
              </p>
            </CardHeader>

            <CardContent>
              <form className="space-y-4" onSubmit={handleSubmit}>
                <div className="space-y-2">
                  <Label htmlFor="username" className="text-sm font-medium">
                    Username
                  </Label>
                  <Input
                    id="username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="Enter your username"
                    className="h-11"
                    autoComplete="username"
                    autoFocus
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password" className="text-sm font-medium">
                    Password
                  </Label>
                  <div className="relative">
                    <Input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Enter your password"
                      className="h-11 pr-10"
                      autoComplete="current-password"
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="absolute right-1 top-1 size-9 text-muted-foreground hover:text-foreground"
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                    </Button>
                  </div>
                </div>

                {error && (
                  <Alert variant="destructive" className="py-2">
                    <AlertCircle className="size-4" />
                    <AlertDescription className="ml-2 text-sm">{error}</AlertDescription>
                  </Alert>
                )}

                <Button
                  type="submit"
                  disabled={loading || !username || !password}
                  className="h-11 w-full text-sm font-semibold shadow-md shadow-primary/20 transition-all hover:shadow-lg hover:shadow-primary/30 hover:-translate-y-0.5"
                >
                  {loading ? (
                    <span className="flex items-center gap-2">
                      <span className="size-4 animate-spin rounded-full border-2 border-primary-foreground/30 border-t-primary-foreground" />
                      Signing in...
                    </span>
                  ) : (
                    'Sign in to ENT'
                  )}
                </Button>

                <div className="pt-2 rounded-xl bg-muted/40 border border-border/40 p-3">
                  <p className="text-xs font-medium text-muted-foreground mb-2">Demo accounts</p>
                  <div className="flex flex-wrap gap-1.5">
                    {[
                      { user: 'admin1', pwd: 'Admin_123!', label: 'Admin' },
                      { user: 'teacher1', pwd: 'Teacher_123!', label: 'Teacher' },
                      { user: 'student1', pwd: 'Student_123!', label: 'Student' },
                    ].map(({ user, pwd, label }) => (
                      <button
                        key={user}
                        type="button"
                        onClick={() => { setUsername(user); setPassword(pwd) }}
                        className="rounded-md border border-border/50 bg-background/70 px-2 py-1 text-[10px] font-mono font-medium hover:bg-muted hover:border-primary/30 transition-colors"
                      >
                        {user} <span className="text-muted-foreground">({label})</span>
                      </button>
                    ))}
                  </div>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
