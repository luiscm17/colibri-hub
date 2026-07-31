import { createBrowserRouter, Navigate, RouterProvider } from 'react-router-dom'
import { AppLayout } from '@/app/layout/AppLayout'
import { ProtectedRoute } from './ProtectedRoute'
import { RouteErrorBoundary } from './RouteErrorBoundary'
import { ComingSoon } from '@/common/components/ComingSoon'
import {
  AdminPage,
  BaleManagementPage,
  LoginPage,
  LotsPage,
  NotFoundPage,
  ProfilePage,
  BaleReceptionPage,
  BaleStockPage,
  BaleDeliveryPage,
  ReportsPage,
  SpinningPage,
} from './lazy-pages'

const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
    errorElement: <RouteErrorBoundary />,
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    errorElement: <RouteErrorBoundary />,
    children: [
      { index: true, element: <Navigate to="/warehouse/bales" replace /> },

      // Warehouse — Bale Management (implemented)
      { path: 'warehouse/bales', element: <BaleManagementPage /> },
      { path: 'warehouse/bales/reception', element: <BaleReceptionPage /> },
      { path: 'warehouse/bales/stock', element: <BaleStockPage /> },
      { path: 'warehouse/bales/delivery', element: <BaleDeliveryPage /> },

      // Warehouse — Other capabilities (not yet implemented)
      { path: 'warehouse/identity', element: <ComingSoon feature="Identidad de producción" /> },
      { path: 'warehouse/finished-product', element: <ComingSoon feature="Producto terminado" /> },
      { path: 'warehouse/supplies', element: <ComingSoon feature="Insumos" /> },

      // Spinning (not yet implemented)
      { path: 'spinning/dashboard', element: <SpinningPage /> },
      { path: 'spinning/unloads', element: <SpinningPage /> },
      { path: 'spinning/progress', element: <SpinningPage /> },
      { path: 'spinning/quality', element: <SpinningPage /> },
      { path: 'spinning/waste', element: <SpinningPage /> },
      { path: 'spinning/skeins', element: <SpinningPage /> },
      { path: 'spinning/consolidated', element: <SpinningPage /> },

      // Lots (not yet implemented)
      { path: 'lots/queue', element: <LotsPage /> },
      { path: 'lots/detail', element: <LotsPage /> },

      // Reports (not yet implemented)
      { path: 'reports/daily', element: <ReportsPage /> },
      { path: 'reports/production', element: <ReportsPage /> },
      { path: 'reports/traceability', element: <ReportsPage /> },

      // Admin
      { path: 'admin/master-data', element: <AdminPage /> },
      { path: 'profile', element: <ProfilePage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])

export function AppRouter() {
  return <RouterProvider router={router} />
}
