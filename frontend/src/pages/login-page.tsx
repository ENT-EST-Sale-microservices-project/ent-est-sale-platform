import { useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/auth-context'
import { useTheme } from '@/context/theme-context'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { GraduationCap, Moon, Sun, Eye, EyeOff, AlertCircle } from 'lucide-react'

export function LoginPage() {
  const { isAuthenticated, login } = useAuth()
  const { resolved, setTheme } = useTheme()
  const navigate = useNavigate()
  const location = useLocation()
  const [username, setUsername] = useState('admin1')
  const [password, setPassword] = useState('Admin_123!')
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
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative flex min-h-screen">
      {/* Theme toggle */}
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setTheme(resolved === 'dark' ? 'light' : 'dark')}
        className="absolute right-4 top-4 z-10 text-muted-foreground hover:text-foreground"
      >
        {resolved === 'dark' ? <Sun className="size-5" /> : <Moon className="size-5" />}
      </Button>

      {/* Left panel — branding */}
      <div className="hidden flex-1 items-center justify-center bg-gradient-to-br from-primary/10 via-accent/5 to-background lg:flex">
        <div className="w-full max-w-md space-y-8 px-8">
          <div className="flex items-center gap-3">
            <div className="flex size-12 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-primary/70 text-primary-foreground shadow-lg">
              <GraduationCap className="size-7" />
            </div>
            <div>
              <h2 className="text-2xl font-bold tracking-tight">ENT EST Salé</h2>
              <p className="text-sm text-muted-foreground">Espace Numérique de Travail</p>
            </div>
          </div>

          <div className="space-y-6">
            <div className="space-y-2">
              <h3 className="text-lg font-semibold text-foreground">Your Academic Platform</h3>
              <p className="text-sm leading-relaxed text-muted-foreground">
                Access courses, manage assignments, collaborate with peers, and stay connected
                with your academic community — all in one place.
              </p>
            </div>

            <div className="grid gap-3">
              {[
                { icon: '📚', title: 'Course Management', desc: 'Create, browse, and download course materials' },
                { icon: '👥', title: 'User Administration', desc: 'Role-based access for admins, teachers, and students' },
                { icon: '🔔', title: 'Real-time Notifications', desc: 'Stay updated with events and announcements' },
              ].map((feature) => (
                <div
                  key={feature.title}
                  className="flex items-start gap-3 rounded-lg border border-border/50 bg-card/50 p-3 backdrop-blur-sm"
                >
                  <span className="text-lg">{feature.icon}</span>
                  <div>
                    <p className="text-sm font-medium">{feature.title}</p>
                    <p className="text-xs text-muted-foreground">{feature.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Right panel — login form */}
      <div className="flex flex-1 items-center justify-center p-6">
        <Card className="w-full max-w-[420px] border-border/50 bg-card/95 shadow-2xl backdrop-blur-xl">
          <CardHeader className="space-y-3 pb-4">
            {/* Mobile logo */}
            <div className="flex items-center gap-2 lg:hidden">
              <div className="flex size-9 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-primary/70 text-primary-foreground shadow-md">
                <GraduationCap className="size-5" />
              </div>
              <span className="text-sm font-bold tracking-tight">ENT EST Salé</span>
            </div>

            <div>
              <CardTitle className="text-2xl font-bold">Welcome back</CardTitle>
              <CardDescription className="mt-1">
                Sign in with your Keycloak credentials to continue.
              </CardDescription>
            </div>
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
                    className="absolute right-1 top-1 size-9 text-muted-foreground"
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
                className="h-11 w-full text-sm font-semibold shadow-md shadow-primary/20 transition-all hover:shadow-lg hover:shadow-primary/30"
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <span className="size-4 animate-spin rounded-full border-2 border-primary-foreground/30 border-t-primary-foreground" />
                    Signing in...
                  </span>
                ) : (
                  'Sign in'
                )}
              </Button>

              <div className="pt-2">
                <p className="text-center text-xs text-muted-foreground">
                  Dev accounts: <code className="rounded bg-muted px-1 py-0.5 font-mono text-[10px]">admin1</code>{' '}
                  <code className="rounded bg-muted px-1 py-0.5 font-mono text-[10px]">teacher1</code>{' '}
                  <code className="rounded bg-muted px-1 py-0.5 font-mono text-[10px]">student1</code>
                </p>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
