import React, { useState } from "react";
import type { QueryResult as QueryResultType } from "../types";

interface QueryResultProps {
  result: QueryResultType | null;
  loading: boolean;
  error: string | null;
  databaseName?: string;
  sql?: string;
}

export const QueryResult: React.FC<QueryResultProps> = ({
  result,
  loading,
  error,
  databaseName,
  sql
}) => {
  const [currentPage, setCurrentPage] = useState(0);
  const [exporting, setExporting] = useState(false);
  const pageSize = 50;

  const handleExport = async () => {
    if (!databaseName || !sql) return;

    setExporting(true);
    try {
      const response = await fetch(`/api/v1/dbs/${databaseName}/query/export`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ sql }),
      });

      if (!response.ok) {
        throw new Error("导出失败");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `query_result_${databaseName}_${Date.now()}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error("Export failed:", err);
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-center py-8">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          <p className="mt-2 text-sm text-gray-600">执行查询中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="rounded-md bg-red-50 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-red-400"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">查询失败</h3>
              <p className="mt-1 text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-center py-12">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">暂无结果</h3>
          <p className="mt-1 text-sm text-gray-500">
            在上方输入 SQL 查询并点击执行
          </p>
        </div>
      </div>
    );
  }

  if (result.rowCount === 0) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-center py-12">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414-2.414a1 1 0 01-.293-.707V5.414a1 1 0 01.293-.707l5.414-5.414a1 1 0 011.414 0l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">无数据</h3>
          <p className="mt-1 text-sm text-gray-500">
            查询执行成功,但未返回任何结果
          </p>
        </div>
      </div>
    );
  }

  // Pagination
  const totalPages = Math.ceil(result.rowCount / pageSize);
  const paginatedRows = result.rows.slice(
    currentPage * pageSize,
    (currentPage + 1) * pageSize
  );

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
        <div className="flex items-center space-x-4 text-sm text-gray-600">
          <span>
            返回 <span className="font-medium text-gray-900">{result.rowCount}</span> 行
          </span>
          <span>•</span>
          <span>
            耗时 <span className="font-medium text-gray-900">{result.executionTimeMs}</span> ms
          </span>
        </div>
        {databaseName && sql && (
          <button
            onClick={handleExport}
            disabled={exporting}
            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            {exporting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-500 mr-2"></div>
                导出中...
              </>
            ) : (
              <>
                <svg
                  className="-ml-0.5 mr-2 h-4 w-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                  />
                </svg>
                导出 CSV
              </>
            )}
          </button>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {result.columns.map((column) => (
                <th
                  key={column}
                  className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {paginatedRows.map((row, idx) => (
              <tr key={idx} className="hover:bg-gray-50">
                {result.columns.map((column) => (
                  <td
                    key={column}
                    className="px-4 py-3 whitespace-nowrap text-sm text-gray-900"
                  >
                    {formatValue(row[column])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="px-4 py-3 border-t border-gray-200 bg-gray-50 flex items-center justify-between">
          <div className="text-sm text-gray-600">
            显示第 {currentPage * pageSize + 1} 到{" "}
            {Math.min((currentPage + 1) * pageSize, result.rowCount)} 条，共{" "}
            {result.rowCount} 条
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => setCurrentPage((p) => Math.max(0, p - 1))}
              disabled={currentPage === 0}
              className="px-3 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
            >
              上一页
            </button>
            <span className="px-3 py-1 text-sm text-gray-600">
              第 {currentPage + 1} / {totalPages} 页
            </span>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={currentPage >= totalPages - 1}
              className="px-3 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
            >
              下一页
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

function formatValue(value: unknown): string {
  if (value === null) return "NULL";
  if (value === undefined) return "";
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
