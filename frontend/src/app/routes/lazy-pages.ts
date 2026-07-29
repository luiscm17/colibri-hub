import { lazy } from 'react'

export const LoginPage = lazy(() => import('@/features/auth/pages/LoginPage'))
export const NotFoundPage = lazy(() => import('@/features/not-found/pages/NotFoundPage'))
export const WarehousePage = lazy(() => import('@/features/warehouse/pages/WarehousePage'))
export const BaleReceptionPage = lazy(() => import('@/features/warehouse/bales/pages/BaleReceptionPage'))
export const BaleManagementPage = lazy(
  () => import('@/features/warehouse/bales/pages/BaleManagementPage'),
)
export const SpinningPage = lazy(() => import('@/features/spinning/pages/SpinningPage'))
export const LotsPage = lazy(() => import('@/features/lots/pages/LotsPage'))
export const ReportsPage = lazy(() => import('@/features/reports/pages/ReportsPage'))
export const AdminPage = lazy(() => import('@/features/admin/pages/AdminPage'))
export const ProfilePage = lazy(() => import('@/features/profile/pages/ProfilePage'))
