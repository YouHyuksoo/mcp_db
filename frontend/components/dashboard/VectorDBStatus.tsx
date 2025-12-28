"use client"

import { VectorDBStats } from "@/lib/types"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Database, Lightbulb, BookOpen } from "lucide-react"

interface VectorDBStatusProps {
  stats: VectorDBStats | null
  loading?: boolean
}

export function VectorDBStatus({ stats, loading }: VectorDBStatusProps) {
  if (loading || !stats) {
    return (
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">메타데이터</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-8 w-20" />
            <Skeleton className="h-3 w-32 mt-2" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">SQL 패턴</CardTitle>
            <Lightbulb className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-8 w-20" />
            <Skeleton className="h-3 w-32 mt-2" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">비즈니스 규칙</CardTitle>
            <BookOpen className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-8 w-20" />
            <Skeleton className="h-3 w-32 mt-2" />
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="grid gap-4 md:grid-cols-3">
      <Card className="transition-all hover:shadow-lg hover:scale-105">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">메타데이터</CardTitle>
          <Database className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.metadata_count.toLocaleString()}</div>
          <p className="text-xs text-muted-foreground">테이블 정보</p>
        </CardContent>
      </Card>
      <Card className="transition-all hover:shadow-lg hover:scale-105">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">SQL 패턴</CardTitle>
          <Lightbulb className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.patterns_count.toLocaleString()}</div>
          <p className="text-xs text-muted-foreground">학습된 쿼리 패턴</p>
        </CardContent>
      </Card>
      <Card className="transition-all hover:shadow-lg hover:scale-105">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">비즈니스 규칙</CardTitle>
          <BookOpen className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.business_rules_count.toLocaleString()}</div>
          <p className="text-xs text-muted-foreground">추출된 규칙</p>
        </CardContent>
      </Card>
    </div>
  )
}
