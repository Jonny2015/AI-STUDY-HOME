import React, { useState } from "react";
import { useOne } from "@refinedev/core";
import type { DatabaseMetadataResponse } from "../types";

interface MetadataViewerProps {
  databaseName: string;
}

export const MetadataViewer: React.FC<MetadataViewerProps> = ({ databaseName }) => {
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  // Fetch metadata
  const { data, isLoading, refetch } = useOne<DatabaseMetadataResponse>({
    resource: "dbs",
    id: databaseName,
    queryOptions: {
      enabled: !!databaseName,
    },
  });

  const metadata = data?.data;

  const handleRefresh = async () => {
    setRefreshing(true);
    setError("");
    try {
      // Force refresh by adding refresh parameter
      await refetch();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "刷新元数据失败";
      setError(message);
    } finally {
      setRefreshing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white shadow rounded-lg p-6">
        <div className="text-center py-8">加载元数据中...</div>
      </div>
    );
  }

  if (!metadata || !metadata.tables || metadata.tables.length === 0) {
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
              d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0 2.21-3.582 4-8 4s-8-1.79-8-4"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">暂无元数据</h3>
          <p className="mt-1 text-sm text-gray-500">
            选择一个数据库查看其结构
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-medium text-gray-900">
          数据库结构
        </h3>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
        >
          <svg
            className={`-ml-0.5 mr-2 h-4 w-4 ${refreshing ? "animate-spin" : ""}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          刷新
        </button>
      </div>

      {error && (
        <div className="mb-4 rounded-md bg-red-50 p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      <div className="space-y-4">
        {metadata.tables.map((table) => (
          <details
            key={`${table.schemaName}.${table.tableName}`}
            className="border border-gray-200 rounded-lg"
          >
            <summary className="cursor-pointer px-4 py-3 bg-gray-50 hover:bg-gray-100 rounded-lg flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <span className="font-medium text-gray-900">
                  {table.tableName}
                </span>
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                    table.tableType === "table"
                      ? "bg-blue-100 text-blue-800"
                      : "bg-purple-100 text-purple-800"
                  }`}
                >
                  {table.tableType === "table" ? "表" : "视图"}
                </span>
                <span className="text-sm text-gray-500">
                  {table.schemaName}
                </span>
              </div>
              <span className="text-gray-500">
                {table.columns.length} 列
              </span>
            </summary>

            <div className="px-4 py-3 border-t border-gray-200">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      列名
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      类型
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      可空
                    </th>
                    <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                      主键
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {table.columns.map((column, idx) => (
                    <tr key={idx}>
                      <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                        {column.columnName}
                        {column.isPrimaryKey && (
                          <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
                            PK
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500">
                        {column.dataType}
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500">
                        {column.isNullable ? "是" : "否"}
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500">
                        {column.isPrimaryKey ? "是" : "否"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        ))}
      </div>
    </div>
  );
};
