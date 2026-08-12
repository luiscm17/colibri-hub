import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { MantineProvider } from '@mantine/core'
import { Notifications } from '@mantine/notifications'
import { theme } from './styles/theme'
import { AuthProvider } from '@/features/auth'
import { AccessProvider } from '@/features/access-control'

import '@mantine/core/styles.css'
import '@mantine/notifications/styles.css'
import './styles/global.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <MantineProvider theme={theme} defaultColorScheme="auto">
      <Notifications position="top-right" zIndex={1000} />
       <AuthProvider>
         <AccessProvider>
           <App />
         </AccessProvider>
       </AuthProvider>
    </MantineProvider>
  </StrictMode>,
)
