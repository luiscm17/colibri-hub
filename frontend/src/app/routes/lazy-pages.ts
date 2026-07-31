import { lazy } from 'react'

export const LoginPage = lazy(() => import('@/features/auth/pages/LoginPage'))
export const NotFoundPage = lazy(() => import('@/features/not-found/pages/NotFoundPage'))
export const BaleReceptionPage = lazy(() => import('@/features/warehouse/bales/pages/BaleReceptionPage'))
export const BaleStockPage = lazy(() => import('@/features/warehouse/bales/pages/BaleStockPage'))
export const BaleDeliveryPage = lazy(() => import('@/features/warehouse/bales/pages/BaleDeliveryPage'))
export const BaleManagementPage = lazy(
  () => import('@/features/warehouse/bales/pages/BaleManagementPage'),
)
export const SpinningPage = lazy(() => import('@/features/spinning/pages/SpinningPage'))
export const LotsPage = lazy(() => import('@/features/lots/pages/LotsPage'))
export const ReportsPage = lazy(() => import('@/features/reports/pages/ReportsPage'))
export const AdminPage = lazy(() => import('@/features/admin/pages/AdminPage'))
export const ProfilePage = lazy(() => import('@/features/profile/pages/ProfilePage'))
