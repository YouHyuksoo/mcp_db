"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Database, Table, FileText, Activity, ChevronDown } from "lucide-react"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import api from "@/lib/api"
import { HealthStatus } from "@/lib/types"
import { DatabaseList } from "@/components/dashboard/DatabaseList"
import { PatternList } from "@/components/dashboard/PatternList"
import { Header } from "@/components/layout/Header"

interface RegisteredDatabase {
  database_sid: string
  schema_name: string
  table_count: number
  last_updated?: string
  connection_status: string
}

interface DatabaseStats {
  metadata_count: number
  patterns_count: number
  business_rules_count: number
}

export default function Dashboard() {
  const [registeredDatabases, setRegisteredDatabases] = useState<RegisteredDatabase[]>([])
  const [selectedDbKey, setSelectedDbKey] = useState<string>("")
  const [dbStats, setDbStats] = useState<DatabaseStats | null>(null)
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // 등록된 데이터베이스 목록 가져오기
  const fetchRegisteredDatabases = async () => {
    try {
      const response = await api.databases.list()
      setRegisteredDatabases(response.databases)

      // 첫 번째 DB를 자동 선택
      if (response.databases.length > 0 && !selectedDbKey) {
        const firstDb = response.databases[0]
        setSelectedDbKey(`${firstDb.database_sid}:${firstDb.schema_name}`)
      }
    } catch (err) {
      console.error("Failed to fetch registered databases:", err)
    }
  }

  // 선택된 DB의 통계 가져오기
  const fetchDatabaseStats = async (dbSid: string, schemaName: string) => {
    try {
      setLoading(true)
      // TODO: Backend API에 database_sid와 schema_name으로 필터링된 통계 요청
      // 현재는 임시로 전체 통계를 가져옴
      const summary = await api.dashboard.getSummary()

      // 선택된 DB에 해당하는 데이터만 필터링
      const selectedDb = registeredDatabases.find(
        db => db.database_sid === dbSid && db.schema_name === schemaName
      )

      if (selectedDb) {
        setDbStats({
          metadata_count: selectedDb.table_count,
          patterns_count: summary.vector_db_stats.patterns_count,
          business_rules_count: summary.vector_db_stats.business_rules_count
        })
      }
    } catch (err) {
      console.error("Failed to fetch database stats:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const init = async () => {
      try {
        const healthData = await api.health.check()
        setHealth(healthData)
        await fetchRegisteredDatabases()
      } catch (err) {
        console.error("Failed to initialize:", err)
        setError("초기 데이터를 불러오는데 실패했습니다.")
      }
    }
    init()
  }, [])

  useEffect(() => {
    if (selectedDbKey) {
      const [dbSid, schemaName] = selectedDbKey.split(":")
      fetchDatabaseStats(dbSid, schemaName)
    }
  }, [selectedDbKey, registeredDatabases])

  const selectedDb = registeredDatabases.find(db =>
    `${db.database_sid}:${db.schema_name}` === selectedDbKey
  )

  const stats = [
    {
      title: "Vector DB",
      value: health?.vector_db === "healthy" ? "온라인" : "초기화 필요",
      icon: Database,
      status: health?.vector_db === "healthy" ? "success" : "warning",
    },
    {
      title: "임베딩 서비스",
      value: health?.embedding_service === "healthy" ? "정상" : "오프라인",
      icon: Activity,
      status: health?.embedding_service === "healthy" ? "success" : "error",
    },
    {
      title: "테이블",
      value: loading ? "..." : `${dbStats?.metadata_count || 0}개`,
      icon: Table,
      status: "info",
    },
    {
      title: "SQL 패턴",
      value: loading ? "..." : `${dbStats?.patterns_count || 0}개`,
      icon: FileText,
      status: "info",
    },
    {
      title: "비즈니스 규칙",
      value: loading ? "..." : `${dbStats?.business_rules_count || 0}개`,
      icon: FileText,
      status: "info",
    },
  ]

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <Header />

      {/* Main Content */}
      <div className="container mx-auto max-w-7xl py-6 space-y-6 px-4">
        {/* Page Title & Database Selector */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">대시보드</h1>
            <p className="text-sm text-muted-foreground mt-1">
              Oracle NL-SQL Management Backend
            </p>
          </div>

          {/* Database Selector */}
          {registeredDatabases.length > 0 && (
            <div className="w-96">
              <Select value={selectedDbKey} onValueChange={setSelectedDbKey}>
                <SelectTrigger className="w-full">
                  <Database className="h-4 w-4 mr-2" />
                  <SelectValue placeholder="데이터베이스 선택" />
                </SelectTrigger>
                <SelectContent>
                  {registeredDatabases.map((db) => {
                    const key = `${db.database_sid}:${db.schema_name}`
                    return (
                      <SelectItem key={key} value={key}>
                        <div className="flex items-center justify-between w-full">
                          <span className="font-medium">{db.database_sid}</span>
                          <span className="text-xs text-muted-foreground ml-2">
                            ({db.schema_name})
                          </span>
                        </div>
                      </SelectItem>
                    )
                  })}
                </SelectContent>
              </Select>
            </div>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-3">
            <p className="text-destructive text-sm font-medium">{error}</p>
            <p className="text-destructive/70 text-xs mt-1">
              Backend 서버가 실행 중인지 확인하세요 (http://localhost:8000)
            </p>
          </div>
        )}

        {/* No Database Selected */}
        {registeredDatabases.length === 0 && (
          <Card>
            <CardHeader>
              <CardTitle>등록된 데이터베이스가 없습니다</CardTitle>
              <CardDescription>
                TNSNames 페이지에서 데이터베이스를 먼저 등록해주세요.
              </CardDescription>
            </CardHeader>
          </Card>
        )}

        {/* Selected Database Info */}
        {selectedDb && (
          <>
            {/* Selected DB Info Card */}
            <Card className="bg-primary/5 border-primary/20">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Database className="h-5 w-5" />
                    선택된 데이터베이스
                  </CardTitle>
                  <div className="text-xs text-muted-foreground">
                    {selectedDb.last_updated &&
                      `마지막 업데이트: ${new Date(selectedDb.last_updated).toLocaleString("ko-KR")}`
                    }
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-4 gap-4 text-sm">
                  <div>
                    <p className="text-muted-foreground text-xs">Database SID</p>
                    <p className="font-medium">{selectedDb.database_sid}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground text-xs">Schema</p>
                    <p className="font-medium">{selectedDb.schema_name}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground text-xs">테이블 수</p>
                    <p className="font-medium">{selectedDb.table_count}개</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground text-xs">연결 상태</p>
                    <p className="font-medium">{selectedDb.connection_status}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Stats Grid */}
            <div className="grid gap-3 grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
              {stats.map((stat) => {
                const Icon = stat.icon
                return (
                  <Card key={stat.title} className="transition-all hover:shadow-md">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-xs font-medium text-muted-foreground">
                        {stat.title}
                      </CardTitle>
                      <Icon className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-xl font-bold">{stat.value}</div>
                      <div className="flex items-center gap-1.5 mt-1">
                        <div
                          className={`h-1.5 w-1.5 rounded-full ${
                            stat.status === "success"
                              ? "bg-green-500 animate-pulse"
                              : stat.status === "warning"
                              ? "bg-yellow-500"
                              : stat.status === "error"
                              ? "bg-red-500"
                              : "bg-blue-500"
                          }`}
                        />
                        <p className="text-xs text-muted-foreground">
                          {stat.status === "success"
                            ? "정상"
                            : stat.status === "warning"
                            ? "주의"
                            : stat.status === "error"
                            ? "오류"
                            : "정보"}
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>

            {/* System Info - Compact */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-medium flex items-center gap-1.5">
                  <Activity className="h-3.5 w-3.5" />
                  시스템 정보
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-7 gap-3 text-xs">
                  <div className="space-y-0.5">
                    <p className="text-muted-foreground text-[10px]">버전</p>
                    <p className="font-medium">2.0.0</p>
                  </div>
                  <div className="space-y-0.5">
                    <p className="text-muted-foreground text-[10px]">임베딩 모델</p>
                    <p className="font-medium">MiniLM-L6</p>
                  </div>
                  <div className="space-y-0.5">
                    <p className="text-muted-foreground text-[10px]">Vector DB</p>
                    <p className="font-medium">ChromaDB</p>
                  </div>
                  <div className="space-y-0.5">
                    <p className="text-muted-foreground text-[10px]">Backend</p>
                    <p className="font-medium">:8000</p>
                  </div>
                  <div className="space-y-0.5">
                    <p className="text-muted-foreground text-[10px]">Frontend</p>
                    <p className="font-medium">Next.js 16</p>
                  </div>
                  <div className="space-y-0.5">
                    <p className="text-muted-foreground text-[10px]">MCP Server</p>
                    <p className="font-medium">17 Tools</p>
                  </div>
                  <div className="space-y-0.5">
                    <p className="text-muted-foreground text-[10px]">Python</p>
                    <p className="font-medium">3.11+</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Recent Patterns for Selected DB */}
            <PatternList
              patterns={[]} // TODO: 선택된 DB의 패턴만 필터링
              loading={loading}
            />
          </>
        )}
      </div>
    </div>
  )
}
