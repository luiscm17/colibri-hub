import { useState, type ReactNode } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  Box,
  Collapse,
  Group,
  UnstyledButton,
} from '@mantine/core'
import { IconChevronRight } from '@tabler/icons-react'
import { type NavItem } from '../navigation-data'
import classes from '@/styles/components/SidebarLinksGroup.module.css'

interface LinksGroupProps {
  icon?: ReactNode
  label: string
  links?: NavItem[]
  /** Se llama después de navegar — cierra el sidebar en mobile */
  onNavigate?: () => void
}

export function SidebarLinksGroup({ icon, label, links, onNavigate }: LinksGroupProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const hasLinks = Array.isArray(links) && links.length > 0

  // Auto-open if any child matches the current route
  const hasActiveChild =
    hasLinks && links!.some((child) => child.path === location.pathname)

  const [opened, setOpened] = useState(hasActiveChild)

  const controlClassName = [
    classes.control,
    opened ? classes.controlExpanded : '',
    hasActiveChild && !opened ? classes.controlHasActive : '',
  ].filter(Boolean).join(' ')

  const items = (links ?? []).map((child) => {
    const isActive = location.pathname === child.path
    return (
      <UnstyledButton
        key={child.path}
        className={classes.link}
        data-active={isActive || undefined}
        onClick={() => {
          if (child.path) {
            navigate(child.path)
            onNavigate?.()
          }
        }}
      >
        {child.icon && (
          <Box component="span" className={classes.linkIcon}>
            {child.icon}
          </Box>
        )}
        <span>{child.label}</span>
      </UnstyledButton>
    )
  })

  return (
    <Box>
      <UnstyledButton
        onClick={() => setOpened((o) => !o)}
        className={controlClassName}
      >
        <Group justify="space-between" gap={0}>
          <Group gap="sm" wrap="nowrap">
            {icon && <Box component="span">{icon}</Box>}
            <Box component="span">{label}</Box>
          </Group>
          {hasLinks && (
            <IconChevronRight
              className={classes.chevron}
              stroke={1.5}
              size={14}
              style={{ transform: opened ? 'rotate(90deg)' : 'none' }}
            />
          )}
        </Group>
      </UnstyledButton>
      {hasLinks && <Collapse expanded={opened}>{items}</Collapse>}
    </Box>
  )
}
