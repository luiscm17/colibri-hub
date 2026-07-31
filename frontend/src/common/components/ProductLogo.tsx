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

    const markColor = isDark
        ? "var(--mantine-color-brand-cyan-3)"
        : "var(--mantine-color-brand-cyan-6)";
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
            <svg
                aria-hidden="true"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 32 32"
                width={height}
                height={height}
                fill="none"
            >
                {/* Hummingbird/C-shape geometric motif */}
                {/* Body arc */}
                <path
                    d="M16 4C9.373 4 4 9.373 4 16c0 4.418 2.393 8.278 5.95 10.355a1.5 1.5 0 0 0 1.5-2.598A9 9 0 1 1 25 16a1.5 1.5 0 0 0 3 0C28 9.373 22.627 4 16 4Z"
                    fill={markColor}
                />
                {/* Wing accent */}
                <path
                    d="M20 14a4 4 0 0 0-4-4 1.5 1.5 0 0 0 0 3 1 1 0 0 1 1 1 1.5 1.5 0 0 0 3 0Z"
                    fill={markColor}
                    opacity={0.7}
                />
                {/* Beak / forward point */}
                <path
                    d="M26 20l3-2-3-2v4Z"
                    fill={markColor}
                />
            </svg>

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
