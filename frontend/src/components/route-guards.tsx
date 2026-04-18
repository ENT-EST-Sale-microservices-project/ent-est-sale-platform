import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/context/auth-context'

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth()
  const location = useLocation()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }
  return <>{children}</>
}

export function RoleRoute({
  children,
  allowedRoles,
}: {
  children: React.ReactNode
  allowedRoles: string[]
}) {
  const { hasAnyRole } = useAuth()
  if (!hasAnyRole(allowedRoles)) {
    return <Navigate to="/unauthorized" replace />
  }
  return <>{children}</>
}
