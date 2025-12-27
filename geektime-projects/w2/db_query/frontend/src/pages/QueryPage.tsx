import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useOne } from "@refinedev/core";
import type { QueryResult as QueryResultType, DatabaseMetadataResponse } from "../types";
import { NaturalLanguageInput } from "../components/NaturalLanguageInput";
import { SqlEditorWithAutocomplete } from "../components/SqlEditorWithAutocomplete";
import { QueryResult } from "../components/QueryResult";
import { MetadataViewer } from "../components/MetadataViewer";

export const QueryPage = () => {
  const { databaseName } = useParams<{ databaseName: string }>();
  const navigate = useNavigate();

  const [sql, setSql] = useState("");
  const [executing, setExecuting] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<QueryResultType | null>(null);
  const [metadataWidth, setMetadataWidth] = useState(25); // 默认25%
  const [isMetadataCollapsed, setIsMetadataCollapsed] = useState(false);

  // 获取数据库元数据用于自动完成
  const { result: metadata } = useOne<DatabaseMetadataResponse>({
    resource: "dbs",
    id: databaseName || "",
    queryOptions: {
      enabled: !!databaseName,
    },
  });

  const handleGenerateSQL = async (prompt: string) => {
    if (!databaseName) {
      setError("未选择数据库");
      return;
    }

    if (!prompt.trim()) {
      setError("请输入查询描述");
      return;
    }

    setGenerating(true);
    setError(null);

    try {
      const response = await fetch(`/api/v1/dbs/${databaseName}/query/natural`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        const errorMsg = errorData.detail || "生成 SQL 失败";

        // 友好提示
        if (errorMsg.includes("OpenAI API key")) {
          setError("AI 功能需要配置 OpenAI API 密钥。请在后端配置 OPENAI_API_KEY 环境变量，或直接使用 SQL 编辑器查询。");
        } else {
          setError(errorMsg);
        }
        return;
      }

      const data = await response.json();
      setSql(data.sql); // Populate the editor with generated SQL
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "生成 SQL 失败";
      setError(message);
    } finally {
      setGenerating(false);
    }
  };

  const handleExecute = async () => {
    if (!sql.trim()) {
      setError("请输入 SQL 查询");
      return;
    }

    if (!databaseName) {
      setError("未选择数据库");
      return;
    }

    setExecuting(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(`/api/v1/dbs/${databaseName}/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ sql }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "查询执行失败");
      }

      const data = await response.json();
      setResult(data);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "查询执行失败";
      setError(message);
    } finally {
      setExecuting(false);
    }
  };

  const handleToggleMetadata = () => {
    setIsMetadataCollapsed(!isMetadataCollapsed);
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    const startX = e.clientX;
    const startWidth = metadataWidth;

    const handleMouseMove = (e: MouseEvent) => {
      const containerWidth = window.innerWidth;
      const deltaX = e.clientX - startX;
      const deltaPercent = (deltaX / containerWidth) * 100;
      const newWidth = Math.max(15, Math.min(50, startWidth + deltaPercent)); // 限制在15%-50%
      setMetadataWidth(newWidth);
    };

    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  if (!databaseName) {
    return (
      <div className="p-8">
        <div className="bg-white rounded-xl p-12 border border-slate-200 shadow-sm text-center">
          <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-slate-800 mb-2">未选择数据库</h3>
          <p className="text-slate-600 mb-6">请先从左侧选择一个数据库</p>
          <button
            onClick={() => navigate("/")}
            className="inline-flex items-center px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
          >
            返回首页
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">SQL 查询</h1>
            <p className="mt-1 text-sm text-slate-600">
              数据库: <span className="font-semibold text-blue-600">{databaseName}</span>
            </p>
          </div>
        </div>
      </div>

      {/* Natural Language Input */}
      <NaturalLanguageInput
        onGenerate={handleGenerateSQL}
        disabled={executing || generating}
      />

      {/* Main Content: SQL Editor + Metadata Viewer with resizable divider */}
      <div className="flex gap-0 overflow-hidden rounded-xl border border-slate-200 shadow-sm bg-white relative">
        {/* SQL Editor - 可调整宽度 */}
        <div
          className="flex flex-col"
          style={{ width: isMetadataCollapsed ? '100%' : `${100 - metadataWidth}%` }}
        >
          <div className="p-6 flex-1">
            <h2 className="text-lg font-semibold text-slate-900 mb-4">SQL 编辑器</h2>

            {/* SQL Editor with Autocomplete */}
            <SqlEditorWithAutocomplete
              value={sql}
              onChange={setSql}
              onExecute={handleExecute}
              tables={metadata?.tables}
              disabled={executing || generating}
              placeholder="输入 SELECT 查询或使用上方 AI 生成..."
            />

            {/* Execute Button */}
            <div className="mt-4 flex items-center justify-between">
              <div className="text-sm text-slate-500 flex items-center">
                <svg className="w-4 h-4 mr-1 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                只允许 SELECT 查询，系统会自动添加 LIMIT 子句
              </div>
              <button
                onClick={handleExecute}
                disabled={executing || generating || !sql.trim()}
                className="inline-flex items-center px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
              >
                {executing ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    执行中...
                  </>
                ) : (
                  <>
                    <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    执行查询
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* 分隔线和按钮容器 - 始终显示 */}
        <div className="relative flex-shrink-0">
          {/* 可拖动分隔线 */}
          <div
            className={`w-1 transition-colors duration-200 ${
              isMetadataCollapsed
                ? 'bg-slate-300'
                : 'bg-slate-200 hover:bg-blue-400 cursor-col-resize'
            }`}
            onMouseDown={handleMouseDown}
          />

          {/* 收缩/展开按钮 - 在分隔线中央 */}
          <button
            onClick={handleToggleMetadata}
            className={`absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-10 w-7 h-7 rounded-lg flex items-center justify-center shadow-md border-2 transition-all duration-200 ${
              isMetadataCollapsed
                ? 'bg-blue-500 border-blue-600 hover:bg-blue-600 hover:scale-110'
                : 'bg-white border-slate-300 hover:bg-slate-50 hover:scale-110'
            }`}
            title={isMetadataCollapsed ? "展开数据库结构" : "收缩数据库结构"}
          >
            {isMetadataCollapsed ? (
              // 展开图标 - 双箭头向左
              <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M11 19l-7-7 7-7m8 0l-7-7 7-7" />
              </svg>
            ) : (
              // 收缩图标 - 单箭头向左
              <svg className="w-4 h-4 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M15 19l-7-7 7-7" />
              </svg>
            )}
          </button>

          {/* 悬停提示条 - 拖动时显示 */}
          {!isMetadataCollapsed && (
            <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-8 h-1 bg-blue-400 opacity-0 hover:opacity-100 transition-opacity" />
          )}
        </div>

        {/* Metadata Viewer - 可调整宽度,支持收缩 */}
        <div
          className={`relative flex-shrink-0 overflow-hidden transition-all duration-300 ease-in-out border-l border-slate-200 ${
            isMetadataCollapsed ? 'w-0' : ''
          }`}
          style={isMetadataCollapsed ? {} : { width: `${metadataWidth}%` }}
        >
          <div className="h-full overflow-auto">
            <MetadataViewer databaseName={databaseName || ""} />
          </div>
        </div>
      </div>

      {/* Query Result */}
      <QueryResult
        result={result}
        loading={executing}
        error={error}
        databaseName={databaseName}
        sql={sql}
      />
    </div>
  );
};
