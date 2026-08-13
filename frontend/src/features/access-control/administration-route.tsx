import AdministrationPage, { AdministrationEditPage as EditPage } from './administration/AdministrationPage'

export default function AccessAdministrationPage({ family }: { family?: string }) {
  return <AdministrationPage family={family} />
}

export function AccessAdministrationEditPage({ family }: { family?: string }) {
  return <EditPage family={family} />
}
