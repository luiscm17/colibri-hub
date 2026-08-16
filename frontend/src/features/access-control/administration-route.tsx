import AdministrationPage, { AdministrationEditPage as EditPage } from './administration/AdministrationPage'
import { Navigate } from 'react-router'
import { collectionOnlyFamily } from './administration/operations'

export default function AccessAdministrationPage({ family }: { family?: string }) {
  return <AdministrationPage family={family} />
}

export function AccessAdministrationEditPage({ family }: { family?: string }) {
  return <EditPage family={family} />
}

export function AccessAdministrationCollectionRecovery({ family }: { family: string }) {
  return collectionOnlyFamily(family) ? <Navigate to={`/access/${family}`} replace /> : null
}
