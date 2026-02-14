/**
 * Layout principal com sidebar/header.
 */

import { BarChart3, Home, LineChart, ListOrdered, Settings, Radar } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

const navItems = [
  { to: "/", icon: Home, label: "Visão Geral" },
  { to: "/ranking", icon: ListOrdered, label: "Ranking" },
  { to: "/explorer", icon: LineChart, label: "Explorer" },
  { to: "/admin", icon: Settings, label: "Admin" },
];

export function Layout() {
  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="hidden w-56 shrink-0 border-r border-gray-800 bg-gray-900/50 lg:block">
        <div className="flex h-14 items-center gap-2.5 border-b border-gray-800 px-5">
          <Radar className="h-6 w-6 text-brand-500" />
          <span className="text-base font-bold tracking-tight">Y</span>
        </div>
        <nav className="mt-4 space-y-1 px-3">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-brand-600/15 text-brand-400"
                    : "text-gray-400 hover:bg-gray-800 hover:text-gray-200"
                }`
              }
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Main content */}
      <div className="flex flex-1 flex-col">
        {/* Mobile header */}
        <header className="flex h-14 items-center justify-between border-b border-gray-800 px-4 lg:hidden">
          <div className="flex items-center gap-2">
            <Radar className="h-5 w-5 text-brand-500" />
            <span className="text-sm font-bold">Y</span>
          </div>
          <nav className="flex gap-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  `rounded-lg p-2 transition-colors ${
                    isActive ? "bg-brand-600/15 text-brand-400" : "text-gray-500"
                  }`
                }
              >
                <item.icon className="h-4 w-4" />
              </NavLink>
            ))}
          </nav>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
