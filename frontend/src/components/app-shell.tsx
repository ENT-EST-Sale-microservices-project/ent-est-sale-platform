import { useState } from 'react'
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
  ChevronLeft,
  CloudUpload,
  GraduationCap,
  LayoutDashboard,
  LogOut,
  Menu,
  Moon,
  ShieldCheck,
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
  { to: '/app/admin', label: 'User Management', icon: ShieldCheck, roles: ['admin'] },
  { to: '/app/teacher', label: 'Course Studio', icon: CloudUpload, roles: ['teacher', 'admin'] },
  { to: '/app/student', label: 'Course Catalog', icon: BookOpenText, roles: ['student'] },
  { to: '/app/notifications', label: 'Notifications', icon: Bell, roles: [] },
]

export function AppShell() {
  const { username, roles, logout, hasAnyRole, claims } = useAuth()
  const { resolved, setTheme } = useTheme()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [mobileOpen, setMobileOpen] = useState(false)

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
      <div className="flex items-center gap-3 px-4 py-5">
        <div className="flex size-9 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-primary/70 text-primary-foreground shadow-md">
          <GraduationCap className="size-5" />
        </div>
        {sidebarOpen && (
          <div className="animate-in fade-in slide-in-from-left-2 duration-200">
            <p className="text-sm font-bold tracking-tight">ENT EST Salé</p>
            <p className="text-[10px] font-medium uppercase tracking-widest text-muted-foreground">
              Workspace
            </p>
          </div>
        )}
      </div>

      <Separator className="mx-4 w-auto" />

      {/* User Card */}
      <div className="p-3">
        <div className={`flex items-center gap-3 rounded-xl border border-border/50 bg-muted/50 p-3 transition-all ${!sidebarOpen ? 'justify-center' : ''}`}>
          <Avatar className="size-9 border-2 border-primary/20 shadow-sm">
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
                    <Badge key={role} variant={roleBadgeVariant(role)} className="text-[10px] px-1.5 py-0">
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
      <nav className="flex-1 space-y-1 px-3 py-2">
        {sidebarOpen && (
          <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
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
                `group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200 ${isActive
                  ? 'bg-primary text-primary-foreground shadow-md shadow-primary/20'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                } ${!sidebarOpen ? 'justify-center' : ''}`
              }
            >
              <item.icon className="size-4 shrink-0" />
              {sidebarOpen && (
                <span className="animate-in fade-in slide-in-from-left-1 duration-150">
                  {item.label}
                </span>
              )}
            </NavLink>
          ))}
      </nav>

      {/* Bottom */}
      <div className="border-t border-border/50 p-3">
        <Button
          onClick={handleLogout}
          variant="ghost"
          className={`w-full gap-2 text-muted-foreground hover:text-destructive ${!sidebarOpen ? 'px-0' : ''}`}
        >
          <LogOut className="size-4" />
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
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex flex-col border-r border-border/50 bg-card/95 backdrop-blur-xl transition-all duration-300 lg:relative lg:z-auto ${sidebarOpen ? 'w-64' : 'w-[72px]'
          } ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}
      >
        {sidebarContent}

        {/* Collapse button (desktop only) */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="absolute -right-3 top-7 z-10 hidden size-6 items-center justify-center rounded-full border bg-card shadow-sm transition-colors hover:bg-muted lg:flex"
        >
          <ChevronLeft className={`size-3.5 transition-transform ${!sidebarOpen ? 'rotate-180' : ''}`} />
        </button>
      </aside>

      {/* Main content */}
      <div className="flex flex-1 flex-col">
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
              <h1 className="text-base font-semibold capitalize">{primaryRole} Workspace</h1>
              <p className="text-xs text-muted-foreground">
                Welcome back, {claims?.preferred_username || username}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Theme Toggle */}
            <Button variant="ghost" size="icon" onClick={toggleTheme} className="text-muted-foreground hover:text-foreground">
              {resolved === 'dark' ? <Sun className="size-[18px]" /> : <Moon className="size-[18px]" />}
            </Button>

            {/* Notifications */}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => navigate('/app/notifications')}
              className="relative text-muted-foreground hover:text-foreground"
            >
              <Bell className="size-[18px]" />
              <span className="absolute right-1.5 top-1.5 size-2 rounded-full bg-primary shadow-sm" />
            </Button>

            <Separator orientation="vertical" className="mx-1 h-6" />

            {/* User Menu */}
            <DropdownMenu>
              <DropdownMenuTrigger render={
                <Button variant="ghost" className="gap-2 px-2">
                  <Avatar className="size-7 border">
                    <AvatarFallback className="bg-gradient-to-br from-primary/20 to-accent/20 text-[10px] font-bold">
                      {initials}
                    </AvatarFallback>
                  </Avatar>
                  {sidebarOpen && (
                    <span className="hidden text-sm font-medium sm:inline">{username}</span>
                  )}
                </Button>
              } />
              <DropdownMenuContent align="end" className="w-48">
                <DropdownMenuItem onClick={() => navigate('/app/profile')}>
                  <User className="mr-2 size-4" />
                  Profile
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => navigate('/app/notifications')}>
                  <Bell className="mr-2 size-4" />
                  Notifications
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
