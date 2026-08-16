import { notifications } from '@mantine/notifications'

export const ACCESS_ADMINISTRATION_RECOVERY_MESSAGE = 'Your access changed. Review the current access and preview again.'

export function announceAccessAdministrationRecovery(): void {
  notifications.show({
    id: 'access-administration-recovery',
    title: 'Access changed',
    message: ACCESS_ADMINISTRATION_RECOVERY_MESSAGE,
    color: 'red',
    autoClose: false,
  })
}
