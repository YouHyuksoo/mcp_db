"use client"

import { useState } from "react"
import { DatabaseInfo } from "@/lib/types"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { FormField } from "@/components/ui/form-field"
import { Database, RefreshCw } from "lucide-react"
import api from "@/lib/api"

interface DatabaseListProps {
  databases: DatabaseInfo[]
  loading?: boolean
  onRefresh?: () => void
}

export function DatabaseList({ databases, loading, onRefresh }: DatabaseListProps) {
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [metadataDir, setMetadataDir] = useState("")
  const [databaseSid, setDatabaseSid] = useState("")
  const [schemaName, setSchemaName] = useState("")
  const [message, setMessage] = useState("")

  const handleReprocess = async () => {
    if (!metadataDir || !databaseSid || !schemaName) {
      setMessage("모든 필드를 입력해주세요.")
      return
    }

    setIsProcessing(true)
    setMessage("")

    try {
      const result = await api.metadata.migrate({
        metadata_dir: metadataDir,
        database_sid: databaseSid,
        schema_name: schemaName,
      })

      if (result.success) {
        setMessage(`✓ 성공: ${result.tables_migrated}개 테이블이 Vector DB에 학습되었습니다.`)
        setTimeout(() => {
          setIsDialogOpen(false)
          setMessage("")
          setMetadataDir("")
          setDatabaseSid("")
          setSchemaName("")
          if (onRefresh) onRefresh()
        }, 2000)
      } else {
        setMessage(`✗ 실패: ${result.error || "알 수 없는 오류"}`)
      }
    } catch (error) {
      setMessage(`✗ 오류: ${error}`)
    } finally {
      setIsProcessing(false)
    }
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            <CardTitle>등록된 데이터베이스</CardTitle>
          </div>
          <CardDescription>메타데이터가 등록된 데이터베이스 목록</CardDescription>
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

  const renderReprocessButton = () => (
    <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
      <DialogTrigger asChild>
        <Button variant="default" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          메타데이터 재학습
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>메타데이터 재학습</DialogTitle>
          <DialogDescription>
            기존 JSON 메타데이터 파일을 Vector DB로 다시 학습합니다.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <FormField
            id="metadata_dir"
            label="메타데이터 디렉토리"
            helpText="CSV 파일을 업로드한 후 생성된 JSON 메타데이터 파일들이 저장된 디렉토리 경로입니다. 일반적으로 ../metadata 또는 절대 경로를 입력합니다. 이 디렉토리에는 테이블별로 {테이블명}.json 형식의 파일들이 존재해야 합니다."
            placeholder="예: ../metadata"
            value={metadataDir}
            onChange={(e) => setMetadataDir(e.target.value)}
          />
          <FormField
            id="database_sid"
            label="Database SID"
            helpText="Oracle 데이터베이스의 시스템 식별자(System Identifier)입니다. tnsnames.ora 파일에서 확인할 수 있으며, 데이터베이스를 고유하게 식별하는 이름입니다. 예: ORCL, DEVDB, PRODDB 등"
            placeholder="예: ORCL"
            value={databaseSid}
            onChange={(e) => setDatabaseSid(e.target.value)}
          />
          <FormField
            id="schema_name"
            label="Schema Name"
            helpText="Oracle 스키마 이름(테이블의 소유자)입니다. 메타데이터를 수집한 스키마와 동일한 이름을 입력해야 합니다. 일반적으로 대문자로 입력합니다. 예: HR, SCOTT, APP_OWNER 등"
            placeholder="예: HR"
            value={schemaName}
            onChange={(e) => setSchemaName(e.target.value)}
          />
          {message && (
            <div className={`text-sm p-2 rounded ${message.startsWith("✓") ? "bg-green-500/10 text-green-500" : "bg-red-500/10 text-red-500"}`}>
              {message}
            </div>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setIsDialogOpen(false)} disabled={isProcessing}>
            취소
          </Button>
          <Button variant="default" onClick={handleReprocess} disabled={isProcessing}>
            {isProcessing ? "처리 중..." : "재학습 시작"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )

  if (databases.length === 0) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              <CardTitle>등록된 데이터베이스</CardTitle>
            </div>
            {renderReprocessButton()}
          </div>
          <CardDescription>메타데이터가 등록된 데이터베이스 목록</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-8">
            등록된 데이터베이스가 없습니다.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            <CardTitle>등록된 데이터베이스</CardTitle>
          </div>
          {renderReprocessButton()}
        </div>
        <CardDescription>총 {databases.length}개의 데이터베이스</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Database SID</TableHead>
              <TableHead>Schema</TableHead>
              <TableHead className="text-right">테이블 수</TableHead>
              <TableHead>마지막 업데이트</TableHead>
              <TableHead>상태</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {databases.map((db) => (
              <TableRow key={`${db.database_sid}-${db.schema_name}`}>
                <TableCell className="font-medium">{db.database_sid}</TableCell>
                <TableCell>{db.schema_name}</TableCell>
                <TableCell className="text-right">{db.table_count}</TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {db.last_updated ? new Date(db.last_updated).toLocaleString("ko-KR") : "N/A"}
                </TableCell>
                <TableCell>
                  <Badge variant={db.connection_status === "active" ? "success" : "outline"}>
                    {db.connection_status}
                  </Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
