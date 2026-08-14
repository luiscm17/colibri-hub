import { Button, List, Text } from '@mantine/core'
import { useId, useState } from 'react'

export type AffectedUser = { user_id: string; user_code: string; display_name: string }

export function ImpactPreview({ affectedUserCount, affectedUsers }: { affectedUserCount: number; affectedUsers: AffectedUser[] }) {
  const [expanded, setExpanded] = useState(false)
  const listId = useId()
  const initialUsers = affectedUsers.slice(0, 6)
  const additionalUsers = affectedUsers.slice(6)
  const visibleUsers = expanded ? affectedUsers : initialUsers

  return <>
    <Text>Users affected by this proposed change: {affectedUserCount}.</Text>
    <List id={listId} size="sm" withPadding>
      {visibleUsers.map((user) => <List.Item key={user.user_id}>{user.display_name} ({user.user_code})</List.Item>)}
    </List>
    {additionalUsers.length > 0 ? <Button variant="subtle" size="compact-sm" aria-expanded={expanded} aria-controls={listId} onClick={() => setExpanded((value) => !value)}>{expanded ? 'Show fewer affected users' : `Show ${additionalUsers.length} additional affected user${additionalUsers.length === 1 ? '' : 's'}`}</Button> : null}
  </>
}
