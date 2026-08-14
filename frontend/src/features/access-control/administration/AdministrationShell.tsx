import { Button, Group, Modal, Stack, Text } from '@mantine/core'
import { useEffect, useRef, useState, type ReactNode } from 'react'
import { useBlocker } from 'react-router'
import {
  recoverAdministrationRoute,
  resolveDiscard,
  type AdministrationRecoveryReason,
  type AdministrationRouteState,
} from './route-state'

type AdministrationShellProps = Readonly<{
  route: AdministrationRouteState
  origin: AdministrationRouteState | null
  navigate(route: AdministrationRouteState): void
  children: (state: {
    route: AdministrationRouteState
    setDraftState(name: string, dirty: boolean): void
    requestDeparture(route?: AdministrationRouteState): void
    recover(reason: AdministrationRecoveryReason): void
  }) => ReactNode
}>

export function AdministrationShell({ route, origin, navigate, children }: AdministrationShellProps) {
  const [draft, setDraft] = useState<{ name: string; dirty: boolean }>({ name: '', dirty: false })
  const [pendingRoute, setPendingRoute] = useState<AdministrationRouteState | null | undefined>(undefined)
  const cancelButton = useRef<HTMLButtonElement>(null)
  const [departureFocus, setDepartureFocus] = useState<HTMLElement | null>(null)
  const blocker = useBlocker(draft.dirty)

  const destination = (requested?: AdministrationRouteState) => requested ?? origin ?? recoverAdministrationRoute(route, 'invalid')
  const requestDeparture = (requested?: AdministrationRouteState) => {
    if (draft.dirty) {
      setDepartureFocus(document.activeElement instanceof HTMLElement ? document.activeElement : null)
      setPendingRoute(destination(requested))
    }
    else navigate(destination(requested))
  }
  const discardDraft = (confirmed: boolean) => {
    if (blocker.state === 'blocked') {
      if (confirmed) { setDraft({ name: '', dirty: false }); blocker.proceed() }
      else {
        blocker.reset()
        requestAnimationFrame(() => departureFocus?.focus())
      }
      return
    }
    const result = resolveDiscard(pendingRoute ?? destination(), confirmed)
    if (result.action === 'preserve') {
      setPendingRoute(undefined)
      requestAnimationFrame(() => departureFocus?.focus())
      return
    }
    setDraft({ name: '', dirty: false })
    setPendingRoute(undefined)
    requestAnimationFrame(() => navigate(result.route))
  }

  useEffect(() => {
    if (pendingRoute || blocker.state === 'blocked') cancelButton.current?.focus()
  }, [blocker.state, pendingRoute])

  return <>
    {children({
    route,
    setDraftState: (name, dirty) => setDraft({ name, dirty }),
    requestDeparture,
    recover: (reason) => navigate(recoverAdministrationRoute(route, reason)),
    })}
    <Modal opened={Boolean(pendingRoute) || blocker.state === 'blocked'} onClose={() => discardDraft(false)} title="Discard unsaved changes?" closeOnClickOutside={false} returnFocus={false} withCloseButton={false}>
      <Stack>
        <Text>You have unsaved changes in {draft.name || 'this draft'}. Discard them and leave this page?</Text>
        <Group justify="flex-end">
          <Button ref={cancelButton} variant="default" onClick={() => discardDraft(false)}>Keep editing</Button>
          <Button color="red" onClick={() => discardDraft(true)}>Discard changes</Button>
        </Group>
      </Stack>
    </Modal>
  </>
}
