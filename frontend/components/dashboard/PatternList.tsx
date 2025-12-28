"use client"

import { PatternSummary } from "@/lib/types"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Lightbulb } from "lucide-react"

interface PatternListProps {
  patterns: PatternSummary[]
  loading?: boolean
}

export function PatternList({ patterns, loading }: PatternListProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Lightbulb className="h-5 w-5" />
            <CardTitle>학습된 SQL 패턴</CardTitle>
          </div>
          <CardDescription>최근 학습된 SQL 쿼리 패턴</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        </CardContent>
      </Card>
    )
  }

  if (patterns.length === 0) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Lightbulb className="h-5 w-5" />
            <CardTitle>학습된 SQL 패턴</CardTitle>
          </div>
          <CardDescription>최근 학습된 SQL 쿼리 패턴</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-8">
            학습된 패턴이 없습니다.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Lightbulb className="h-5 w-5" />
          <CardTitle>학습된 SQL 패턴</CardTitle>
        </div>
        <CardDescription>최근 {patterns.length}개 패턴</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>질문</TableHead>
              <TableHead>Database</TableHead>
              <TableHead className="text-right">사용 횟수</TableHead>
              <TableHead className="text-right">성공률</TableHead>
              <TableHead>학습 시간</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {patterns.map((pattern) => (
              <TableRow key={pattern.pattern_id}>
                <TableCell className="max-w-xs truncate font-medium">
                  {pattern.question}
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {pattern.database_sid}.{pattern.schema_name}
                </TableCell>
                <TableCell className="text-right">{pattern.use_count}</TableCell>
                <TableCell className="text-right">
                  <Badge
                    variant={
                      pattern.success_rate >= 0.9
                        ? "success"
                        : pattern.success_rate >= 0.7
                        ? "warning"
                        : "destructive"
                    }
                  >
                    {(pattern.success_rate * 100).toFixed(0)}%
                  </Badge>
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {pattern.learned_at ? new Date(pattern.learned_at).toLocaleString("ko-KR") : "N/A"}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
