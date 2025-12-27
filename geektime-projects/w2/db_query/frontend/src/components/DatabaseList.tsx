import React from "react";
import { useList } from "@refinedev/core";
import type { Database } from "../types";

interface DatabaseListProps {
  onSelect?: (databaseName: string) => void;
  onQuery?: (databaseName: string) => void;
}

export const DatabaseList: React.FC<DatabaseListProps> = ({ onSelect, onQuery }) => {
  const { query, result } = useList<Database>({
    resource: "dbs",
  });

  // Handle different possible data structures from Refine
  const databases = Array.isArray(result?.data)
    ? result.data
    : (result?.data as any)?.data || [];

  // Debug: log the data structure
  console.log("useList result:", result);
  console.log("databases:", databases);
  console.log("query.isLoading:", query.isLoading);
  console.log("query.isError:", query.isError);

  if (query.isLoading) {
    return (
      <div className="text-center py-8 flex items-center justify-center space-x-2">
        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-sky-500"></div>
        <span className="text-gray-600">加载中...</span>
      </div>
    );
  }

  if (query.isError) {
    return (
      <div className="text-center py-8 text-red-500 flex items-center justify-center space-x-2">
        <svg
          className="w-5 h-5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <span>加载数据库列表失败</span>
      </div>
    );
  }

  console.log("databases.length:", databases.length);

  if (databases.length === 0) {
    return (
      <div className="text-center py-12 bg-white/50 backdrop-blur-sm rounded-xl border border-sky-100">
        <div className="mx-auto h-16 w-16 bg-gradient-to-br from-sky-100 to-blue-100 rounded-full flex items-center justify-center mb-4">
          <svg
            className="h-8 w-8 text-sky-500"
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
        </div>
        <h3 className="mt-2 text-sm font-semibold text-gray-800">暂无数据库</h3>
        <p className="mt-1 text-sm text-gray-500">
          点击顶部按钮添加第一个数据库连接
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white/50 backdrop-blur-sm shadow-sm rounded-xl overflow-hidden border border-sky-100">
      <ul className="divide-y divide-sky-100">
        {databases.map((db: Database) => (
          <li key={db.databaseName}>
            <div
              className={`px-4 py-4 sm:px-6 cursor-pointer hover:bg-sky-50/50 transition-all duration-200 ${
                onSelect ? "cursor-pointer" : ""
              }`}
              onClick={() => onSelect?.(db.databaseName)}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <div className="w-8 h-8 bg-gradient-to-br from-sky-400 to-blue-500 rounded-lg flex items-center justify-center">
                      <svg
                        className="w-4 h-4 text-white"
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
                    </div>
                    <p className="text-sm font-semibold text-sky-700 truncate">
                      {db.databaseName}
                    </p>
                  </div>
                  <p className="mt-2 flex items-center text-sm space-x-2">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-sky-100 text-sky-700">
                      {db.dbType}
                    </span>
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        db.connectionStatus === "connected"
                          ? "bg-emerald-100 text-emerald-700"
                          : "bg-red-100 text-red-700"
                      }`}
                    >
                      {db.connectionStatus === "connected" ? "已连接" : "未连接"}
                    </span>
                  </p>
                </div>
                <div className="ml-4 flex-shrink-0 flex items-center space-x-2">
                  {onSelect && (
                    <button
                      type="button"
                      className="px-3 py-1.5 text-sky-600 hover:text-sky-700 hover:bg-sky-50 rounded-lg text-sm font-medium transition-colors duration-200"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelect(db.databaseName);
                      }}
                    >
                      查看
                    </button>
                  )}
                  {onQuery && (
                    <button
                      type="button"
                      className="px-3 py-1.5 text-emerald-600 hover:text-emerald-700 hover:bg-emerald-50 rounded-lg text-sm font-medium transition-colors duration-200"
                      onClick={(e) => {
                        e.stopPropagation();
                        onQuery(db.databaseName);
                      }}
                    >
                      查询
                    </button>
                  )}
                  <button
                    type="button"
                    className="px-3 py-1.5 text-red-500 hover:text-red-600 hover:bg-red-50 rounded-lg text-sm transition-colors duration-200"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(db.databaseName);
                    }}
                  >
                    删除
                  </button>
                </div>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );

  function handleDelete(name: string) {
    if (window.confirm(`确定要删除数据库 "${name}" 吗？`)) {
      console.log("Deleting database:", name);
      // TODO: Implement delete functionality
    }
  }
};
