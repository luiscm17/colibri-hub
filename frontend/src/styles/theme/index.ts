import { createTheme } from '@mantine/core'
import { brandCyan } from './colors'

export const theme = createTheme({
  primaryColor: 'brand-cyan',
  primaryShade: { light: 5, dark: 4 },

  colors: {
    'brand-cyan': brandCyan,
  },

  fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
  fontFamilyMonospace: "ui-monospace, 'SF Mono', Consolas, monospace",

  fontSizes: {
    xs: '12px',
    sm: '14px',
    md: '16px',
    lg: '18px',
    xl: '24px',
  },

  lineHeights: {
    xs: '1.5',
    sm: '1.5',
    md: '1.5',
    lg: '1.4',
    xl: '1.3',
  },

  headings: {
    sizes: {
      h1: { fontSize: '24px', fontWeight: '600', lineHeight: '1.3' },
      h2: { fontSize: '18px', fontWeight: '600', lineHeight: '1.4' },
    },
  },

  defaultRadius: 'md',

  spacing: {
    xs: '8px',
    sm: '12px',
    md: '16px',
    lg: '24px',
    xl: '32px',
  },

  shadows: {
    sm: '0 1px 2px rgba(0,0,0,0.06)',
    md: '0 4px 6px rgba(0,0,0,0.07)',
    lg: '0 10px 15px rgba(0,0,0,0.1)',
  },

  components: {
    Button: {
      defaultProps: {
        radius: 'md',
      },
    },
    ActionIcon: {
      defaultProps: {
        radius: 'md',
      },
    },
    TextInput: {
      defaultProps: {
        radius: 'md',
        size: 'sm',
      },
    },
    Select: {
      defaultProps: {
        radius: 'md',
        size: 'sm',
      },
    },
    NumberInput: {
      defaultProps: {
        radius: 'md',
        size: 'sm',
      },
    },
    Textarea: {
      defaultProps: {
        radius: 'md',
        size: 'sm',
      },
    },
    PasswordInput: {
      defaultProps: {
        radius: 'md',
        size: 'sm',
      },
    },
    Badge: {
      defaultProps: {
        variant: 'light',
      },
    },
    Tooltip: {
      defaultProps: {
        openDelay: 300,
      },
    },
    Modal: {
      defaultProps: {
        radius: 'md',
      },
    },
    Drawer: {
      defaultProps: {
        size: 300,
      },
    },
    Paper: {
      defaultProps: {
        withBorder: true,
        radius: 'md',
      },
    },
    Alert: {
      defaultProps: {},
    },
    Notification: {
      defaultProps: {},
    },
  },
})
