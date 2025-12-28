"use client"

import { UploadedFile } from "@/lib/types"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Upload } from "lucide-react"

interface UploadHistoryProps {
  uploads: UploadedFile[]
  loading?: boolean
}

export function UploadHistory({ uploads, loading }: UploadHistoryProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            <CardTitle>업로드 기록</CardTitle>
          </div>
          <CardDescription>CSV 및 PowerBuilder 파일 업로드 기록</CardDescription>
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

  if (uploads.length === 0) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            <CardTitle>업로드 기록</CardTitle>
          </div>
          <CardDescription>CSV 및 PowerBuilder 파일 업로드 기록</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-8">
            업로드 기록이 없습니다.
          </p>
        </CardContent>
      </Card>
    )
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return "N/A"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + " " + sizes[i]
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Upload className="h-5 w-5" />
          <CardTitle>업로드 기록</CardTitle>
        </div>
        <CardDescription>총 {uploads.length}개 파일</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>파일명</TableHead>
              <TableHead>타입</TableHead>
              <TableHead className="text-right">파일 크기</TableHead>
              <TableHead className="text-right">추출된 규칙</TableHead>
              <TableHead>상태</TableHead>
              <TableHead>업로드 시간</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {uploads.map((upload, index) => (
              <TableRow key={`${upload.file_name}-${index}`}>
                <TableCell className="font-medium max-w-xs truncate">
                  {upload.file_name}
                </TableCell>
                <TableCell>
                  <Badge variant="outline">{upload.file_type}</Badge>
                </TableCell>
                <TableCell className="text-right text-sm text-muted-foreground">
                  {formatFileSize(upload.file_size)}
                </TableCell>
                <TableCell className="text-right">
                  {upload.rules_extracted !== null ? upload.rules_extracted : "-"}
                </TableCell>
                <TableCell>
                  <Badge
                    variant={
                      upload.processing_status === "completed"
                        ? "success"
                        : upload.processing_status === "processing"
                        ? "warning"
                        : upload.processing_status === "failed"
                        ? "destructive"
                        : "outline"
                    }
                  >
                    {upload.processing_status}
                  </Badge>
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {upload.upload_time ? new Date(upload.upload_time).toLocaleString("ko-KR") : "N/A"}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
