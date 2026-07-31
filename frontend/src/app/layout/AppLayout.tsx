import { useEffect, useRef, useState, Suspense } from "react";
import {
    Box,
    Flex,
    Splitter,
    Group,
    Text,
    ActionIcon,
    Drawer,
    Tooltip,
    useMantineColorScheme,
    useComputedColorScheme,
    Indicator,
    Avatar,
    Menu,
} from "@mantine/core";
import { useDisclosure, useMediaQuery, type SplitterPaneSize, type UseSplitterReturnValue } from "@mantine/hooks";
import { IconSun, IconMoon, IconChevronDown, IconMenu2 } from "@tabler/icons-react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { TopBar } from "./TopBar";
import { Sidebar } from "./Sidebar";
import { useAuth } from "@/features/auth";
import { ErrorBoundary } from "@/common/components/ErrorBoundary";
import { AppBreadcrumbs } from "@/common/components/AppBreadcrumbs";
import { PageSkeleton } from "@/common/components/PageState";
import { ProductLogo } from "@/common/components/ProductLogo";
import { usePageTitle } from "@/common/hooks/usePageTitle";
import classes from "@/styles/components/AppLayout.module.css";

export function AppLayout() {
    usePageTitle();
    const navigate = useNavigate();
    const location = useLocation();
    const splitterRef = useRef<UseSplitterReturnValue>(null);
    const isMobile = useMediaQuery("(max-width: 47.99em)");
    const wasMobile = useRef<boolean | undefined>(undefined);
    const [mobileNavOpen, { open: openMobileNav, close: closeMobileNav }] = useDisclosure(false);
    const [sizes, setSizes] = useState<SplitterPaneSize[]>(() => {
        const saved = localStorage.getItem("sidebarSizes:v1");
        return saved ? (JSON.parse(saved) as SplitterPaneSize[]) : [20, 80];
    });

    const { setColorScheme } = useMantineColorScheme();
    const computedScheme = useComputedColorScheme("light");
    const isDark = computedScheme === "dark";
    const { user, logout, isResourceAllowed } = useAuth();

    // Mobile: Splitter sidebar pane stays collapsed (0px), Drawer overlays nav instead.
    // Desktop: Splitter sidebar pane works normally.
    // Uses collapse/expand directly (not toggleCollapse) to guarantee state regardless
    // of previous breakpoint or localStorage persistence.
    useEffect(() => {
        if (isMobile === undefined) return;
        if (wasMobile.current === undefined) {
            wasMobile.current = isMobile;
            if (isMobile) {
                splitterRef.current?.collapse(0);
            }
            return;
        }
        if (wasMobile.current === isMobile) return;
        wasMobile.current = isMobile;
        closeMobileNav();
        if (isMobile) {
            splitterRef.current?.collapse(0);
        } else {
            splitterRef.current?.expand(0);
        }
    }, [isMobile, closeMobileNav]);

    const handleNavClick = () => {
        closeMobileNav();
    };

    const handleToggleSidebar = () => {
        if (isMobile) {
            openMobileNav();
        } else {
            splitterRef.current?.toggleCollapse(0);
        }
    };

    const handleSizeChange = (newSizes: SplitterPaneSize[]) => {
        setSizes(newSizes);
        localStorage.setItem("sidebarSizes:v1", JSON.stringify(newSizes));
    };

    return (
        <Flex direction="column" h="100vh">
            <Box h={56} style={{ flexShrink: 0 }}>
                <TopBar
                    left={
                        <>
                            <ActionIcon
                                variant="subtle"
                                color="gray"
                                onClick={handleToggleSidebar}
                                aria-label="Toggle sidebar"
                                hiddenFrom="sm"
                            >
                                <IconMenu2 size={18} />
                            </ActionIcon>

                            <ProductLogo variant="compact" size="sm" />
                        </>
                    }
                    right={
                        <Group gap="sm" wrap="nowrap">
                            <Tooltip label={isDark ? "Modo claro" : "Modo oscuro"}>
                                <ActionIcon
                                    variant="subtle"
                                    color="gray"
                                    onClick={() => setColorScheme(isDark ? "light" : "dark")}
                                    aria-label="Toggle color scheme"
                                >
                                    {isDark ? <IconSun size={18} /> : <IconMoon size={18} />}
                                </ActionIcon>
                            </Tooltip>

                            <Menu shadow="md" width={180}>
                                <Menu.Target>
                                    <Group gap={6} className={classes.clickable} wrap="nowrap">
                                        <Indicator size={8} offset={2} color="green" withBorder>
                                            <Avatar size={28} color="brand-cyan" radius="xl">
                                                {user?.initials ?? "?"}
                                            </Avatar>
                                        </Indicator>
                                        <Text size="sm" visibleFrom="sm">
                                            {user?.name ?? "Usuario"}
                                        </Text>
                                        <IconChevronDown
                                            size={14}
                                            color="var(--mantine-color-dimmed)"
                                        />
                                    </Group>
                                </Menu.Target>

                                <Menu.Dropdown>
                                    <Menu.Label>Usuario</Menu.Label>
                                    <Menu.Item onClick={() => navigate("/profile")}>
                                        Perfil
                                    </Menu.Item>
                                    <Menu.Item
                                        color="red"
                                        onClick={() => {
                                            logout();
                                            navigate("/login", { replace: true });
                                        }}
                                    >
                                        Cerrar sesión
                                    </Menu.Item>
                                </Menu.Dropdown>
                            </Menu>
                        </Group>
                    }
                />
            </Box>

            {/* Mobile: Drawer overlay for navigation */}
            <Drawer
                opened={mobileNavOpen}
                onClose={closeMobileNav}
                size={280}
                padding={0}
                hiddenFrom="sm"
                withCloseButton={false}
                styles={{
                    body: { height: "100%", padding: 0 },
                }}
            >
                <Box px="md" pt="md" pb="xs">
                    <Group justify="space-between" align="center">
                        <ProductLogo variant="full" size="md" />
                        <ActionIcon
                            variant="subtle"
                            color="gray"
                            onClick={closeMobileNav}
                            aria-label="Cerrar navegación"
                        >
                            <IconMenu2 size={18} />
                        </ActionIcon>
                    </Group>
                </Box>
                <Sidebar isResourceAllowed={isResourceAllowed} onNavigate={handleNavClick} />
            </Drawer>

            <Splitter
                splitterRef={splitterRef}
                sizes={sizes}
                onSizeChange={handleSizeChange}
                className={classes.fill}
            >
                <Splitter.Pane
                    defaultSize={20}
                    min={15}
                    max={25}
                    collapsible
                    collapseThreshold={1}
                    bg={isDark ? "dark.7" : "gray.0"}
                >
                    {!isMobile && (
                        <Sidebar isResourceAllowed={isResourceAllowed} onNavigate={handleNavClick} />
                    )}
                </Splitter.Pane>
                <Splitter.Pane defaultSize={80} p="md" className={classes.scrollArea}>
                    <ErrorBoundary>
                        <AppBreadcrumbs />
                        <div className="page-enter" key={location.pathname}>
                            <Suspense fallback={<PageSkeleton />}>
                                <Outlet />
                            </Suspense>
                        </div>
                    </ErrorBoundary>
                </Splitter.Pane>
            </Splitter>
        </Flex>
    );
}
