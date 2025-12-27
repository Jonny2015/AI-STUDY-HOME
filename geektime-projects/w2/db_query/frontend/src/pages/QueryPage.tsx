import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import type { QueryResult as QueryResultType } from "../types";
import { NaturalLanguageInput } from "../components/NaturalLanguageInput";
import { SqlEditor } from "../components/SqlEditor";
import { QueryResult } from "../components/QueryResult";

export const QueryPage = () => {
  const { databaseName } = useParams<{ databaseName: string }>();
  const navigate = useNavigate();

  const [sql, setSql] = useState("");
  const [executing, setExecuting] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<QueryResultType | null>(null);

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

      {/* SQL Editor Card */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm">
        <div className="p-6">
          {/* SQL Editor */}
          <SqlEditor
            value={sql}
            onChange={setSql}
            onExecute={handleExecute}
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
