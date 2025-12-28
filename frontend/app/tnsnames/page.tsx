"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { FormField } from "@/components/ui/form-field"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Database, FileSearch, Search, Plus, CheckCircle } from "lucide-react"
import { DatabaseSidebar } from "@/components/DatabaseSidebar"
import { Header } from "@/components/layout/Header"
import api from "@/lib/api"
import type { DatabaseConnection, RegisteredDatabase } from "@/lib/types"

export default function TNSNamesPage() {
  const [filePath, setFilePath] = useState("")
  const [databases, setDatabases] = useState<DatabaseConnection[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [message, setMessage] = useState("")
  const [searchKeyword, setSearchKeyword] = useState("")
  const [selectedDatabase, setSelectedDatabase] = useState<RegisteredDatabase | null>(null)

  // Registration dialog state
  const [isRegisterDialogOpen, setIsRegisterDialogOpen] = useState(false)
  const [registeringSid, setRegisteringSid] = useState("")
  const [registerSchemaName, setRegisterSchemaName] = useState("")
  const [registerUser, setRegisterUser] = useState("")
  const [registerPassword, setRegisterPassword] = useState("")
  const [registerMessage, setRegisterMessage] = useState("")
  const [isRegistering, setIsRegistering] = useState(false)

  const handleParse = async () => {
    if (!filePath) {
      setMessage("파일 경로를 입력해주세요.")
      return
    }

    setIsLoading(true)
    setMessage("")

    try {
      const result = await api.tnsnames.parse(filePath)

      if (result.success) {
        setDatabases(result.databases)
        setMessage(`✓ 성공: ${result.total_databases}개의 데이터베이스를 파싱했습니다.`)
      } else {
        setMessage(`✗ 실패: ${result.error || "알 수 없는 오류"}`)
        setDatabases([])
      }
    } catch (error) {
      setMessage(`✗ 오류: ${error}`)
      setDatabases([])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSearch = async () => {
    if (!searchKeyword) {
      try {
        const result = await api.tnsnames.list()
        setDatabases(result.databases)
      } catch (error) {
        setMessage(`✗ 검색 오류: ${error}`)
      }
      return
    }

    try {
      const result = await api.tnsnames.search(searchKeyword)
      setDatabases(result.databases)
      setMessage(`✓ ${result.total_count}개의 데이터베이스를 찾았습니다.`)
    } catch (error) {
      setMessage(`✗ 검색 오류: ${error}`)
    }
  }

  const openRegisterDialog = (sid: string) => {
    setRegisteringSid(sid)
    setRegisterSchemaName("")
    setRegisterUser("")
    setRegisterPassword("")
    setRegisterMessage("")
    setIsRegisterDialogOpen(true)
  }

  const handleRegister = async () => {
    if (!registerSchemaName || !registerUser || !registerPassword) {
      setRegisterMessage("스키마명, 사용자 이름, 비밀번호를 모두 입력해주세요.")
      return
    }

    setIsRegistering(true)
    setRegisterMessage("")

    try {
      const result = await api.databases.registerFromTnsnames(
        registeringSid,
        registerSchemaName,
        registerUser,
        registerPassword
      )

      if (result.success) {
        setRegisterMessage(`✓ 성공: ${registeringSid} 데이터베이스가 등록되었습니다.`)
        setTimeout(() => {
          setIsRegisterDialogOpen(false)
          setRegisterSchemaName("")
          setRegisterUser("")
          setRegisterPassword("")
          setRegisterMessage("")
        }, 1500)
      } else {
        setRegisterMessage(`✗ 실패: 데이터베이스 등록에 실패했습니다.`)
      }
    } catch (error: any) {
      setRegisterMessage(`✗ 오류: ${error.response?.data?.detail || error.message}`)
    } finally {
      setIsRegistering(false)
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <div className="h-[calc(100vh-4rem)] flex">
        {/* Left Sidebar - Registered Databases */}
        <div className="w-80 border-r p-4 overflow-y-auto">
          <DatabaseSidebar
            selectedDatabaseSid={selectedDatabase?.database_sid}
            onSelectDatabase={setSelectedDatabase}
          />
        </div>

        {/* Main Content */}
        <div className="flex-1 overflow-y-auto">
          <div className="container mx-auto p-6 space-y-6">
            <div>
              <h1 className="text-3xl font-bold tracking-tight">TNSNames 관리</h1>
              <p className="text-sm text-muted-foreground mt-1">
                tnsnames.ora 파일을 파싱하여 Oracle 데이터베이스 연결 정보를 관리합니다
              </p>
            </div>

          {/* Parse tnsnames.ora file */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <FileSearch className="h-5 w-5" />
                <CardTitle>tnsnames.ora 파일 파싱</CardTitle>
              </div>
              <CardDescription>
                Oracle 클라이언트의 tnsnames.ora 파일 경로를 입력하여 데이터베이스 연결 정보를 추출합니다.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <FormField
                  label="tnsnames.ora 파일 경로"
                  helpText="Oracle 클라이언트 설치 경로의 network/admin 디렉토리에 있는 tnsnames.ora 파일의 절대 경로를 입력하세요. 예: D:\app\oracle\product\19c\network\admin\tnsnames.ora 또는 /opt/oracle/product/19c/network/admin/tnsnames.ora"
                  placeholder="예: D:\app\oracle\product\19c\network\admin\tnsnames.ora"
                  value={filePath}
                  onChange={(e) => setFilePath(e.target.value)}
                />

                {message && (
                  <div
                    className={`text-sm p-3 rounded ${
                      message.startsWith("✓")
                        ? "bg-green-500/10 text-green-500"
                        : "bg-red-500/10 text-red-500"
                    }`}
                  >
                    {message}
                  </div>
                )}

                <Button onClick={handleParse} disabled={isLoading}>
                  {isLoading ? "파싱 중..." : "파싱 시작"}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Search and Database List */}
          {databases.length > 0 && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Database className="h-5 w-5" />
                    <CardTitle>파싱된 데이터베이스 목록</CardTitle>
                  </div>
                  <Badge variant="outline">{databases.length}개</Badge>
                </div>
                <CardDescription>
                  tnsnames.ora에서 추출한 Oracle 데이터베이스 연결 정보입니다. 등록 버튼을 클릭하여 DB를 시스템에 등록하세요.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Search */}
                  <div className="flex gap-2">
                    <FormField
                      label=""
                      helpText="데이터베이스 SID 또는 설명(Description)에서 키워드를 검색합니다. 검색 결과는 실시간으로 필터링됩니다."
                      placeholder="SID 또는 설명으로 검색..."
                      value={searchKeyword}
                      onChange={(e) => setSearchKeyword(e.target.value)}
                      className="flex-1"
                    />
                    <Button onClick={handleSearch} variant="outline" className="mt-auto">
                      <Search className="h-4 w-4 mr-2" />
                      검색
                    </Button>
                  </div>

                  {/* Database Table */}
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>SID</TableHead>
                        <TableHead>Host</TableHead>
                        <TableHead>Port</TableHead>
                        <TableHead>Service Name</TableHead>
                        <TableHead>Connection Type</TableHead>
                        <TableHead>Description</TableHead>
                        <TableHead className="text-right">작업</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {databases.map((db) => (
                        <TableRow key={db.sid}>
                          <TableCell className="font-medium">{db.sid}</TableCell>
                          <TableCell>{db.host}</TableCell>
                          <TableCell>{db.port}</TableCell>
                          <TableCell>{db.service_name}</TableCell>
                          <TableCell>
                            <Badge variant={db.connection_type === "SID" ? "default" : "secondary"}>
                              {db.connection_type}
                            </Badge>
                          </TableCell>
                          <TableCell className="text-sm text-muted-foreground">
                            {db.description || "N/A"}
                          </TableCell>
                          <TableCell className="text-right">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => openRegisterDialog(db.sid)}
                            >
                              <Plus className="h-3 w-3 mr-1" />
                              등록
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Info Card */}
          <Card>
            <CardHeader>
              <CardTitle>사용 안내</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h3 className="font-semibold mb-2">1. tnsnames.ora 파일 찾기</h3>
                <p className="text-sm text-muted-foreground">
                  Oracle 클라이언트가 설치된 디렉토리에서{" "}
                  <code className="bg-muted px-1 rounded">network/admin/tnsnames.ora</code> 파일을 찾습니다.
                </p>
                <ul className="text-sm text-muted-foreground list-disc list-inside mt-2 space-y-1">
                  <li>
                    Windows:{" "}
                    <code className="bg-muted px-1 rounded">
                      D:\app\oracle\product\19c\network\admin\tnsnames.ora
                    </code>
                  </li>
                  <li>
                    Linux:{" "}
                    <code className="bg-muted px-1 rounded">
                      /opt/oracle/product/19c/network/admin/tnsnames.ora
                    </code>
                  </li>
                </ul>
              </div>

              <div>
                <h3 className="font-semibold mb-2">2. 파일 파싱</h3>
                <p className="text-sm text-muted-foreground">
                  파일 경로를 입력하고 "파싱 시작" 버튼을 클릭하면 모든 데이터베이스 연결 정보가 추출됩니다.
                </p>
              </div>

              <div>
                <h3 className="font-semibold mb-2">3. 데이터베이스 등록</h3>
                <p className="text-sm text-muted-foreground">
                  파싱된 DB 목록에서 원하는 DB의 "등록" 버튼을 클릭하고, 사용자 이름과 비밀번호를 입력하여 시스템에 등록합니다.
                  등록된 DB는 왼쪽 사이드바에 표시됩니다.
                </p>
              </div>

              <div>
                <h3 className="font-semibold mb-2">4. 등록된 DB 관리</h3>
                <p className="text-sm text-muted-foreground">
                  왼쪽 사이드바에서 등록된 DB 목록을 확인하고, 삭제 버튼으로 더 이상 사용하지 않는 DB를 제거할 수 있습니다.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
      </div>

      {/* Registration Dialog */}
      <Dialog open={isRegisterDialogOpen} onOpenChange={setIsRegisterDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>데이터베이스 등록</DialogTitle>
            <DialogDescription>
              {registeringSid} 데이터베이스에 접속할 사용자 정보를 입력하세요.
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <FormField
              id="register_schema_name"
              label="스키마 이름"
              helpText="조회할 스키마 이름입니다. 일반적으로 사용자 이름과 동일합니다. 예: SMVNPDBext, HR, SCOTT 등"
              placeholder="예: SMVNPDBext"
              value={registerSchemaName}
              onChange={(e) => setRegisterSchemaName(e.target.value)}
            />
            <FormField
              id="register_user"
              label="사용자 이름"
              helpText="Oracle 데이터베이스 접속 계정 이름입니다. 일반적으로 대문자로 입력합니다. 예: SYSTEM, HR, SCOTT 등"
              placeholder="예: SYSTEM"
              value={registerUser}
              onChange={(e) => setRegisterUser(e.target.value)}
            />
            <FormField
              id="register_password"
              label="비밀번호"
              type="password"
              helpText="Oracle 데이터베이스 접속 비밀번호입니다. 입력한 비밀번호는 암호화되어 안전하게 저장됩니다."
              placeholder="비밀번호 입력"
              value={registerPassword}
              onChange={(e) => setRegisterPassword(e.target.value)}
            />
            {registerMessage && (
              <div
                className={`text-sm p-2 rounded ${
                  registerMessage.startsWith("✓")
                    ? "bg-green-500/10 text-green-500"
                    : "bg-red-500/10 text-red-500"
                }`}
              >
                {registerMessage}
              </div>
            )}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setIsRegisterDialogOpen(false)}
              disabled={isRegistering}
            >
              취소
            </Button>
            <Button onClick={handleRegister} disabled={isRegistering}>
              {isRegistering ? "등록 중..." : "등록"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
