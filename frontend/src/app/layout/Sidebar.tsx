import { ScrollArea, Stack } from "@mantine/core";
import { navData } from '../navigation-data'
import { SidebarLinksGroup } from "./SidebarLinksGroup";
import { ACCESS_CATALOG, useAccess } from '@/features/access-control'
import { canDisplayNavigationItem, deriveNavigation } from './navigation-state'

interface SidebarProps {
    /** Se llama después de navegar — cierra el sidebar en mobile */
    onNavigate?: () => void;
}

export function Sidebar({ onNavigate }: SidebarProps) {
    const { snapshot } = useAccess()
    const visibleNavData = deriveNavigation(navData, (item) => canDisplayNavigationItem(item, (path) => Boolean(snapshot?.allows(ACCESS_CATALOG[path]))));

    return (
        <Stack gap={0} style={{ height: "100%" }} pt="xs">
            <ScrollArea style={{ flex: 1 }}>
                <Stack gap={2} px="xs">
                    {visibleNavData.map((section) => (
                        <SidebarLinksGroup
                            key={section.label}
                            icon={section.icon}
                            label={section.label}
                            links={section.children}
                            onNavigate={onNavigate}
                        />
                    ))}
                </Stack>
            </ScrollArea>
        </Stack>
    );
}
