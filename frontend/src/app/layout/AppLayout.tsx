import { useState, useEffect, Suspense } from "react";
import {
    Box,
    Flex,
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
import { useDisclosure, useMediaQuery } from "@mantine/hooks";
import { IconSun, IconMoon, IconChevronDown, IconMenu2 } from "@tabler/icons-react";
import { Outlet, useLocation, useNavigate } from "react-router";
import { TopBar } from "./TopBar";
import { Sidebar } from "./Sidebar";
import { useAuth } from "@/features/auth";
import { SessionExpiredDialog } from "@/features/auth/components/SessionExpiredDialog";
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
    const isMobile = useMediaQuery("(max-width: 47.99em)");
    const [mobileNavOpen, { open: openMobileNav, close: closeMobileNav }] = useDisclosure(false);
    const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
        return localStorage.getItem("sidebarCollapsed") === "true";
    });

    useEffect(() => {
        localStorage.setItem("sidebarCollapsed", String(sidebarCollapsed));
    }, [sidebarCollapsed]);

    const { setColorScheme } = useMantineColorScheme();
    const computedScheme = useComputedColorScheme("light");
    const isDark = computedScheme === "dark";
    const { account, logout } = useAuth();

    const handleNavClick = () => {
        closeMobileNav();
    };

    const handleToggleSidebar = () => {
        if (isMobile) {
            openMobileNav();
        } else {
            setSidebarCollapsed((prev) => {
                return !prev;
            });
        }
    };

    return (
        <>
        <SessionExpiredDialog />
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
                                                {account?.initials ?? "?"}
                                            </Avatar>
                                        </Indicator>
                                        <Text size="sm" visibleFrom="sm">
                                            {account?.displayName ?? "User"}
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
                                            void logout();
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
                <Sidebar onNavigate={handleNavClick} />
            </Drawer>

            {/* Desktop: Sidebar + main content */}
            <Flex className={classes.body}>
                {!isMobile && (
                    <Box
                        component="aside"
                        className={`${classes.sidebar} ${sidebarCollapsed ? classes.sidebarCollapsed : ""}`}
                        bg={isDark ? "dark.7" : "gray.0"}
                    >
                        <Sidebar onNavigate={handleNavClick} />
                    </Box>
                )}
                <Box component="main" className={classes.main} p="md">
                    <ErrorBoundary>
                        <AppBreadcrumbs />
                        <div className="page-enter" key={location.pathname}>
                            <Suspense fallback={<PageSkeleton />}>
                                <Outlet />
                            </Suspense>
                        </div>
                    </ErrorBoundary>
                </Box>
            </Flex>
        </Flex>
        </>
    );
}
