import { createBrowserRouter, Navigate, RouterProvider } from 'react-router'
import { AppLayout } from '@/app/layout/AppLayout'
import { AuthenticationBoundary } from '@/features/auth/components/AuthenticationBoundary'
import { UnauthenticatedOnly } from '@/features/auth/components/UnauthenticatedOnly'
import { PasswordChangeOnly } from '@/features/auth/components/PasswordChangeOnly'
import { AuthenticatedOnly } from '@/features/auth/components/AuthenticatedOnly'
import { RouteErrorBoundary } from './RouteErrorBoundary'
import { ComingSoon } from '@/common/components/ComingSoon'
import { ACCESS_CATALOG } from '@/features/access-control'
import type { SpinningWorkspace } from '@/features/spinning'
import { ProtectedRoute } from './protected-route'
import { AccessAdministrationCollectionRecovery, AccessAdministrationEditPage, AccessAdministrationPage, AuthenticationAccountsPage, AuthenticationHistoryPage, BaleDeliveryPage, BaleManagementPage, BaleReceptionPage, BaleStockPage, LoginPage, LotsPage, MandatoryPasswordChangePage, NotFoundPage, ProfilePage, SpinningPage } from './lazy-pages'

const protectAdministration = (path: keyof typeof ACCESS_CATALOG, page: React.ReactNode) => <ProtectedRoute requirement={ACCESS_CATALOG[path]}>{page}</ProtectedRoute>
const spinningPage = (workspace: SpinningWorkspace) => <SpinningPage workspace={workspace} />

const router = createBrowserRouter([
  { path: '/login', element: <UnauthenticatedOnly><LoginPage /></UnauthenticatedOnly>, errorElement: <RouteErrorBoundary /> },
  { path: '/password-change', element: <PasswordChangeOnly><MandatoryPasswordChangePage /></PasswordChangeOnly>, errorElement: <RouteErrorBoundary /> },
  {
    path: '/',
    element: <AuthenticationBoundary><AuthenticatedOnly><AppLayout /></AuthenticatedOnly></AuthenticationBoundary>,
    errorElement: <RouteErrorBoundary />,
    children: [
      { index: true, element: <Navigate to="/profile" replace /> },
      { path: 'warehouse/bales', element: <ProtectedRoute requirement={ACCESS_CATALOG['/warehouse/bales']}><BaleManagementPage /></ProtectedRoute> },
      { path: 'warehouse/bales/reception', element: <ProtectedRoute requirement={ACCESS_CATALOG['/warehouse/bales/reception']}><BaleReceptionPage /></ProtectedRoute> },
      { path: 'warehouse/bales/stock', element: <ProtectedRoute requirement={ACCESS_CATALOG['/warehouse/bales/stock']}><BaleStockPage /></ProtectedRoute> },
      { path: 'warehouse/bales/delivery', element: <ProtectedRoute requirement={ACCESS_CATALOG['/warehouse/bales/delivery']}><BaleDeliveryPage /></ProtectedRoute> },
      { path: 'warehouse/identity', element: <ProtectedRoute requirement={ACCESS_CATALOG['/warehouse/identity']}><ComingSoon feature="Identidad de producción" /></ProtectedRoute> },
      { path: 'warehouse/finished-product', element: <ProtectedRoute requirement={ACCESS_CATALOG['/warehouse/finished-product']}><ComingSoon feature="Producto terminado" /></ProtectedRoute> },
      { path: 'warehouse/supplies', element: <ProtectedRoute requirement={ACCESS_CATALOG['/warehouse/supplies']}><ComingSoon feature="Insumos" /></ProtectedRoute> },
      { path: 'spinning/preparation', element: <ProtectedRoute requirement={ACCESS_CATALOG['/spinning/preparation']}>{spinningPage('preparation')}</ProtectedRoute> },
      { path: 'spinning/ring-spinning', element: <ProtectedRoute requirement={ACCESS_CATALOG['/spinning/ring-spinning']}>{spinningPage('ringSpinning')}</ProtectedRoute> },
      { path: 'spinning/bobbin-winding', element: <ProtectedRoute requirement={ACCESS_CATALOG['/spinning/bobbin-winding']}>{spinningPage('bobbinWinding')}</ProtectedRoute> },
      { path: 'spinning/twisting', element: <ProtectedRoute requirement={ACCESS_CATALOG['/spinning/twisting']}>{spinningPage('twisting')}</ProtectedRoute> },
      { path: 'spinning/skeining', element: <ProtectedRoute requirement={ACCESS_CATALOG['/spinning/skeining']}>{spinningPage('skeining')}</ProtectedRoute> },
      { path: 'spinning/quality', element: <ProtectedRoute requirement={ACCESS_CATALOG['/spinning/quality']}>{spinningPage('quality')}</ProtectedRoute> },
      { path: 'spinning/waste', element: <ProtectedRoute requirement={ACCESS_CATALOG['/spinning/waste']}>{spinningPage('waste')}</ProtectedRoute> },
      { path: 'spinning/corrections', element: spinningPage('corrections') },
      { path: 'spinning/consolidated', element: <ProtectedRoute requirement={ACCESS_CATALOG['/spinning/consolidated']}>{spinningPage('consolidated')}</ProtectedRoute> },
      ...['lots', 'lots/queue', 'lots/detail', 'lots/inventory', 'lots/dyeing', 'lots/drying', 'lots/winding', 'lots/bagging', 'lots/quality'].map((path) => ({ path, element: <ProtectedRoute requirement={ACCESS_CATALOG[`/${path}`]}><LotsPage /></ProtectedRoute> })),
      { path: 'auth/accounts', element: protectAdministration('/auth/accounts', <AuthenticationAccountsPage />) },
      { path: 'auth/accounts/:accountId', element: protectAdministration('/auth/accounts', <AuthenticationAccountsPage />) },
      { path: 'auth/history', element: protectAdministration('/auth/history', <AuthenticationHistoryPage />) },
      { path: 'access/users', element: protectAdministration('/access/users', <AccessAdministrationPage family="users" />) },
      { path: 'access/users/:subjectId', element: protectAdministration('/access/users', <AccessAdministrationPage family="users" />) },
      { path: 'access/roles', element: protectAdministration('/access/roles', <AccessAdministrationPage family="roles" />) },
      { path: 'access/roles/:subjectId', element: protectAdministration('/access/roles', <AccessAdministrationPage family="roles" />) },
      { path: 'access/roles/:subjectId/edit', element: protectAdministration('/access/roles', <AccessAdministrationEditPage family="roles" />) },
      { path: 'access/presets', element: protectAdministration('/access/presets', <AccessAdministrationPage family="presets" />) },
      { path: 'access/presets/:subjectId', element: protectAdministration('/access/presets', <AccessAdministrationPage family="presets" />) },
      { path: 'access/presets/:subjectId/edit', element: protectAdministration('/access/presets', <AccessAdministrationEditPage family="presets" />) },
      { path: 'access/scopes', element: protectAdministration('/access/scopes', <AccessAdministrationPage family="scopes" />) },
      { path: 'access/scopes/*', element: protectAdministration('/access/scopes', <AccessAdministrationCollectionRecovery family="scopes" />) },
      { path: 'access/history', element: protectAdministration('/access/history', <AccessAdministrationPage family="history" />) },
      { path: 'access/history/*', element: protectAdministration('/access/history', <AccessAdministrationCollectionRecovery family="history" />) },
      { path: 'profile', element: <ProfilePage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])

export function AppRouter() { return <RouterProvider router={router} /> }
