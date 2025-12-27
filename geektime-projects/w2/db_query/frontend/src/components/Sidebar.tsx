import { useList } from "@refinedev/core";
import type { Database } from "../types";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  onAddDatabase: () => void;
  currentPath: string;
  onNavigate: (path: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  onClose,
  onAddDatabase,
  currentPath,
  onNavigate,
}) => {
  const { query, result } = useList<Database>({
    resource: "dbs",
  });

  // Handle different possible data structures from Refine
  const databases = Array.isArray(result?.data)
    ? result.data
    : (result?.data as any)?.data || [];

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-20 lg:hidden"
          onClick={onClose}
        ></div>
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed lg:static inset-y-0 left-0 z-30
          w-64 bg-white border-r border-slate-200
          transform transition-transform duration-300 ease-in-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        <div className="flex flex-col h-full">
          {/* Logo section */}
          <div className="p-6 border-b border-slate-200">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                </svg>
              </div>
              <div>
                <h2 className="text-lg font-bold text-slate-800">数据库查询</h2>
                <p className="text-xs text-slate-500">Database Query</p>
              </div>
            </div>
          </div>

          {/* Database list */}
          <div className="flex-1 overflow-y-auto">
            <div className="p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  数据库列表
                </h3>
                <span className="text-xs text-slate-400">{databases.length}</span>
              </div>

              {query.isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                </div>
              ) : databases.length === 0 ? (
                <div className="text-center py-8">
                  <svg className="mx-auto h-12 w-12 text-slate-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414-2.414a1 1 0 01-.293-.707V5.414a1 1 0 01.293-.707l5.414-5.414a1 1 0 011.414 0l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <p className="text-sm text-slate-500 mb-4">暂无数据库</p>
                  <button
                    onClick={onAddDatabase}
                    className="text-sm text-blue-600 hover:text-blue-700 font-medium"
                  >
                    + 添加第一个数据库
                  </button>
                </div>
              ) : (
                <ul className="space-y-1">
                  {databases.map((db: Database) => {
                    const isActive = currentPath === `/query/${db.databaseName}`;
                    return (
                      <li key={db.databaseName}>
                        <button
                          onClick={() => onNavigate(`/query/${db.databaseName}`)}
                          className={`
                            w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg
                            transition-all duration-200 group
                            ${isActive
                              ? 'bg-blue-50 text-blue-700'
                              : 'text-slate-700 hover:bg-slate-100'
                            }
                          `}
                        >
                          <div className={`
                            w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0
                            ${isActive
                              ? 'bg-blue-600 text-white'
                              : 'bg-slate-200 text-slate-600 group-hover:bg-slate-300'
                            }
                          `}>
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                            </svg>
                          </div>
                          <div className="flex-1 min-w-0 text-left">
                            <p className="text-sm font-medium truncate">{db.databaseName}</p>
                            <p className="text-xs opacity-75 truncate">{db.dbType}</p>
                          </div>
                          {isActive && (
                            <svg className="w-4 h-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                          )}
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          </div>

          {/* Bottom action button */}
          <div className="p-4 border-t border-slate-200">
            <button
              onClick={onAddDatabase}
              className="w-full inline-flex items-center justify-center px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors shadow-sm"
            >
              <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              添加数据库
            </button>
          </div>
        </div>
      </aside>
    </>
  );
};
