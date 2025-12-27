import { useState } from "react";
import { useCustom } from "@refinedev/core";
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

  const { refetch } = useCustom<QueryResultType>({
    url: `/api/v1/dbs/${databaseName}/query`,
    method: "post",
    config: {
      payload: { sql },
    },
    queryOptions: {
      enabled: false, // Don't fetch on mount
    },
  });

  const handleGenerateSQL = async (prompt: string) => {
    if (!databaseName) {
      setError("未选择数据库");
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
        throw new Error(errorData.detail || "生成 SQL 失败");
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
      const response = await refetch();
      if (response?.data?.data) {
        setResult(response.data.data);
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "查询执行失败";
      setError(message);
    } finally {
      setExecuting(false);
    }
  };

  if (!databaseName) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-center py-12">
          <h3 className="text-lg font-medium text-gray-900">未选择数据库</h3>
          <p className="mt-2 text-sm text-gray-500">
            请先从主页选择一个数据库
          </p>
          <button
            onClick={() => navigate("/")}
            className="mt-4 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700"
          >
            返回主页
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Natural Language Input */}
      <NaturalLanguageInput
        onGenerate={handleGenerateSQL}
        disabled={executing || generating}
      />

      {/* Header */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">SQL 查询</h1>
            <p className="mt-1 text-sm text-gray-500">
              数据库: <span className="font-medium text-indigo-600">{databaseName}</span>
            </p>
          </div>
          <button
            onClick={() => navigate("/")}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            <svg
              className="-ml-1 mr-2 h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M10 19l-7-7m0 0l7-7m-7 7h18"
              />
            </svg>
            返回
          </button>
        </div>

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
          <div className="text-sm text-gray-500">
            提示: 只允许 SELECT 查询,系统会自动添加 LIMIT 子句
          </div>
          <button
            onClick={handleExecute}
            disabled={executing || generating || !sql.trim()}
            className="inline-flex items-center px-6 py-3 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {executing ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                执行中...
              </>
            ) : (
              <>
                <svg
                  className="-ml-1 mr-2 h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                执行查询
              </>
            )}
          </button>
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
