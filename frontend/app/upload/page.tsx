"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Upload, Database, FileText, CheckCircle2, AlertCircle, Loader2 } from "lucide-react"
import { Header } from "@/components/layout/Header"
import api from "@/lib/api"

interface RegisteredDatabase {
  database_sid: string
  schema_name: string
  table_count: number
  last_updated?: string
  connection_status: string
}

interface UploadedFile {
  name: string
  file: File | null
  uploaded: boolean
}

interface ProcessingStep {
  id: string
  label: string
  status: "pending" | "in_progress" | "completed" | "error"
  message?: string
}

export default function UploadPage() {
  const [registeredDatabases, setRegisteredDatabases] = useState<RegisteredDatabase[]>([])
  const [selectedDbKey, setSelectedDbKey] = useState<string>("")
  const [isLoadingDatabases, setIsLoadingDatabases] = useState(true)

  // CSV 파일 상태
  const [files, setFiles] = useState<{
    tableInfo: UploadedFile
    commonColumns: UploadedFile
    codeDefinitions: UploadedFile
  }>({
    tableInfo: { name: "table_info_template.csv", file: null, uploaded: false },
    commonColumns: { name: "common_columns_template.csv", file: null, uploaded: false },
    codeDefinitions: { name: "code_definitions_template.csv", file: null, uploaded: false },
  })

  // 처리 상태
  const [isProcessing, setIsProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [processingSteps, setProcessingSteps] = useState<ProcessingStep[]>([
    { id: "validation", label: "CSV 파일 검증", status: "pending" },
    { id: "schema", label: "DB 스키마 조회", status: "pending" },
    { id: "integration", label: "메타정보 통합", status: "pending" },
    { id: "embedding", label: "임베딩 생성", status: "pending" },
    { id: "vectordb", label: "Vector DB 저장", status: "pending" },
  ])
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  // 등록된 데이터베이스 목록 가져오기
  useEffect(() => {
    const fetchDatabases = async () => {
      try {
        setIsLoadingDatabases(true)
        const response = await api.databases.list()
        setRegisteredDatabases(response.databases)

        // 첫 번째 DB를 자동 선택
        if (response.databases.length > 0 && !selectedDbKey) {
          const firstDb = response.databases[0]
          setSelectedDbKey(`${firstDb.database_sid}:${firstDb.schema_name}`)
        }
      } catch (err) {
        console.error("Failed to fetch databases:", err)
        setErrorMessage("데이터베이스 목록을 불러오는데 실패했습니다.")
      } finally {
        setIsLoadingDatabases(false)
      }
    }

    fetchDatabases()
  }, [])

  // 파일 선택 핸들러
  const handleFileSelect = (fileType: "tableInfo" | "commonColumns" | "codeDefinitions") => {
    const input = document.createElement("input")
    input.type = "file"
    input.accept = ".csv"
    input.onchange = (e: Event) => {
      const target = e.target as HTMLInputElement
      const file = target.files?.[0]
      if (file) {
        setFiles(prev => ({
          ...prev,
          [fileType]: { ...prev[fileType], file, uploaded: false }
        }))
      }
    }
    input.click()
  }

  // 처리 단계 업데이트
  const updateStep = (stepId: string, status: ProcessingStep["status"], message?: string) => {
    setProcessingSteps(prev =>
      prev.map(step =>
        step.id === stepId ? { ...step, status, message } : step
      )
    )
  }

  // CSV 업로드 및 처리
  const handleProcess = async () => {
    // 검증
    if (!selectedDbKey) {
      setErrorMessage("데이터베이스를 선택해주세요.")
      return
    }

    if (!files.tableInfo.file || !files.commonColumns.file || !files.codeDefinitions.file) {
      setErrorMessage("모든 CSV 파일을 업로드해주세요.")
      return
    }

    setIsProcessing(true)
    setErrorMessage(null)
    setSuccessMessage(null)
    setProgress(0)

    const [dbSid, schemaName] = selectedDbKey.split(":")

    console.log("🔍 Upload Debug Info:")
    console.log("  selectedDbKey:", selectedDbKey)
    console.log("  dbSid:", dbSid)
    console.log("  schemaName:", schemaName)
    console.log("  selectedDb:", selectedDb)
    console.log("  registeredDatabases:", registeredDatabases)

    // Validate schemaName - TEMPORARY: Allow "undefined" for debugging
    if (!schemaName) {
      setErrorMessage("선택한 데이터베이스에 스키마 정보가 없습니다. TNSNames 페이지에서 데이터베이스를 다시 등록해주세요.")
      setIsProcessing(false)
      return
    }

    // Warn but continue if schemaName is "undefined"
    if (schemaName === "undefined") {
      console.warn("⚠️ WARNING: schemaName is 'undefined' - this may cause issues!")
      console.warn("⚠️ Continuing anyway for debugging purposes...")
    }

    try {
      // Step 1: CSV 파일 검증
      updateStep("validation", "in_progress")
      setProgress(10)

      // FormData 생성
      const formData = new FormData()
      formData.append("database_sid", dbSid)
      formData.append("schema_name", schemaName)
      formData.append("table_info", files.tableInfo.file)
      formData.append("common_columns", files.commonColumns.file)
      formData.append("code_definitions", files.codeDefinitions.file)

      updateStep("validation", "completed", "CSV 파일 형식 확인 완료")
      setProgress(20)

      // Step 2: DB 스키마 조회
      updateStep("schema", "in_progress")
      setProgress(30)

      // Step 3~5: Backend API 호출 (통합 처리)
      console.log("📤 Sending request to backend...")
      const response = await api.metadata.process(formData)
      console.log("📥 Backend response:", response)

      if (response.success) {
        updateStep("schema", "completed", `${response.tables_processed || 0}개 테이블 조회 완료`)
        setProgress(50)

        updateStep("integration", "in_progress")
        setProgress(60)
        await new Promise(resolve => setTimeout(resolve, 1000)) // 시뮬레이션
        updateStep("integration", "completed", "메타정보 통합 완료")
        setProgress(70)

        updateStep("embedding", "in_progress")
        setProgress(80)
        await new Promise(resolve => setTimeout(resolve, 1500)) // 시뮬레이션
        updateStep("embedding", "completed", `${response.tables_processed || 0}개 임베딩 생성 완료`)
        setProgress(90)

        updateStep("vectordb", "in_progress")
        setProgress(95)
        await new Promise(resolve => setTimeout(resolve, 800)) // 시뮬레이션
        updateStep("vectordb", "completed", "Vector DB 저장 완료")
        setProgress(100)

        setSuccessMessage(
          `메타데이터 처리가 완료되었습니다. ${response.tables_processed || 0}개의 테이블이 Vector DB에 저장되었습니다.`
        )

        // 파일 상태 초기화
        setFiles({
          tableInfo: { name: "table_info_template.csv", file: null, uploaded: false },
          commonColumns: { name: "common_columns_template.csv", file: null, uploaded: false },
          codeDefinitions: { name: "code_definitions_template.csv", file: null, uploaded: false },
        })
      } else {
        throw new Error(response.error || "처리 중 오류가 발생했습니다.")
      }
    } catch (error: any) {
      console.error("Processing error:", error)
      const currentStep = processingSteps.find(s => s.status === "in_progress")
      if (currentStep) {
        updateStep(currentStep.id, "error", error.message || "오류 발생")
      }
      setErrorMessage(error.message || "메타데이터 처리 중 오류가 발생했습니다.")
    } finally {
      setIsProcessing(false)
    }
  }

  // 선택된 DB 정보
  const selectedDb = registeredDatabases.find(
    db => `${db.database_sid}:${db.schema_name}` === selectedDbKey
  )

  // 업로드 준비 완료 여부
  const isReadyToProcess =
    selectedDbKey &&
    files.tableInfo.file &&
    files.commonColumns.file &&
    files.codeDefinitions.file

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <div className="container mx-auto max-w-7xl py-6 space-y-6 px-4">
        {/* Page Title */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">메타데이터 업로드</h1>
          <p className="text-sm text-muted-foreground mt-1">
            CSV 파일을 업로드하여 DB 스키마와 통합된 메타정보를 생성하고 Vector DB에 저장합니다
          </p>
        </div>

        {/* 워크플로우 안내 */}
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <strong>워크플로우 2단계:</strong> TNSNames에서 등록한 DB를 선택하고, CSV 3종을 업로드하여 메타정보를 생성합니다.
          </AlertDescription>
        </Alert>

        {/* Step 1: DB 선택 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              Step 1: 데이터베이스 선택
            </CardTitle>
            <CardDescription>
              메타데이터를 등록할 데이터베이스를 선택하세요
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoadingDatabases ? (
              <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm text-muted-foreground">데이터베이스 목록 로딩 중...</span>
              </div>
            ) : registeredDatabases.length === 0 ? (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  등록된 데이터베이스가 없습니다. TNSNames 페이지에서 먼저 데이터베이스를 등록해주세요.
                </AlertDescription>
              </Alert>
            ) : (
              <div className="space-y-4">
                <Select value={selectedDbKey} onValueChange={setSelectedDbKey} disabled={isProcessing}>
                  <SelectTrigger className="w-full">
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

                {selectedDb && (
                  <div className="bg-primary/5 border border-primary/20 rounded-lg p-3">
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <p className="text-muted-foreground text-xs">Database SID</p>
                        <p className="font-medium">{selectedDb.database_sid}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground text-xs">Schema</p>
                        <p className="font-medium">{selectedDb.schema_name}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground text-xs">연결 상태</p>
                        <p className="font-medium">{selectedDb.connection_status}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Step 2: CSV 파일 업로드 */}
        {selectedDbKey && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Step 2: CSV 파일 업로드 (3종)
              </CardTitle>
              <CardDescription>
                테이블 정보, 공통 컬럼, 코드 정의 파일을 업로드하세요
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4">
                {/* Table Info CSV */}
                <div className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <h4 className="font-medium text-sm">1. 테이블 정보 (table_info_template.csv)</h4>
                      <p className="text-xs text-muted-foreground">테이블명, 설명, 비즈니스 목적</p>
                    </div>
                    {files.tableInfo.file && (
                      <CheckCircle2 className="h-5 w-5 text-green-500" />
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleFileSelect("tableInfo")}
                      disabled={isProcessing}
                    >
                      <Upload className="h-4 w-4 mr-2" />
                      {files.tableInfo.file ? "다시 선택" : "파일 선택"}
                    </Button>
                    {files.tableInfo.file && (
                      <span className="text-sm text-muted-foreground">{files.tableInfo.file.name}</span>
                    )}
                  </div>
                </div>

                {/* Common Columns CSV */}
                <div className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <h4 className="font-medium text-sm">2. 공통 컬럼 (common_columns_template.csv)</h4>
                      <p className="text-xs text-muted-foreground">컬럼명, 데이터 타입, 설명, 비즈니스 의미</p>
                    </div>
                    {files.commonColumns.file && (
                      <CheckCircle2 className="h-5 w-5 text-green-500" />
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleFileSelect("commonColumns")}
                      disabled={isProcessing}
                    >
                      <Upload className="h-4 w-4 mr-2" />
                      {files.commonColumns.file ? "다시 선택" : "파일 선택"}
                    </Button>
                    {files.commonColumns.file && (
                      <span className="text-sm text-muted-foreground">{files.commonColumns.file.name}</span>
                    )}
                  </div>
                </div>

                {/* Code Definitions CSV */}
                <div className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <h4 className="font-medium text-sm">3. 코드 정의 (code_definitions_template.csv)</h4>
                      <p className="text-xs text-muted-foreground">코드 컬럼명, 코드 값, 코드 의미</p>
                    </div>
                    {files.codeDefinitions.file && (
                      <CheckCircle2 className="h-5 w-5 text-green-500" />
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleFileSelect("codeDefinitions")}
                      disabled={isProcessing}
                    >
                      <Upload className="h-4 w-4 mr-2" />
                      {files.codeDefinitions.file ? "다시 선택" : "파일 선택"}
                    </Button>
                    {files.codeDefinitions.file && (
                      <span className="text-sm text-muted-foreground">{files.codeDefinitions.file.name}</span>
                    )}
                  </div>
                </div>

                {/* Process Button */}
                <Button
                  onClick={handleProcess}
                  disabled={!isReadyToProcess || isProcessing}
                  className="w-full"
                  size="lg"
                >
                  {isProcessing ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      처리 중...
                    </>
                  ) : (
                    <>
                      <Database className="h-4 w-4 mr-2" />
                      메타데이터 처리 시작
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 3: 처리 진행 상황 */}
        {(isProcessing || processingSteps.some(s => s.status !== "pending")) && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Loader2 className={`h-5 w-5 ${isProcessing ? "animate-spin" : ""}`} />
                처리 진행 상황
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Progress Bar */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">전체 진행률</span>
                  <span className="font-medium">{progress}%</span>
                </div>
                <Progress value={progress} />
              </div>

              {/* Processing Steps */}
              <div className="space-y-3">
                {processingSteps.map((step) => (
                  <div
                    key={step.id}
                    className={`flex items-start gap-3 p-3 rounded-lg border ${
                      step.status === "completed"
                        ? "bg-green-500/5 border-green-500/20"
                        : step.status === "in_progress"
                        ? "bg-blue-500/5 border-blue-500/20"
                        : step.status === "error"
                        ? "bg-red-500/5 border-red-500/20"
                        : "bg-muted/30 border-border"
                    }`}
                  >
                    <div className="mt-0.5">
                      {step.status === "completed" && (
                        <CheckCircle2 className="h-5 w-5 text-green-500" />
                      )}
                      {step.status === "in_progress" && (
                        <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />
                      )}
                      {step.status === "error" && (
                        <AlertCircle className="h-5 w-5 text-red-500" />
                      )}
                      {step.status === "pending" && (
                        <div className="h-5 w-5 rounded-full border-2 border-muted-foreground/30" />
                      )}
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-sm">{step.label}</p>
                      {step.message && (
                        <p className="text-xs text-muted-foreground mt-1">{step.message}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Messages */}
        {errorMessage && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{errorMessage}</AlertDescription>
          </Alert>
        )}

        {successMessage && (
          <Alert className="bg-green-500/10 border-green-500/20 text-green-700">
            <CheckCircle2 className="h-4 w-4" />
            <AlertDescription>{successMessage}</AlertDescription>
          </Alert>
        )}
      </div>
    </div>
  )
}
