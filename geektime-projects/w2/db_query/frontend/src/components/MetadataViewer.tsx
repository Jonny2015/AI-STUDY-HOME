import React, { useState, useMemo } from "react";
import { useOne } from "@refinedev/core";
import type { DatabaseMetadataResponse, TableMetadata } from "../types";

interface MetadataViewerProps {
  databaseName: string;
}

// 按schema分组表结构
interface SchemaGroup {
  schemaName: string;
  tables: TableMetadata[];
}

export const MetadataViewer: React.FC<MetadataViewerProps> = ({ databaseName }) => {
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [expandedSchemas, setExpandedSchemas] = useState<Set<string>>(new Set(["public"]));

  // Fetch metadata
  const { query, result } = useOne<DatabaseMetadataResponse>({
    resource: "dbs",
    id: databaseName,
    queryOptions: {
      enabled: !!databaseName,
    },
  });

  const metadata = result;

  // 按schema分组并排序
  const groupedData = useMemo(() => {
    if (!metadata?.tables) return [];

    const schemaMap = new Map<string, TableMetadata[]>();

    metadata.tables.forEach(table => {
      const schema = table.schemaName || "public";
      if (!schemaMap.has(schema)) {
        schemaMap.set(schema, []);
      }
      schemaMap.get(schema)!.push(table);
    });

    // 转换为数组并排序
    const groups: SchemaGroup[] = Array.from(schemaMap.entries())
      .map(([schemaName, tables]) => ({
        schemaName,
        tables: tables.sort((a, b) => a.tableName.localeCompare(b.tableName))
      }))
      .sort((a, b) => {
        // public schema 排在第一位
        if (a.schemaName === "public") return -1;
        if (b.schemaName === "public") return 1;
        return a.schemaName.localeCompare(b.schemaName);
      });

    return groups;
  }, [metadata]);

  // 过滤表和列
  const filteredGroups = useMemo(() => {
    if (!searchTerm) return groupedData;

    const lowerSearch = searchTerm.toLowerCase();

    return groupedData
      .map(group => ({
        ...group,
        tables: group.tables.filter(table => {
          // 搜索表名
          if (table.tableName.toLowerCase().includes(lowerSearch)) return true;

          // 搜索列名
          return table.columns.some(col =>
            col.columnName.toLowerCase().includes(lowerSearch)
          );
        })
      }))
      .filter(group => group.tables.length > 0);
  }, [groupedData, searchTerm]);

  const handleRefresh = async () => {
    setRefreshing(true);
    setError("");
    try {
      await query.refetch();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "刷新元数据失败";
      setError(message);
    } finally {
      setRefreshing(false);
    }
  };

  const toggleSchema = (schemaName: string) => {
    setExpandedSchemas(prev => {
      const newSet = new Set(prev);
      if (newSet.has(schemaName)) {
        newSet.delete(schemaName);
      } else {
        newSet.add(schemaName);
      }
      return newSet;
    });
  };

  if (query.isLoading) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <div className="text-center py-8 text-slate-600">加载元数据中...</div>
      </div>
    );
  }

  if (!metadata || !metadata.tables || metadata.tables.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <div className="text-center py-12">
          <svg
            className="mx-auto h-12 w-12 text-slate-400"
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
          <h3 className="mt-2 text-sm font-medium text-slate-900">暂无元数据</h3>
          <p className="mt-1 text-sm text-slate-500">
            选择一个数据库查看其结构
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white h-full flex flex-col overflow-hidden">
      {/* Header - 极简紧凑 */}
      <div className="flex justify-between items-center px-2.5 py-2 border-b border-slate-200 bg-slate-50/50 flex-shrink-0">
        <div className="flex items-center gap-1.5">
          <h3 className="text-xs font-semibold text-slate-700">数据库结构</h3>
          <span className="inline-flex items-center px-1 py-0.5 rounded-full text-[10px] font-medium bg-blue-100 text-blue-700">
            {metadata?.tables.length || 0}
          </span>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="inline-flex items-center px-1.5 py-0.5 text-xs text-slate-600 hover:bg-slate-200 rounded disabled:opacity-50 transition-colors"
        >
          <svg
            className={`w-3 h-3 ${refreshing ? "animate-spin" : ""}`}
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
        </button>
      </div>

      {/* 搜索框 - 极简 */}
      <div className="px-2 py-1.5 border-b border-slate-200 flex-shrink-0">
        <div className="relative">
          <input
            type="text"
            placeholder="搜索..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-6 pr-2 py-1 text-xs border border-slate-200 rounded focus:ring-1 focus:ring-blue-400 focus:border-blue-400 bg-white"
          />
          <svg
            className="absolute left-1.5 top-1/2 transform -translate-y-1/2 h-3 w-3 text-slate-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
      </div>

      {error && (
        <div className="mx-2 mt-1 rounded bg-red-50 px-2 py-1 flex-shrink-0">
          <p className="text-[10px] text-red-700">{error}</p>
        </div>
      )}

      {/* 树形结构展示 - 可滚动 */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden">
        <div className="py-0.5 space-y-0.5">
          {filteredGroups.length === 0 ? (
            <div className="text-center py-4 text-slate-500 text-xs">
              未找到匹配的表或字段
            </div>
          ) : (
            filteredGroups.map((group) => (
              <div key={group.schemaName} className="border border-slate-200 rounded overflow-hidden">
                {/* Schema 头部 - 极简 */}
                <div
                  className="px-2 py-1 bg-gradient-to-r from-slate-50 to-slate-100 border-b border-slate-200 flex items-center gap-1 cursor-pointer hover:from-blue-50 hover:to-blue-100 transition-colors"
                  onClick={() => toggleSchema(group.schemaName)}
                >
                  <svg
                    className={`w-3 h-3 text-slate-500 transition-transform flex-shrink-0 ${
                      expandedSchemas.has(group.schemaName) ? "rotate-90" : ""
                    }`}
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <span className="font-semibold text-slate-700 text-xs truncate">
                    {group.schemaName}
                  </span>
                  <span className="text-[10px] text-slate-500 flex-shrink-0">
                    {group.tables.length}
                  </span>
                </div>

                {/* 表列表 - 极简 */}
                {expandedSchemas.has(group.schemaName) && (
                  <div className="divide-y divide-slate-100 bg-white">
                    {group.tables.map((table) => (
                      <details
                        key={`${group.schemaName}.${table.tableName}`}
                        className="group"
                        open={searchTerm.length > 0}
                      >
                        <summary className="cursor-pointer px-2 py-1 hover:bg-blue-50/50 transition-colors flex items-center gap-1 select-none">
                          <svg
                            className="w-3 h-3 text-slate-400 group-open:text-blue-500 transition-colors flex-shrink-0"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
                            />
                          </svg>
                          <span className="font-medium text-slate-900 text-xs truncate flex-1 min-w-0">
                            {table.tableName}
                          </span>
                          <span className="text-[10px] text-slate-500 flex-shrink-0">
                            {table.columns.length}
                          </span>
                        </summary>

                        {/* 字段列表 - 不限制高度,使用外层滚动 */}
                        <div className="bg-slate-50/30">
                          <div className="divide-y divide-slate-100">
                            {table.columns.map((column, idx) => (
                              <div
                                key={idx}
                                className="flex items-center gap-1 px-2 py-0.75 hover:bg-blue-50/70 transition-colors group/col"
                              >
                                {column.isPrimaryKey && (
                                  <svg
                                    className="w-2.5 h-2.5 text-yellow-500 flex-shrink-0"
                                    fill="currentColor"
                                    viewBox="0 0 20 20"
                                  >
                                    <path
                                      fillRule="evenodd"
                                      d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z"
                                      clipRule="evenodd"
                                    />
                                  </svg>
                                )}
                                <span className="font-mono text-xs text-slate-800 truncate flex-1 min-w-0" title={column.columnName}>
                                  {column.columnName}
                                </span>
                                <div className="flex items-center gap-0.5 flex-shrink-0">
                                  <span className="text-[10px] text-slate-500 bg-white px-1 py-0.5 rounded font-mono border border-slate-200" title={column.dataType}>
                                    {column.dataType.length > 6 ? column.dataType.substring(0, 6) + '…' : column.dataType}
                                  </span>
                                  {!column.isNullable && (
                                    <span className="text-[10px] text-red-600 bg-red-50 px-1 py-0.5 rounded border border-red-200">
                                      ∅
                                    </span>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </details>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
