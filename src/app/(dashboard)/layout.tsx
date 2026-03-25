"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"

const navItems = [
  { href: "/map", label: "Mapa", icon: "🗺" },
  { href: "/analysis", label: "Análise", icon: "📊" },
  { href: "/data", label: "Dados", icon: "📁" },
]

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <aside className="w-16 shrink-0 border-r bg-muted/40 flex flex-col items-center py-4 gap-2">
        <div className="text-lg font-bold mb-4">M</div>
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex flex-col items-center gap-0.5 rounded-lg p-2 text-xs transition-colors hover:bg-accent",
              pathname === item.href && "bg-accent text-accent-foreground"
            )}
          >
            <span className="text-lg">{item.icon}</span>
            <span>{item.label}</span>
          </Link>
        ))}
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-hidden">{children}</main>
    </div>
  )
}
