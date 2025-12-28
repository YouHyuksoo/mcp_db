"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Database, Table as TableIcon, FileText, Loader2, AlertCircle } from "lucide-react"
import { Header } from "@/components/layout/Header"
import api from "@/lib/api"

interface MetadataItem {
  table_name: string
  table_comment: string
  column_count: number
  last_updated: string
}

export default function PatternsPage() {
  const [metadata, setMetadata] = useState<MetadataItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [totalCount, setTotalCount] = useState(0)

  useEffect(() => {
    loadMetadata()
  }, [])

  const loadMetadata = async () => {
    try {
      setIsLoading(true)
      setError(null)

      const response = await api.metadata.list()
      setMetadata(response.metadata)
      setTotalCount(response.total_count)
    } catch (err: any) {
      console.error("Failed to load metadata:", err)
      setError(err.message || "메타데이터를 불러오는데 실패했습니다.")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <div className="container mx-auto max-w-7xl py-6 space-y-6 px-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">메타데이터 조회</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Vector DB에 저장된 테이블 메타데이터를 확인하세요
          </p>
        </div>

        {/* 통계 카드 */}
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">총 테이블 수</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{totalCount}</div>
            </CardContent>
          </Card>
        </div>

        {/* 메타데이터 테이블 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TableIcon className="h-5 w-5" />
              테이블 메타데이터
            </CardTitle>
            <CardDescription>업로드된 테이블 정보</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                <span className="ml-2 text-muted-foreground">메타데이터 로딩 중...</span>
              </div>
            ) : error ? (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            ) : metadata.length === 0 ? (
              <div className="border-2 border-dashed border-border rounded-lg p-12 text-center">
                <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground mb-2">저장된 메타데이터가 없습니다</p>
                <p className="text-sm text-muted-foreground">
                  Upload 페이지에서 CSV 파일을 업로드하여 메타데이터를 생성하세요
                </p>
              </div>
            ) : (
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>테이블명</TableHead>
                      <TableHead>설명</TableHead>
                      <TableHead className="text-center">컬럼 수</TableHead>
                      <TableHead className="text-right">마지막 업데이트</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {metadata.map((item, index) => (
                      <TableRow key={index}>
                        <TableCell className="font-mono font-medium">
                          {item.table_name}
                        </TableCell>
                        <TableCell className="max-w-md truncate">
                          {item.table_comment || <span className="text-muted-foreground italic">설명 없음</span>}
                        </TableCell>
                        <TableCell className="text-center">
                          <Badge variant="secondary">{item.column_count}</Badge>
                        </TableCell>
                        <TableCell className="text-right text-sm text-muted-foreground">
                          {new Date(item.last_updated).toLocaleString('ko-KR')}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
