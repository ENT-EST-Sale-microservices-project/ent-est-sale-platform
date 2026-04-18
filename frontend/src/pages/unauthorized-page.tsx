import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { ShieldAlert, ArrowLeft, LogOut } from 'lucide-react'
import { useAuth } from '@/context/auth-context'

export function UnauthorizedPage() {
  const navigate = useNavigate()
  const { logout } = useAuth()
  
  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background p-4 text-center">
      <div className="flex size-24 items-center justify-center rounded-full bg-destructive/10 text-destructive mb-8 shadow-sm">
        <ShieldAlert className="size-12" />
      </div>
      <h1 className="text-3xl font-bold tracking-tight sm:text-4xl mb-4">Access Denied</h1>
      <p className="text-muted-foreground max-w-md mx-auto mb-8 leading-relaxed">
        You do not have the required permissions to access this page. If you believe this is an error, please contact your administrator to request access.
      </p>
      <div className="flex flex-col sm:flex-row gap-4">
        <Button onClick={() => navigate('/app')} size="lg" className="gap-2">
          <ArrowLeft className="size-4" />
          Back to Dashboard
        </Button>
        <Button onClick={handleLogout} variant="outline" size="lg" className="gap-2 text-muted-foreground">
          <LogOut className="size-4" />
          Sign Out
        </Button>
      </div>
    </div>
  )
}
