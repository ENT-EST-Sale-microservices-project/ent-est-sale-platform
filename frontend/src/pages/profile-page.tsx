import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useAuth } from '@/context/auth-context'
import { roleBadgeVariant } from '@/lib/auth'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { CalendarDays, Key, Mail, Shield, User } from 'lucide-react'

export function ProfilePage() {
  const { username, roles, claims, session } = useAuth()
  
  const initials = username.slice(0, 2).toUpperCase()
  const email = claims?.email || 'No email provided'
  const firstName = claims?.given_name || ''
  const lastName = claims?.family_name || ''
  const fullName = [firstName, lastName].filter(Boolean).join(' ') || username

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Profile</h2>
        <p className="text-muted-foreground">Manage your account settings and preferences.</p>
      </div>

      <div className="grid gap-6 md:grid-cols-3">
        <Card className="md:col-span-1 border-border/50 bg-card/80 backdrop-blur-sm shadow-sm">
          <CardContent className="pt-6 flex flex-col items-center text-center space-y-4">
            <Avatar className="size-24 border-4 border-background shadow-md">
              <AvatarFallback className="text-3xl font-bold bg-gradient-to-br from-primary to-accent text-primary-foreground">
                {initials}
              </AvatarFallback>
            </Avatar>
            <div className="space-y-1">
              <h3 className="text-xl font-bold">{fullName}</h3>
              <p className="text-sm text-muted-foreground">{username}</p>
            </div>
            <div className="flex flex-wrap justify-center gap-1.5 pt-2">
              {roles.length ? (
                roles.filter(r => ['admin', 'teacher', 'student'].includes(r)).map(role => (
                  <Badge key={role} variant={roleBadgeVariant(role)} className="px-2 py-0.5 uppercase tracking-wider text-[10px]">
                    {role}
                  </Badge>
                ))
              ) : (
                <Badge variant="outline">No Role</Badge>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="md:col-span-2 border-border/50 bg-card/80 backdrop-blur-sm shadow-sm">
          <CardHeader>
            <CardTitle>Account Details</CardTitle>
            <CardDescription>
              Information synced from your Keycloak identity provider.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-1">
                <p className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                  <User className="size-4" /> Full Name
                </p>
                <p className="font-medium">{fullName}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                  <Mail className="size-4" /> Email Address
                </p>
                <p className="font-medium">{email}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                  <Shield className="size-4" /> Provider
                </p>
                <p className="font-medium capitalize">{claims?.iss?.split('/').pop() || 'ENT Keycloak'}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                  <Key className="size-4" /> Account ID
                </p>
                <p className="font-mono text-xs truncate max-w-[200px]" title={claims?.sub}>{claims?.sub || 'Unknown'}</p>
              </div>
            </div>

            <div className="pt-4 border-t border-border/50">
              <h4 className="text-sm font-semibold mb-3">Active Session</h4>
              <div className="rounded-lg border border-border/50 bg-muted/30 p-4 flex items-start gap-3">
                <CalendarDays className="size-5 text-primary shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium">Session Expiry</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {session?.expiresAt ? new Date(session.expiresAt * 1000).toLocaleString() : 'Unknown'}
                  </p>
                  <p className="text-[10px] text-muted-foreground mt-2 italic">
                    Note: The application automatically refreshes your session before it expires while you are active.
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
