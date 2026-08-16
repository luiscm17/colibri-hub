import { Button, Center, Loader, Stack, Text } from '@mantine/core'
import { useNavigate } from 'react-router'
import { ForbiddenState, OfflineState } from '@/common/components/PageState'
import { useAccess, type AccessRequirement } from '@/features/access-control'
import { resolveProtectedRoute } from './protected-route-state'

export function ProtectedRoute({ requirement, children }: { requirement: AccessRequirement; children: React.ReactNode }) {
  const { state, retry } = useAccess()
  const navigate = useNavigate()
  const outcome = resolveProtectedRoute(state, requirement)

  if (outcome === 'allowed') return <>{children}</>
  if (outcome === 'loading') return <Center h={300}><Loader aria-label="Loading access" /></Center>
  if (outcome === 'unavailable') return <OfflineState onRetry={() => void retry()} />
  if (outcome === 'blocked') {
    return <Center h={300}><Stack align="center"><Text>No active access profile is available.</Text><Button onClick={() => navigate('/profile')}>Go to profile</Button></Stack></Center>
  }
  return <ForbiddenState action={{ label: 'Go to profile', onClick: () => navigate('/profile') }} />
}
