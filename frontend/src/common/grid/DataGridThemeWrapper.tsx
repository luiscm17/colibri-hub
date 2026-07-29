import { Box, type BoxProps } from '@mantine/core'
import type { ReactNode } from 'react'
import classes from './DataGridThemeWrapper.module.css'

interface DataGridThemeWrapperProps extends BoxProps {
  children: ReactNode
}

export function DataGridThemeWrapper({ children, className, ...others }: DataGridThemeWrapperProps) {
  return (
    <Box className={[classes.root, className].filter(Boolean).join(' ')} {...others}>
      {children}
    </Box>
  )
}
