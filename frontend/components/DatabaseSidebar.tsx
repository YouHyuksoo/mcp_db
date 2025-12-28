"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Database, Trash2, RefreshCw, CheckCircle2, XCircle } from "lucide-react"
import api from "@/lib/api"
import type { RegisteredDatabase } from "@/lib/types"

interface DatabaseSidebarProps {
  onSelectDatabase?: (database: RegisteredDatabase) => void
  selectedDatabaseSid?: string
  onRefresh?: () => void
}

export function DatabaseSidebar({ onSelectDatabase, selectedDatabaseSid, onRefresh }: DatabaseSidebarProps) {
  const [databases, setDatabases] = useState<RegisteredDatabase[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchDatabases = async () => {
    try {
      setLoading(true)
      const result = await api.databases.list()
      setDatabases(result.databases)
      setError(null)
    } catch (err) {
      console.error("Failed to fetch registered databases:", err)
      setError("DB 목록을 불러오는데 실패했습니다.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDatabases()
  }, [])

  const handleDelete = async (databaseSid: string, e: React.MouseEvent) => {
    e.stopPropagation()

    if (!confirm(`${databaseSid} 데이터베이스를 삭제하시겠습니까?`)) {
      return
    }

    try {
      await api.databases.delete(databaseSid)
      await fetchDatabases()
      if (onRefresh) onRefresh()
    } catch (err) {
      console.error("Failed to delete database:", err)
      alert("DB 삭제에 실패했습니다.")
    }
  }

  const handleRefresh = () => {
    fetchDatabases()
    if (onRefresh) onRefresh()
  }

  if (loading) {
    return (
      <Card className="h-full">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              <CardTitle className="text-lg">등록된 DB</CardTitle>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-2">
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="h-full">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              <CardTitle className="text-lg">등록된 DB</CardTitle>
            </div>
            <Button variant="ghost" size="sm" onClick={handleRefresh}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive">{error}</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            <CardTitle className="text-lg">등록된 DB</CardTitle>
          </div>
          <div className="flex items-center gap-1">
            <Badge variant="outline">{databases.length}</Badge>
            <Button variant="ghost" size="sm" onClick={handleRefresh}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-2">
        {databases.length === 0 ? (
          <div className="text-center py-8 text-sm text-muted-foreground">
            <Database className="h-12 w-12 mx-auto mb-3 opacity-20" />
            <p>등록된 데이터베이스가 없습니다.</p>
            <p className="text-xs mt-1">tnsnames.ora에서 DB를 등록하세요.</p>
          </div>
        ) : (
          databases.map((db) => (
            <div
              key={db.database_sid}
              className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                selectedDatabaseSid === db.database_sid
                  ? "bg-primary/10 border-primary"
                  : "hover:bg-muted"
              }`}
              onClick={() => onSelectDatabase && onSelectDatabase(db)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold text-sm truncate">{db.database_sid}</span>
                    {db.is_connected ? (
                      <CheckCircle2 className="h-3 w-3 text-green-500 flex-shrink-0" />
                    ) : (
                      <XCircle className="h-3 w-3 text-gray-400 flex-shrink-0" />
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground truncate">
                    {db.user}@{db.host}:{db.port}
                  </p>
                  <p className="text-xs text-muted-foreground truncate mt-1">
                    {db.service_name}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 w-6 p-0 flex-shrink-0"
                  onClick={(e) => handleDelete(db.database_sid, e)}
                >
                  <Trash2 className="h-3 w-3 text-destructive" />
                </Button>
              </div>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  )
}
