/**
 * @file frontend/app/upload/page.tsx
 * @description
 * 이 페이지는 메타데이터 학습을 위한 CSV 파일 업로드 기능을 담당합니다.
 * 사용자는 등록된 DB를 선택하고, 테이블 정보/공통 칼럼/코드 정의 CSV를 업로드하여
 * 시스템이 데이터를 학습(임베딩 및 Vector DB 저장)하도록 요청합니다.
 *
 * 초보자 가이드:
 * 1. **DB 선택**: 상단 셀렉트 박스에서 학습시킬 대상 DB를 먼저 선택해야 합니다.
 * 2. **CSV 파일**: 템플릿 양식에 맞는 3종의 파일을 모두 선택한 후 '학습 시작' 버튼을 누르세요.
 * 3. **진행 상태**: 업로드부터 Vector DB 저장까지의 단계별 상태가 카드로 표시됩니다.
 *
 * 유지보수 팁:
 * - 처리 단계 추가/변경: `processingSteps` 상태값과 `handleProcess` 함수 내 로직을 수정하세요.
 * - API 연동: `api.metadata.process` 호출 부분을 확인하세요.
 */
"use client";

import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Upload,
  Database,
  FileText,
  CheckCircle2,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { Header } from "@/components/layout/Header";
import api from "@/lib/api";
import { RegisteredDatabase as ApiRegisteredDatabase } from "@/lib/types";

// RegisteredDatabase interface is now imported from lib/types

interface UploadedFile {
  name: string;
  file: File | null;
  uploaded: boolean;
}

interface ProcessingStep {
  id: string;
  label: string;
  status: "pending" | "in_progress" | "completed" | "error";
  message?: string;
}

export default function UploadPage() {
  // RegisteredDatabase 타입 정의 (API 타입 사용)
  type RegisteredDatabase = ApiRegisteredDatabase;

  const [registeredDatabases, setRegisteredDatabases] = useState<
    RegisteredDatabase[]
  >([]);
  const [selectedDbKey, setSelectedDbKey] = useState<string>("");
  const [isLoadingDatabases, setIsLoadingDatabases] = useState(true);

  // CSV 파일 상태
  const [files, setFiles] = useState<{
    tableMetadata: UploadedFile;
    columnDefinitions: UploadedFile;
  }>({
    tableMetadata: { name: "table_metadata.csv", file: null, uploaded: false },
    columnDefinitions: {
      name: "column_definitions.csv",
      file: null,
      uploaded: false,
    },
  });

  // 처리 상태
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [processingSteps, setProcessingSteps] = useState<ProcessingStep[]>([
    { id: "validation", label: "CSV 파일 검증", status: "pending" },
    { id: "schema", label: "DB 스키마 조회", status: "pending" },
    { id: "integration", label: "메타정보 통합", status: "pending" },
    { id: "embedding", label: "임베딩 생성", status: "pending" },
    { id: "vectordb", label: "Vector DB 저장", status: "pending" },
  ]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // 등록된 데이터베이스 목록 가져오기
  useEffect(() => {
    const fetchDatabases = async () => {
      try {
        setIsLoadingDatabases(true);
        const response = await api.databases.list();
        // API 응답을 로컬 타입에 맞게 변환 (기본값 추가)
        const databases: ApiRegisteredDatabase[] = response.databases;
        setRegisteredDatabases(databases);

        // 첫 번째 DB를 자동 선택
        if (databases.length > 0 && !selectedDbKey) {
          const firstDb = databases[0];
          setSelectedDbKey(`${firstDb.database_sid}:${firstDb.schema_name}`);
        }
      } catch (err) {
        console.error("Failed to fetch databases:", err);
        setErrorMessage("데이터베이스 목록을 불러오는데 실패했습니다.");
      } finally {
        setIsLoadingDatabases(false);
      }
    };

    fetchDatabases();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 파일 선택 핸들러
  const handleFileSelect = (
    fileType: "tableMetadata" | "columnDefinitions"
  ) => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".csv";
    input.onchange = (e: Event) => {
      const target = e.target as HTMLInputElement;
      const file = target.files?.[0];
      if (file) {
        setFiles((prev) => ({
          ...prev,
          [fileType]: { ...prev[fileType], file, uploaded: false },
        }));
      }
    };
    input.click();
  };

  // 처리 단계 업데이트
  const updateStep = (
    stepId: string,
    status: ProcessingStep["status"],
    message?: string
  ) => {
    setProcessingSteps((prev) =>
      prev.map((step) =>
        step.id === stepId ? { ...step, status, message } : step
      )
    );
  };

  // CSV 업로드 및 처리
  const handleProcess = async () => {
    // 검증
    if (!selectedDbKey) {
      setErrorMessage("데이터베이스를 선택해주세요.");
      return;
    }

    if (!files.tableMetadata.file || !files.columnDefinitions.file) {
      setErrorMessage("모두 CSV 파일을 업로드해주세요.");
      return;
    }

    setIsProcessing(true);
    setErrorMessage(null);
    setSuccessMessage(null);
    setProgress(0);

    const [dbSid, schemaName] = selectedDbKey.split(":");

    console.log("🔍 Upload Debug Info:");
    console.log("  selectedDbKey:", selectedDbKey);
    console.log("  dbSid:", dbSid);
    console.log("  schemaName:", schemaName);

    // Validate schemaName
    if (!schemaName || schemaName === "undefined") {
      setErrorMessage(
        "선택한 데이터베이스에 스키마 정보가 없습니다. 데이터베이스 등록 시 스키마 정보를 정확히 입력해주세요."
      );
      setIsProcessing(false);
      return;
    }

    try {
      // Step 1: CSV 파일 검증
      updateStep("validation", "in_progress");
      setProgress(10);

      // FormData 생성
      const formData = new FormData();
      formData.append("db_key", dbSid); // API expects db_key (SID)
      // schema_name is fetched from credentials in backend using db_key
      formData.append("table_metadata", files.tableMetadata.file);
      formData.append("column_definitions", files.columnDefinitions.file);

      updateStep("validation", "completed", "CSV 파일 형식 확인 완료");
      setProgress(20);

      // Step 2: DB 스키마 조회
      updateStep("schema", "in_progress");
      setProgress(30);

      // Step 3~5: Backend API 호출 (통합 처리)
      console.log("📤 Sending request to backend...");
      const response = await api.metadata.process(formData);
      console.log("📥 Backend response:", response);

      if (response.success) {
        updateStep(
          "schema",
          "completed",
          `${response.tables_processed || 0}개 테이블 조회 완료`
        );
        setProgress(50);

        updateStep("integration", "in_progress");
        setProgress(60);
        await new Promise((resolve) => setTimeout(resolve, 500)); // 시뮬레이션
        updateStep("integration", "completed", "메타정보 통합 완료");
        setProgress(70);

        updateStep("embedding", "in_progress");
        setProgress(80);
        await new Promise((resolve) => setTimeout(resolve, 500)); // 시뮬레이션
        updateStep(
          "embedding",
          "completed",
          `${response.tables_processed || 0}개 임베딩 생성 완료`
        );
        setProgress(90);

        updateStep("vectordb", "in_progress");
        setProgress(95);
        await new Promise((resolve) => setTimeout(resolve, 500)); // 시뮬레이션
        updateStep("vectordb", "completed", "Vector DB 저장 완료");
        setProgress(100);

        setSuccessMessage(
          `메타데이터 처리가 완료되었습니다. ${
            response.tables_processed || 0
          }개의 테이블이 Vector DB에 저장되었습니다.`
        );

        // 파일 상태 초기화
        setFiles({
          tableMetadata: {
            name: "table_metadata.csv",
            file: null,
            uploaded: false,
          },
          columnDefinitions: {
            name: "column_definitions.csv",
            file: null,
            uploaded: false,
          },
        });
      } else {
        throw new Error(response.error || "처리 중 오류가 발생했습니다.");
      }
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : "오류 발생";
      console.error("Processing error:", error);
      const currentStep = processingSteps.find(
        (s) => s.status === "in_progress"
      );
      if (currentStep) {
        updateStep(currentStep.id, "error", errorMessage);
      }
      setErrorMessage(
        errorMessage || "메타데이터 처리 중 오류가 발생했습니다."
      );
    } finally {
      setIsProcessing(false);
      // Reset steps after delay? No, keep result visible
    }
  };

  // 선택된 DB 정보
  const selectedDb = registeredDatabases.find(
    (db) => `${db.database_sid}:${db.schema_name}` === selectedDbKey
  );

  // 업로드 준비 완료 여부 (누락된 변수 복구)
  const isReadyToProcess =
    selectedDbKey && files.tableMetadata.file && files.columnDefinitions.file;

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <div className="container mx-auto max-w-7xl py-6 space-y-6 px-4">
        {/* Page Title */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">
            메타데이터 업로드
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            CSV 파일을 업로드하여 DB 스키마와 통합된 메타정보를 생성하고 Vector
            DB에 저장합니다 (2종 통합 양식)
          </p>
        </div>

        {/* 워크플로우 안내 */}
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            <strong>워크플로우 2단계:</strong> TNSNames에서 등록한 DB를
            선택하고, <b>table_metadata.csv</b>와 <b>column_definitions.csv</b>
            를 업로드하여 메타정보를 생성합니다.
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
                <span className="text-sm text-muted-foreground">
                  데이터베이스 목록 로딩 중...
                </span>
              </div>
            ) : registeredDatabases.length === 0 ? (
              <Alert>
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  등록된 데이터베이스가 없습니다. TNSNames 페이지에서 먼저
                  데이터베이스를 등록해주세요.
                </AlertDescription>
              </Alert>
            ) : (
              <div className="space-y-4">
                <Select
                  value={selectedDbKey}
                  onValueChange={setSelectedDbKey}
                  disabled={isProcessing}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="데이터베이스 선택" />
                  </SelectTrigger>
                  <SelectContent>
                    {registeredDatabases.map((db) => {
                      const key = `${db.database_sid}:${db.schema_name}`;
                      return (
                        <SelectItem key={key} value={key}>
                          <div className="flex items-center justify-between w-full">
                            <span className="font-medium">
                              {db.database_sid}
                            </span>
                            <span className="text-xs text-muted-foreground ml-2">
                              ({db.schema_name})
                            </span>
                          </div>
                        </SelectItem>
                      );
                    })}
                  </SelectContent>
                </Select>

                {selectedDb && (
                  <div className="bg-primary/5 border border-primary/20 rounded-lg p-3">
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <p className="text-muted-foreground text-xs">
                          Database SID
                        </p>
                        <p className="font-medium">{selectedDb.database_sid}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground text-xs">Schema</p>
                        <p className="font-medium">{selectedDb.schema_name}</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground text-xs">
                          연결 상태
                        </p>
                        <p className="font-medium">
                          {selectedDb.is_connected ? "연결됨" : "연결 안됨"}
                        </p>
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
                Step 2: CSV 파일 업로드 (2종)
              </CardTitle>
              <CardDescription>
                테이블 정의서(table_metadata.csv)와 컬럼
                정의서(column_definitions.csv)를 업로드하세요
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4">
                {/* Table Metadata CSV */}
                <div className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <h4 className="font-medium text-sm">
                        1. 테이블 정보 (table_metadata.csv)
                      </h4>
                      <p className="text-xs text-muted-foreground">
                        테이블명, 한글명, 설명, 도메인, 키워드, 샘플 쿼리
                      </p>
                    </div>
                    {files.tableMetadata.file && (
                      <CheckCircle2 className="h-5 w-5 text-green-500" />
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleFileSelect("tableMetadata")}
                      disabled={isProcessing}
                    >
                      <Upload className="h-4 w-4 mr-2" />
                      {files.tableMetadata.file ? "다시 선택" : "파일 선택"}
                    </Button>
                    {files.tableMetadata.file && (
                      <span className="text-sm text-muted-foreground">
                        {files.tableMetadata.file.name}
                      </span>
                    )}
                  </div>
                </div>

                {/* Column Definitions CSV */}
                <div className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <h4 className="font-medium text-sm">
                        2. 컬럼/코드 정의 (column_definitions.csv)
                      </h4>
                      <p className="text-xs text-muted-foreground">
                        컬럼명, 한글명, 설명, 코드값(JSON)
                      </p>
                    </div>
                    {files.columnDefinitions.file && (
                      <CheckCircle2 className="h-5 w-5 text-green-500" />
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleFileSelect("columnDefinitions")}
                      disabled={isProcessing}
                    >
                      <Upload className="h-4 w-4 mr-2" />
                      {files.columnDefinitions.file ? "다시 선택" : "파일 선택"}
                    </Button>
                    {files.columnDefinitions.file && (
                      <span className="text-sm text-muted-foreground">
                        {files.columnDefinitions.file.name}
                      </span>
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
        {(isProcessing ||
          processingSteps.some((s) => s.status !== "pending")) && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Loader2
                  className={`h-5 w-5 ${isProcessing ? "animate-spin" : ""}`}
                />
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
                        <p className="text-xs text-muted-foreground mt-1">
                          {step.message}
                        </p>
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
  );
}
