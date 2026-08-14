import { Group, Text, useComputedColorScheme } from "@mantine/core";

interface ProductLogoProps {
    /** 'full' renders mark + text, 'compact' renders mark only */
    variant?: "full" | "compact";
    /** Controls rendered height: sm=20px, md=32px, lg=40px */
    size?: "sm" | "md" | "lg";
    /** Whether to show "Colibri Hub" text (ignored when variant='compact') */
    showName?: boolean;
}

const SIZE_MAP = { sm: 20, md: 32, lg: 40 } as const;

/**
 * Product identity mark for Colibri Hub.
 * Renders an inline SVG geometric hummingbird/C-shape motif with optional brand text.
 * Adapts colors to the active Mantine color scheme.
 */
export function ProductLogo({
    variant = "full",
    size = "md",
    showName = true,
}: ProductLogoProps) {
    const colorScheme = useComputedColorScheme("light");
    const isDark = colorScheme === "dark";

    const textColor = isDark
        ? "var(--mantine-color-gray-1)"
        : "var(--mantine-color-dark-7)";

    const height = SIZE_MAP[size];
    const showText = variant === "full" && showName;

    return (
        <Group
            gap={height > 24 ? "xs" : 4}
            wrap="nowrap"
            aria-label="Colibri Hub"
        >
            <img
                src="/favicon.svg"
                alt=""
                aria-hidden="true"
                width={height}
                height={height}
                style={{ display: 'block' }}
            />

            {showText && (
                <Text
                    size={height >= 32 ? "md" : "sm"}
                    fw={700}
                    c={textColor}
                    style={{ whiteSpace: "nowrap", lineHeight: 1 }}
                >
                    Colibri Hub
                </Text>
            )}
        </Group>
    );
}
