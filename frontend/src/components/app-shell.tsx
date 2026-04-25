import { useState, useEffect, useCallback } from 'react'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Separator } from '@/components/ui/separator'
import { roleBadgeVariant } from '@/lib/auth'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/auth-context'
import { useTheme } from '@/context/theme-context'
import {
  Bell,
  BookOpenText,
  CalendarDays,
  ChevronLeft,
  ClipboardList,
  CloudUpload,
  GraduationCap,
  LayoutDashboard,
  LogOut,
  Menu,
  MessageSquare,
  Moon,
  ShieldCheck,
  Sparkles,
  Sun,
  User,
} from 'lucide-react'

type NavItem = {
  to: string
  label: string
  icon: React.ComponentType<{ className?: string }>
  roles: string[]
}

const navItems: NavItem[] = [
  { to: '/app', label: 'Dashboard', icon: LayoutDashboard, roles: [] },
  { to: '/app/assistant', label: 'AI Assistant', icon: Sparkles, roles: [] },
  { to: '/app/admin', label: 'User Management', icon: ShieldCheck, roles: ['admin'] },
  { to: '/app/teacher', label: 'Course Studio', icon: CloudUpload, roles: ['teacher', 'admin'] },
  { to: '/app/student', label: 'Course Catalog', icon: BookOpenText, roles: ['student'] },
  { to: '/app/calendar', label: 'Calendar', icon: CalendarDays, roles: [] },
  { to: '/app/forum', label: 'Forum', icon: MessageSquare, roles: [] },
  { to: '/app/exams', label: 'Assignments', icon: ClipboardList, roles: ['teacher', 'admin', 'student'] },
  { to: '/app/notifications', label: 'Notifications', icon: Bell, roles: [] },
]

export function AppShell() {
  const { username, roles, logout, hasAnyRole, claims, apiFetch } = useAuth()
  const { resolved, setTheme } = useTheme()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [unreadCount, setUnreadCount] = useState(0)

  const fetchUnreadCount = useCallback(async () => {
    try {
      const notifications = await apiFetch<{ read: boolean }[]>('/api/notifications')
      setUnreadCount(notifications.filter(n => !n.read).length)
    } catch {
      // graceful fail
    }
  }, [apiFetch])

  useEffect(() => {
    fetchUnreadCount()
    // Refresh every 60 seconds
    const interval = setInterval(fetchUnreadCount, 60000)
    return () => clearInterval(interval)
  }, [fetchUnreadCount])

  function handleLogout() {
    logout()
    navigate('/login')
  }

  const toggleTheme = () => setTheme(resolved === 'dark' ? 'light' : 'dark')
  const initials = username.slice(0, 2).toUpperCase()
  const primaryRole = roles[0] || 'user'

  const sidebarContent = (
    <>
      {/* Logo */}
      <div className={`flex items-center gap-3 px-4 py-5 ${!sidebarOpen ? 'justify-center' : ''}`}>
        <Link to="/app" className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-primary/70 text-primary-foreground shadow-md hover:shadow-primary/30 transition-shadow">
          <GraduationCap className="size-5" />
        </Link>
        {sidebarOpen && (
          <div className="animate-in fade-in slide-in-from-left-2 duration-200 min-w-0">
            <p className="text-sm font-bold tracking-tight truncate">ENT EST Salé</p>
            <p className="text-[10px] font-medium uppercase tracking-widest text-muted-foreground">
              Workspace
            </p>
          </div>
        )}
      </div>

      <Separator className="mx-4 w-auto opacity-50" />

      {/* User Card */}
      <div className="p-3">
        <div className={`flex items-center gap-3 rounded-xl border border-border/40 bg-muted/40 p-3 transition-all ${!sidebarOpen ? 'justify-center' : ''}`}>
          <Avatar className="size-9 shrink-0 border-2 border-primary/20 shadow-sm">
            <AvatarFallback className="bg-gradient-to-br from-primary/20 to-accent/20 text-xs font-bold">
              {initials}
            </AvatarFallback>
          </Avatar>
          {sidebarOpen && (
            <div className="min-w-0 animate-in fade-in slide-in-from-left-2 duration-200">
              <p className="truncate text-sm font-semibold">{username}</p>
              <div className="mt-1 flex flex-wrap gap-1">
                {roles.length ? (
                  roles.filter(r => ['admin', 'teacher', 'student'].includes(r)).map((role) => (
                    <Badge key={role} variant={roleBadgeVariant(role)} className="text-[10px] px-1.5 py-0 h-4">
                      {role}
                    </Badge>
                  ))
                ) : (
                  <Badge variant="outline" className="text-[10px]">user</Badge>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-0.5 px-3 py-2">
        {sidebarOpen && (
          <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/70">
            Navigation
          </p>
        )}
        {navItems
          .filter((item) => item.roles.length === 0 || hasAnyRole(item.roles))
          .map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/app'}
              onClick={() => setMobileOpen(false)}
              className={({ isActive }) =>
                `group relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150 ${
                  isActive
                    ? 'bg-primary text-primary-foreground shadow-sm shadow-primary/20'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                } ${!sidebarOpen ? 'justify-center' : ''}`
              }
            >
              <item.icon className="size-4 shrink-0" />
              {sidebarOpen && (
                <span className="animate-in fade-in slide-in-from-left-1 duration-150 flex-1">
                  {item.label}
                </span>
              )}
              {/* Notification count badge on Bell nav item */}
              {item.to === '/app/notifications' && unreadCount > 0 && (
                <span className={`flex items-center justify-center rounded-full bg-destructive text-destructive-foreground text-[9px] font-bold leading-none ${sidebarOpen ? 'min-w-4 h-4 px-1' : 'absolute -top-0.5 -right-0.5 size-4'}`}>
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </NavLink>
          ))}
      </nav>

      {/* Bottom */}
      <div className="border-t border-border/40 p-3 space-y-1">
        <Button
          onClick={handleLogout}
          variant="ghost"
          size="sm"
          className={`w-full gap-2 text-muted-foreground hover:text-destructive hover:bg-destructive/10 ${!sidebarOpen ? 'justify-center px-0' : 'justify-start'}`}
        >
          <LogOut className="size-4 shrink-0" />
          {sidebarOpen && 'Sign Out'}
        </Button>
      </div>
    </>
  )

  return (
    <div className="flex min-h-screen bg-background">
      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex flex-col border-r border-border/50 bg-card/95 backdrop-blur-xl transition-all duration-300 lg:relative lg:z-auto ${
          sidebarOpen ? 'w-64' : 'w-[72px]'
        } ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}
      >
        {sidebarContent}

        {/* Collapse button */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="absolute -right-3 top-7 z-10 hidden size-6 items-center justify-center rounded-full border border-border bg-card shadow-md transition-colors hover:bg-muted lg:flex"
        >
          <ChevronLeft className={`size-3.5 transition-transform duration-200 ${!sidebarOpen ? 'rotate-180' : ''}`} />
        </button>
      </aside>

      {/* Main content */}
      <div className="flex flex-1 flex-col min-w-0">
        {/* Header */}
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border/50 bg-card/80 px-4 backdrop-blur-xl sm:px-6">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden"
              onClick={() => setMobileOpen(true)}
            >
              <Menu className="size-5" />
            </Button>
            <div>
              <h1 className="text-sm font-semibold capitalize">{primaryRole} Workspace</h1>
              <p className="text-xs text-muted-foreground hidden sm:block">
                Welcome back, {claims?.preferred_username || username}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            {/* Theme Toggle */}
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleTheme}
              className="text-muted-foreground hover:text-foreground size-9"
            >
              {resolved === 'dark' ? <Sun className="size-4" /> : <Moon className="size-4" />}
            </Button>

            {/* Notifications Bell */}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => {
                navigate('/app/notifications')
                setUnreadCount(0)
              }}
              className="relative text-muted-foreground hover:text-foreground size-9"
            >
              <Bell className="size-4" />
              {unreadCount > 0 && (
                <span className="absolute right-1.5 top-1.5 flex size-4 items-center justify-center rounded-full bg-destructive text-[9px] font-bold text-destructive-foreground shadow-sm">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </Button>

            <Separator orientation="vertical" className="mx-0.5 h-5 opacity-50" />

            {/* User Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger render={
                <Button variant="ghost" className="gap-2 px-2 h-9">
                  <Avatar className="size-7 border border-border/50">
                    <AvatarFallback className="bg-gradient-to-br from-primary/20 to-accent/20 text-[10px] font-bold">
                      {initials}
                    </AvatarFallback>
                  </Avatar>
                  <span className="hidden text-sm font-medium sm:inline">{username}</span>
                </Button>
              } />
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuItem onClick={() => navigate('/app/profile')}>
                  <User className="mr-2 size-4" />
                  Profile
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => { navigate('/app/notifications'); setUnreadCount(0) }}>
                  <Bell className="mr-2 size-4" />
                  Notifications
                  {unreadCount > 0 && (
                    <Badge variant="destructive" className="ml-auto text-[10px] px-1.5 py-0 h-4">{unreadCount}</Badge>
                  )}
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="text-destructive focus:text-destructive">
                  <LogOut className="mr-2 size-4" />
                  Sign Out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto p-4 sm:p-6 lg:p-8">
          <div className="mx-auto w-full max-w-7xl">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
