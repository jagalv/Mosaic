import {
  Building2,
  FileText,
  LayoutDashboard,
  Settings,
  Star,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  soon?: boolean; // route exists but is a "coming soon" stub this session
}

// Starter universe (Milestone 1). Used by the dashboard / companies grid and
// the hero's example chips. Presentation-only — not a new data source.
export const STARTER_TICKERS = [
  "AAPL",
  "MSFT",
  "NVDA",
  "GOOGL",
  "AMZN",
  "META",
  "JPM",
  "KO",
  "XOM",
  "UNH",
] as const;

export const NAV: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Companies", href: "/companies", icon: Building2 },
  { label: "Watchlist", href: "/watchlist", icon: Star },
  { label: "Notes", href: "/notes", icon: FileText },
  { label: "Settings", href: "/settings", icon: Settings },
];
