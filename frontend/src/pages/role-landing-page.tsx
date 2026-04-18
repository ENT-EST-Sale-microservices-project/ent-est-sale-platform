import { Navigate } from 'react-router-dom'
import { useAuth } from '@/context/auth-context'

export function RoleLandingPage() {
  const { hasAnyRole } = useAuth()

  if (hasAnyRole(['admin'])) return <Navigate to="/app/admin" replace />
  if (hasAnyRole(['teacher'])) return <Navigate to="/app/teacher" replace />
  if (hasAnyRole(['student'])) return <Navigate to="/app/student" replace />

  return <Navigate to="/unauthorized" replace />
}
