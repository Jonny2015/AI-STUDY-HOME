import { useNavigate } from "react-router-dom";
import { useList } from "@refinedev/core";
import type { Database } from "../types";

export const Dashboard = () => {
  const navigate = useNavigate();

  const { query, result } = useList<Database>({
    resource: "dbs",
  });

  const databases = Array.isArray(result?.data)
    ? result.data
    : (result?.data as any)?.data || [];

  const handleDatabaseClick = (databaseName: string) => {
    navigate(`/query/${databaseName}`);
  };

  return (
    <div className="space-y-8">
      {/* 页面头部 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-slate-900">数据库管理</h2>
          <p className="mt-2 text-slate-600">管理您的数据库连接并执行查询</p>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
        <div className="relative overflow-hidden rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
          <div className="flex items-center gap-4">
            <div className="rounded-xl bg-violet-50 p-3">
              <svg className="h-6 w-6 text-violet-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
              </svg>
            </div>
            <div>
              <p className="text-sm text-slate-600">总数据库</p>
              <p className="mt-1 text-2xl font-semibold text-slate-900">{databases.length}</p>
            </div>
          </div>
        </div>

        <div className="relative overflow-hidden rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
          <div className="flex items-center gap-4">
            <div className="rounded-xl bg-emerald-50 p-3">
              <svg className="h-6 w-6 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <p className="text-sm text-slate-600">已连接</p>
              <p className="mt-1 text-2xl font-semibold text-slate-900">
                {databases.filter((db: Database) => db.connectionStatus === "connected").length}
              </p>
            </div>
          </div>
        </div>

        <div className="relative overflow-hidden rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
          <div className="flex items-center gap-4">
            <div className="rounded-xl bg-amber-50 p-3">
              <svg className="h-6 w-6 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <p className="text-sm text-slate-600">支持类型</p>
              <p className="mt-1 text-2xl font-semibold text-slate-900">2</p>
            </div>
          </div>
        </div>
      </div>

      {/* 数据库列表 */}
      <div className="rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
        {/* 表头 */}
        <div className="border-b border-slate-200 px-6 py-5">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-slate-900">数据库列表</h3>
            <span className="text-sm text-slate-500">{databases.length} 个数据库</span>
          </div>
        </div>

        {/* 列表内容 */}
        <div>
          {query.isLoading ? (
            <div className="flex flex-col items-center justify-center py-16">
              <div className="h-10 w-10 animate-spin rounded-full border-4 border-violet-200 border-t-violet-600"></div>
              <p className="mt-4 text-sm text-slate-600">加载中...</p>
            </div>
          ) : databases.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16">
              <div className="mb-4 rounded-2xl bg-slate-50 p-6">
                <svg className="h-16 w-16 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414-2.414a1 1 0 01-.293-.707V5.414a1 1 0 01.293-.707l5.414-5.414a1 1 0 011.414 0l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h4 className="text-lg font-semibold text-slate-900">暂无数据库</h4>
              <p className="mt-2 text-sm text-slate-600 max-w-sm text-center">
                点击右上角"添加数据库"按钮，创建您的第一个数据库连接
              </p>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {databases.map((db: Database) => (
                <div
                  key={db.databaseName}
                  onClick={() => handleDatabaseClick(db.databaseName)}
                  className="group cursor-pointer px-6 py-5 transition-all hover:bg-violet-50"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4 flex-1 min-w-0">
                      {/* 图标 */}
                      <div className="flex-shrink-0">
                        <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 p-2.5 shadow-lg shadow-violet-200">
                          <svg className="h-full w-full text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                          </svg>
                        </div>
                      </div>

                      {/* 信息 */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="text-base font-semibold text-slate-900 truncate">{db.databaseName}</h4>
                          <span className="inline-flex items-center rounded-full bg-violet-50 px-2.5 py-1 text-xs font-semibold text-violet-700 ring-1 ring-inset ring-violet-200">
                            {db.dbType}
                          </span>
                          <span
                            className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ${
                              db.connectionStatus === "connected"
                                ? "bg-emerald-50 text-emerald-700 ring-emerald-200"
                                : "bg-red-50 text-red-700 ring-red-200"
                            }`}
                          >
                            {db.connectionStatus === "connected" ? "已连接" : "未连接"}
                          </span>
                        </div>
                        <p className="text-sm text-slate-500">
                          创建于 {db.createdAt ? new Date(db.createdAt).toLocaleDateString("zh-CN") : "N/A"}
                        </p>
                      </div>
                    </div>

                    {/* 箭头 */}
                    <div className="flex-shrink-0 ml-4">
                      <div className="h-10 w-10 rounded-full bg-slate-100 flex items-center justify-center group-hover:bg-violet-100 transition-colors">
                        <svg className="h-5 w-5 text-slate-400 group-hover:text-violet-600 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
