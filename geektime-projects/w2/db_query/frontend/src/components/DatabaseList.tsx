import React, { useState } from "react";
import { useList, useDelete } from "@refinedev/core";
import type { Database } from "../types";

interface DatabaseListProps {
  onSelect?: (databaseName: string) => void;
  onQuery?: (databaseName: string) => void;
  onEdit?: (database: Database) => void;
}

export const DatabaseList: React.FC<DatabaseListProps> = ({ onSelect, onQuery, onEdit }) => {
  const { query, result } = useList<Database>({
    resource: "dbs",
  });

  const [editingDb, setEditingDb] = useState<Database | null>(null);
  const [editUrl, setEditUrl] = useState("");

  // Delete mutation
  const { mutate: deleteDb } = useDelete();

  // Handle different possible data structures from Refine
  const databases = Array.isArray(result?.data)
    ? result.data
    : (result?.data as any)?.data || [];

  // Handle delete
  const handleDelete = async (name: string) => {
    if (window.confirm(`确定要删除数据库 "${name}" 吗？此操作将同时删除所有相关的元数据缓存。`)) {
      try {
        await deleteDb(
          { resource: "dbs", id: name },
          {
            onSuccess: () => {
              // Refetch the list
              query.refetch();
            },
          }
        );
      } catch (error) {
        console.error("删除失败:", error);
        alert("删除数据库失败,请重试");
      }
    }
  };

  // Handle edit
  const handleEdit = (db: Database) => {
    setEditingDb(db);
    setEditUrl(db.url || "");
  };

  // Handle save edit
  const handleSaveEdit = async () => {
    if (!editingDb || !editUrl.trim()) {
      alert("请输入数据库连接URL");
      return;
    }

    try {
      const response = await fetch(`/api/v1/dbs/${editingDb.databaseName}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: editUrl }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "更新失败");
      }

      // Success
      setEditingDb(null);
      setEditUrl("");
      query.refetch();
    } catch (error: any) {
      alert(error.message || "更新数据库失败");
    }
  };

  // Handle cancel edit
  const handleCancelEdit = () => {
    setEditingDb(null);
    setEditUrl("");
  };

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
            {editingDb?.databaseName === db.databaseName ? (
              // 编辑模式
              <div className="px-4 py-4 sm:px-6 bg-sky-50/50">
                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-medium text-sky-700 mb-1">
                      数据库名称
                    </label>
                    <input
                      type="text"
                      value={editingDb.databaseName}
                      disabled
                      className="w-full px-3 py-2 text-sm border border-sky-200 rounded-lg bg-gray-100 cursor-not-allowed"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-sky-700 mb-1">
                      数据库连接URL
                    </label>
                    <input
                      type="text"
                      value={editUrl}
                      onChange={(e) => setEditUrl(e.target.value)}
                      placeholder="postgresql://user:password@host:port/database"
                      className="w-full px-3 py-2 text-sm border border-sky-200 rounded-lg focus:ring-2 focus:ring-sky-400 focus:border-sky-400"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleSaveEdit}
                      className="px-4 py-2 text-sm font-medium text-white bg-sky-500 hover:bg-sky-600 rounded-lg transition-colors"
                    >
                      保存
                    </button>
                    <button
                      onClick={handleCancelEdit}
                      className="px-4 py-2 text-sm font-medium text-sky-600 hover:bg-sky-50 rounded-lg transition-colors"
                    >
                      取消
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              // 显示模式
              <div
                className={`px-4 py-4 sm:px-6 hover:bg-sky-50/50 transition-all duration-200`}
              >
                <div className="flex items-center justify-between">
                  <div
                    className="flex-1 cursor-pointer"
                    onClick={() => onSelect?.(db.databaseName)}
                  >
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
                  <div className="ml-4 flex-shrink-0 flex items-center space-x-1">
                    {onSelect && (
                      <button
                        type="button"
                        className="p-2 text-sky-600 hover:text-sky-700 hover:bg-sky-50 rounded-lg transition-colors duration-200 group/btn relative"
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelect(db.databaseName);
                        }}
                        title="查看"
                      >
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                        <span className="absolute invisible group-hover/btn:visible z-10 px-2 py-1 text-xs text-white bg-slate-800 rounded whitespace-nowrap bottom-full left-1/2 transform -translate-x-1/2 mb-1">
                          查看
                        </span>
                      </button>
                    )}
                    <button
                      type="button"
                      className="p-2 text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors duration-200 group/btn relative"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleEdit(db);
                      }}
                      title="编辑"
                    >
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                      <span className="absolute invisible group-hover/btn:visible z-10 px-2 py-1 text-xs text-white bg-slate-800 rounded whitespace-nowrap bottom-full left-1/2 transform -translate-x-1/2 mb-1">
                        编辑
                      </span>
                    </button>
                    <button
                      type="button"
                      className="p-2 text-red-500 hover:text-red-600 hover:bg-red-50 rounded-lg text-sm transition-colors duration-200 group/btn relative"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(db.databaseName);
                      }}
                      title="删除"
                    >
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                      <span className="absolute invisible group-hover/btn:visible z-10 px-2 py-1 text-xs text-white bg-slate-800 rounded whitespace-nowrap bottom-full left-1/2 transform -translate-x-1/2 mb-1">
                        删除
                      </span>
                    </button>
                  </div>
                </div>
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
};
