import { createBrowserRouter, Navigate, RouterProvider } from 'react-router'
import { AppLayout } from '@/app/layout/AppLayout'
import { AuthenticationBoundary } from '@/features/auth/components/AuthenticationBoundary'
import { UnauthenticatedOnly } from '@/features/auth/components/UnauthenticatedOnly'
import { PasswordChangeOnly } from '@/features/auth/components/PasswordChangeOnly'
import { AuthenticatedOnly } from '@/features/auth/components/AuthenticatedOnly'
import { RouteErrorBoundary } from './RouteErrorBoundary'
import { ComingSoon } from '@/common/components/ComingSoon'
import { ACCESS_CATALOG } from '@/features/access-control'
import { ProtectedRoute } from './protected-route'
import {
  AdminPage,
  BaleManagementPage,
  LoginPage,
  MandatoryPasswordChangePage,
  LotsPage,
  NotFoundPage,
  ProfilePage,
  BaleReceptionPage,
  BaleStockPage,
  BaleDeliveryPage,
  SpinningPage,
} from './lazy-pages'

const router = createBrowserRouter([
  {
    path: '/login',
    element: (
      <UnauthenticatedOnly>
        <LoginPage />
      </UnauthenticatedOnly>
    ),
    errorElement: <RouteErrorBoundary />,
  },
  {
    path: '/password-change',
    element: (
      <PasswordChangeOnly>
        <MandatoryPasswordChangePage />
      </PasswordChangeOnly>
    ),
    errorElement: <RouteErrorBoundary />,
  },
  {
    path: '/',
    element: (
      <AuthenticationBoundary>
        <AuthenticatedOnly>
          <AppLayout />
        </AuthenticatedOnly>
      </AuthenticationBoundary>
    ),
    errorElement: <RouteErrorBoundary />,
    children: [
      { index: true, element: <Navigate to="/profile" replace /> },

      // Warehouse — Bale Management (implemented)
      { path: 'warehouse/bales', element: <ProtectedRoute requirement={ACCESS_CATALOG['/warehouse/bales']}><BaleManagementPage /></ProtectedRoute> },
      { path: 'warehouse/bales/reception', element: <ProtectedRoute requirement={ACCESS_CATALOG['/warehouse/bales/reception']}><BaleReceptionPage /></ProtectedRoute> },
      { path: 'warehouse/bales/stock', element: <ProtectedRoute requirement={ACCESS_CATALOG['/warehouse/bales/stock']}><BaleStockPage /></ProtectedRoute> },
      { path: 'warehouse/bales/delivery', element: <ProtectedRoute requirement={ACCESS_CATALOG['/warehouse/bales/delivery']}><BaleDeliveryPage /></ProtectedRoute> },

      // Warehouse — Other capabilities (not yet implemented)
      { path: 'warehouse/identity', element: <ProtectedRoute requirement={ACCESS_CATALOG['/warehouse/identity']}><ComingSoon feature="Identidad de producción" /></ProtectedRoute> },
      { path: 'warehouse/finished-product', element: <ProtectedRoute requirement={ACCESS_CATALOG['/warehouse/finished-product']}><ComingSoon feature="Producto terminado" /></ProtectedRoute> },
      { path: 'warehouse/supplies', element: <ProtectedRoute requirement={ACCESS_CATALOG['/warehouse/supplies']}><ComingSoon feature="Insumos" /></ProtectedRoute> },

      // Spinning (not yet implemented)
      { path: 'spinning/preparation', element: <ProtectedRoute requirement={ACCESS_CATALOG['/spinning/preparation']}><SpinningPage /></ProtectedRoute> },
      { path: 'spinning/ring-spinning', element: <ProtectedRoute requirement={ACCESS_CATALOG['/spinning/ring-spinning']}><SpinningPage /></ProtectedRoute> },
      { path: 'spinning/bobbin-winding', element: <ProtectedRoute requirement={ACCESS_CATALOG['/spinning/bobbin-winding']}><SpinningPage /></ProtectedRoute> },
      { path: 'spinning/twisting', element: <ProtectedRoute requirement={ACCESS_CATALOG['/spinning/twisting']}><SpinningPage /></ProtectedRoute> },
      { path: 'spinning/skeining', element: <ProtectedRoute requirement={ACCESS_CATALOG['/spinning/skeining']}><SpinningPage /></ProtectedRoute> },
      { path: 'spinning/quality', element: <ProtectedRoute requirement={ACCESS_CATALOG['/spinning/quality']}><SpinningPage /></ProtectedRoute> },
      { path: 'spinning/waste', element: <ProtectedRoute requirement={ACCESS_CATALOG['/spinning/waste']}><SpinningPage /></ProtectedRoute> },
      { path: 'spinning/consolidated', element: <ProtectedRoute requirement={ACCESS_CATALOG['/spinning/consolidated']}><SpinningPage /></ProtectedRoute> },

      // Lots (not yet implemented)
      { path: 'lots', element: <ProtectedRoute requirement={ACCESS_CATALOG['/lots']}><LotsPage /></ProtectedRoute> },
      { path: 'lots/queue', element: <ProtectedRoute requirement={ACCESS_CATALOG['/lots/queue']}><LotsPage /></ProtectedRoute> },
      { path: 'lots/detail', element: <ProtectedRoute requirement={ACCESS_CATALOG['/lots/detail']}><LotsPage /></ProtectedRoute> },
      { path: 'lots/inventory', element: <ProtectedRoute requirement={ACCESS_CATALOG['/lots/inventory']}><LotsPage /></ProtectedRoute> },
      { path: 'lots/dyeing', element: <ProtectedRoute requirement={ACCESS_CATALOG['/lots/dyeing']}><LotsPage /></ProtectedRoute> },
      { path: 'lots/drying', element: <ProtectedRoute requirement={ACCESS_CATALOG['/lots/drying']}><LotsPage /></ProtectedRoute> },
      { path: 'lots/winding', element: <ProtectedRoute requirement={ACCESS_CATALOG['/lots/winding']}><LotsPage /></ProtectedRoute> },
      { path: 'lots/bagging', element: <ProtectedRoute requirement={ACCESS_CATALOG['/lots/bagging']}><LotsPage /></ProtectedRoute> },
      { path: 'lots/quality', element: <ProtectedRoute requirement={ACCESS_CATALOG['/lots/quality']}><LotsPage /></ProtectedRoute> },

      // Admin
      { path: 'access/:destination', element: <ProtectedRoute requirement={ACCESS_CATALOG['/access/users']}><AdminPage /></ProtectedRoute> },
      { path: 'profile', element: <ProfilePage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])

export function AppRouter() {
  return <RouterProvider router={router} />
}
