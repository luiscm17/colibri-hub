import type { ReactNode } from 'react'
import {
  IconBuildingWarehouse, IconSpiral, IconStack3, IconSettings, IconPackage,
  IconHistory, IconTruckDelivery, IconPackageImport, IconBoxSeam, IconDashboard,
  IconSitemap, IconTrash, IconFileAnalytics, IconListDetails, IconRoute,
} from '@tabler/icons-react'
import { ACCESS_CATALOG } from '@/features/access-control'

export interface NavItem {
  label: string
  path?: keyof typeof ACCESS_CATALOG
  icon?: ReactNode
  children?: NavItem[]
}

export const navData: NavItem[] = [
  { label: 'Almacén', icon: <IconBuildingWarehouse size={18} />, children: [
    { label: 'Gestión de fardos', path: '/warehouse/bales', icon: <IconPackage size={16} /> },
    { label: 'Stock de fardos', path: '/warehouse/bales/stock', icon: <IconHistory size={16} /> },
    { label: 'Entrega de fardos', path: '/warehouse/bales/delivery', icon: <IconTruckDelivery size={16} /> },
    { label: 'Identidad de producción', path: '/warehouse/identity', icon: <IconPackageImport size={16} /> },
    { label: 'Producto terminado', path: '/warehouse/finished-product', icon: <IconPackageImport size={16} /> },
    { label: 'Insumos', path: '/warehouse/supplies', icon: <IconBoxSeam size={16} /> },
  ] },
  { label: 'Hilatura', icon: <IconSpiral size={18} />, children: [
    { label: 'Preparación', path: '/spinning/preparation', icon: <IconDashboard size={16} /> },
    { label: 'Ring spinning', path: '/spinning/ring-spinning', icon: <IconDashboard size={16} /> },
    { label: 'Bobinado', path: '/spinning/bobbin-winding', icon: <IconDashboard size={16} /> },
    { label: 'Retorcido', path: '/spinning/twisting', icon: <IconDashboard size={16} /> },
    { label: 'Madejas', path: '/spinning/skeining', icon: <IconDashboard size={16} /> },
    { label: 'Calidad de proceso', path: '/spinning/quality', icon: <IconSitemap size={16} /> },
    { label: 'Desperdicio', path: '/spinning/waste', icon: <IconTrash size={16} /> },
    { label: 'Consolidado', path: '/spinning/consolidated', icon: <IconFileAnalytics size={16} /> },
  ] },
  { label: 'Proceso por Lotes', icon: <IconStack3 size={18} />, children: [
    { label: 'Cola de lotes', path: '/lots/queue', icon: <IconListDetails size={16} /> },
    { label: 'Detalle del lote', path: '/lots/detail', icon: <IconRoute size={16} /> },
  ] },
  { label: 'Acceso', icon: <IconSettings size={18} />, children: [
    { label: 'Accounts', path: '/auth/accounts', icon: <IconSettings size={16} /> },
    { label: 'Authentication history', path: '/auth/history', icon: <IconHistory size={16} /> },
    { label: 'Usuarios', path: '/access/users', icon: <IconSettings size={16} /> },
    { label: 'Roles', path: '/access/roles', icon: <IconSettings size={16} /> },
    { label: 'Presets de rol', path: '/access/presets', icon: <IconSettings size={16} /> },
    { label: 'Scopes', path: '/access/scopes', icon: <IconSettings size={16} /> },
    { label: 'Historial de acceso', path: '/access/history', icon: <IconHistory size={16} /> },
  ] },
]
