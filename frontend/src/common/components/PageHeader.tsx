import { type ReactNode } from "react";
import { Group, Stack, Text, Title } from "@mantine/core";

interface PageHeaderProps {
    title: string;
    /** Optional description rendered below the title */
    description?: string;
    /** Slot derecho opcional para acciones (botones, filtros, etc.) */
    children?: ReactNode;
}

/**
 * Encabezado de página con título y slot de acciones.
 * El breadcrumb se renderiza globalmente desde AppLayout.
 */
export function PageHeader({ title, description, children }: PageHeaderProps) {
    return (
        <Group justify="space-between" wrap="nowrap" mb="md">
            <Stack gap={0}>
                <Title order={2}>{title}</Title>
                {description && (
                    <Text size="sm" c="dimmed">
                        {description}
                    </Text>
                )}
            </Stack>
            {children && (
                <Group gap="sm" wrap="nowrap">
                    {children}
                </Group>
            )}
        </Group>
    );
}
