import React from "react";
import { useList } from "@refinedev/core";
import type { Database } from "../types";

interface DatabaseListProps {
  onSelect?: (databaseName: string) => void;
  onQuery?: (databaseName: string) => void;
}

export const DatabaseList: React.FC<DatabaseListProps> = ({ onSelect, onQuery }) => {
  const { data, isLoading, isError } = useList<Database>({
    resource: "dbs",
  });

  // Debug: log the data structure
  console.log("useList data:", data);
  console.log("data?.data:", data?.data);
  console.log("isLoading:", isLoading);
  console.log("isError:", isError);

  if (isLoading) {
    return <div className="text-center py-8">加载中...</div>;
  }

  if (isError) {
    return (
      <div className="text-center py-8 text-red-600">
        加载数据库列表失败
      </div>
    );
  }

  // Try different ways to access the array
  const databases = Array.isArray(data) ? data : (Array.isArray(data?.data) ? data.data : []);

  console.log("databases:", databases);
  console.log("databases.length:", databases.length);

  if (databases.length === 0) {
    return (
      <div className="text-center py-12 bg-white rounded-lg shadow">
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
        <h3 className="mt-2 text-sm font-medium text-gray-900">暂无数据库</h3>
        <p className="mt-1 text-sm text-gray-500">
          点击下方按钮添加第一个数据库连接
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      <ul className="divide-y divide-gray-200">
        {databases.map((db) => (
          <li key={db.databaseName}>
            <div
              className={`px-4 py-4 sm:px-6 cursor-pointer hover:bg-gray-50 transition-colors ${
                onSelect ? "cursor-pointer" : ""
              }`}
              onClick={() => onSelect?.(db.databaseName)}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <p className="text-sm font-medium text-indigo-600 truncate">
                    {db.databaseName}
                  </p>
                  <p className="mt-1 flex items-center text-sm text-gray-500">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800 mr-2">
                      {db.dbType}
                    </span>
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                        db.connectionStatus === "connected"
                          ? "bg-green-100 text-green-800"
                          : "bg-red-100 text-red-800"
                      }`}
                    >
                      {db.connectionStatus}
                    </span>
                  </p>
                </div>
                <div className="ml-4 flex-shrink-0 flex items-center space-x-2">
                  {onSelect && (
                    <button
                      type="button"
                      className="text-indigo-600 hover:text-indigo-900 text-sm font-medium"
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
                      className="text-green-600 hover:text-green-900 text-sm font-medium"
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
                    className="text-red-600 hover:text-red-900 text-sm"
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
