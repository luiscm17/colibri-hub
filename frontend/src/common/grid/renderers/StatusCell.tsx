import { Badge } from '@mantine/core'

interface StatusCellProps {
  status: string
  colorMap: Record<string, string>
  iconMap?: Record<string, React.ComponentType<{ size?: number }>>
}

export function StatusCell({ status, colorMap, iconMap }: StatusCellProps) {
  const color = colorMap[status]
  const Icon = iconMap?.[status]

  return (
    <Badge
      color={color}
      leftSection={Icon ? <Icon size={14} /> : undefined}
    >
      {status}
    </Badge>
  )
}
