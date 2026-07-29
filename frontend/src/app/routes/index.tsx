import { createBrowserRouter, Navigate, RouterProvider } from 'react-router-dom'
import { AppLayout } from '@/app/layout/AppLayout'
import { ProtectedRoute } from './ProtectedRoute'
import {
  AdminPage,
  BaleManagementPage,
  LoginPage,
  LotsPage,
  NotFoundPage,
  ProfilePage,
  BaleReceptionPage,
  BaleStockPage,
  ReportsPage,
  SpinningPage,
  WarehousePage,
} from './lazy-pages'

const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <Navigate to="/warehouse/bales" replace /> },
      { path: 'warehouse/bales', element: <BaleManagementPage /> },
      { path: 'warehouse/bales/reception', element: <BaleReceptionPage /> },
      { path: 'warehouse/bales/stock', element: <BaleStockPage /> },
      { path: 'warehouse/identity', element: <WarehousePage /> },
      { path: 'warehouse/issue', element: <WarehousePage /> },
      { path: 'warehouse/finished-product', element: <WarehousePage /> },
      { path: 'warehouse/classification', element: <WarehousePage /> },
      { path: 'warehouse/exits', element: <WarehousePage /> },
      { path: 'warehouse/supplies', element: <WarehousePage /> },
      { path: 'warehouse/stock', element: <WarehousePage /> },
      { path: 'spinning/dashboard', element: <SpinningPage /> },
      { path: 'spinning/unloads', element: <SpinningPage /> },
      { path: 'spinning/progress', element: <SpinningPage /> },
      { path: 'spinning/quality', element: <SpinningPage /> },
      { path: 'spinning/waste', element: <SpinningPage /> },
      { path: 'spinning/skeins', element: <SpinningPage /> },
      { path: 'spinning/consolidated', element: <SpinningPage /> },
      { path: 'lots/queue', element: <LotsPage /> },
      { path: 'lots/detail', element: <LotsPage /> },
      { path: 'reports/daily', element: <ReportsPage /> },
      { path: 'reports/production', element: <ReportsPage /> },
      { path: 'reports/traceability', element: <ReportsPage /> },
      { path: 'admin/master-data', element: <AdminPage /> },
      { path: 'profile', element: <ProfilePage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])

export function AppRouter() {
  return <RouterProvider router={router} />
}
