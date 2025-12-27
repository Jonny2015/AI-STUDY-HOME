import { useState } from "react";
import { Routes, Route, useLocation, useNavigate } from "react-router-dom";
import { useInvalidate } from "@refinedev/core";
import { Dashboard } from "./pages/Dashboard";
import { QueryPage } from "./pages/QueryPage";
import { AddDatabaseModal } from "./components/AddDatabaseModal";

function App() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const invalidate = useInvalidate();
  const location = useLocation();
  const navigate = useNavigate();

  const handleSuccess = () => {
    invalidate({
      resource: "dbs",
      invalidates: ["list"],
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* 顶部导航栏 */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-lg border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            {/* Logo和品牌 */}
            <div className="flex items-center gap-8">
              <button
                onClick={() => navigate("/")}
                className="flex items-center gap-3 hover:opacity-80 transition-opacity"
              >
                <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg shadow-violet-200">
                  <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                  </svg>
                </div>
                <div>
                  <h1 className="text-xl font-bold text-slate-800">DB Query</h1>
                  <p className="text-xs text-slate-500">智能数据库查询</p>
                </div>
              </button>

              {/* 导航链接 */}
              <nav className="hidden md:flex items-center gap-1">
                <button
                  onClick={() => navigate("/")}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    location.pathname === "/"
                      ? "bg-violet-50 text-violet-700"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                  }`}
                >
                  首页
                </button>
              </nav>
            </div>

            {/* 右侧操作区 */}
            <div className="flex items-center gap-3">
              <button
                onClick={() => setIsModalOpen(true)}
                className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-violet-500 to-purple-600 px-5 py-2.5 text-sm font-semibold text-white shadow-lg shadow-violet-200 hover:shadow-xl hover:shadow-violet-300 transition-all hover:-translate-y-0.5"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
                添加数据库
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* 主内容区 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/query/:databaseName" element={<QueryPage />} />
        </Routes>
      </main>

      <AddDatabaseModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSuccess={handleSuccess}
      />
    </div>
  );
}

export default App;
