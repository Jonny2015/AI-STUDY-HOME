import { useNavigate } from "react-router-dom";
import { useList } from "@refinedev/core";
import type { Database } from "../types";
import { DatabaseList } from "../components/DatabaseList";

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

  const handleQuery = (databaseName: string) => {
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
      <DatabaseList
        onSelect={handleDatabaseClick}
        onQuery={handleQuery}
      />
    </div>
  );
};
