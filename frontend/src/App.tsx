import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from '@/components/app-shell'
import { ProtectedRoute, RoleRoute } from '@/components/route-guards'
import { AdminPage } from '@/pages/admin-page'
import { LoginPage } from '@/pages/login-page'
import { NotFoundPage } from '@/pages/not-found-page'
import { DashboardPage } from '@/pages/dashboard-page'
import { StudentPage } from '@/pages/student-page'
import { TeacherPage } from '@/pages/teacher-page'
import { NotificationsPage } from '@/pages/notifications-page'
import { ProfilePage } from '@/pages/profile-page'
import { UnauthorizedPage } from '@/pages/unauthorized-page'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/app" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/unauthorized" element={<UnauthorizedPage />} />

      <Route
        path="/app"
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="notifications" element={<NotificationsPage />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route
          path="admin"
          element={
            <RoleRoute allowedRoles={['admin']}>
              <AdminPage />
            </RoleRoute>
          }
        />
        <Route
          path="teacher"
          element={
            <RoleRoute allowedRoles={['teacher', 'admin']}>
              <TeacherPage />
            </RoleRoute>
          }
        />
        <Route
          path="student"
          element={
            <RoleRoute allowedRoles={['student']}>
              <StudentPage />
            </RoleRoute>
          }
        />
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
