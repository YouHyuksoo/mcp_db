"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Database, Upload, Code, FileText, Home } from "lucide-react"
import { Button } from "@/components/ui/button"

export function Header() {
  const pathname = usePathname()

  const navItems = [
    { href: "/", label: "대시보드", icon: Home },
    { href: "/tnsnames", label: "TNSNames", icon: Database },
    { href: "/upload", label: "업로드", icon: Upload },
    { href: "/patterns", label: "패턴", icon: Code },
  ]

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center space-x-2">
          <Database className="h-6 w-6 text-primary" />
          <span className="font-bold text-xl">Oracle NL-SQL</span>
        </Link>

        {/* Navigation */}
        <nav className="flex items-center space-x-1">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.href

            return (
              <Link key={item.href} href={item.href}>
                <Button
                  variant={isActive ? "default" : "ghost"}
                  size="sm"
                  className="gap-2"
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Button>
              </Link>
            )
          })}
        </nav>

        {/* System Badge */}
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-xs text-muted-foreground">Backend 연결됨</span>
        </div>
      </div>
    </header>
  )
}
