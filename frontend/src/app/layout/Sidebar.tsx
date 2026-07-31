import { ScrollArea, Stack } from "@mantine/core";
import { navData, type NavItem } from "../navigation-data";
import { SidebarLinksGroup } from "./SidebarLinksGroup";

interface SidebarProps {
    /** Optional RBAC filter callback */
    isResourceAllowed?: (resourceType: string) => boolean;
    /** Se llama después de navegar — cierra el sidebar en mobile */
    onNavigate?: () => void;
}

function filterNavItems(items: NavItem[], isAllowed: (rt: string) => boolean): NavItem[] {
    return items.flatMap((item) => {
        if (item.children) {
            const filteredChildren = item.children.filter(
                (c) => !c.resourceType || isAllowed(c.resourceType),
            );
            return filteredChildren.length === 0 ? [] : [{ ...item, children: filteredChildren }];
        }
        return item.resourceType && !isAllowed(item.resourceType) ? [] : [item];
    }) as NavItem[];
}

export function Sidebar({ isResourceAllowed, onNavigate }: SidebarProps) {
    const visibleNavData = isResourceAllowed ? filterNavItems(navData, isResourceAllowed) : navData;

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
