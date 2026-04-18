import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { ArrowLeft, Ghost } from 'lucide-react'

export function NotFoundPage() {
  const navigate = useNavigate()
  
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background p-4 text-center">
      <div className="flex size-24 items-center justify-center rounded-full bg-muted text-muted-foreground mb-8">
        <Ghost className="size-12 animate-pulse" />
      </div>
      <h1 className="text-4xl font-bold tracking-tight sm:text-5xl mb-4">404</h1>
      <h2 className="text-xl font-semibold tracking-tight text-muted-foreground mb-8">
        Oops! We can't find that page.
      </h2>
      <p className="text-muted-foreground max-w-md mx-auto mb-8">
        The page you are looking for might have been removed, had its name changed, or is temporarily unavailable.
      </p>
      <Button onClick={() => navigate('/app')} size="lg" className="gap-2">
        <ArrowLeft className="size-4" />
        Return to Dashboard
      </Button>
    </div>
  )
}
