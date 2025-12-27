import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { DatabaseList } from "../components/DatabaseList";
import { MetadataViewer } from "../components/MetadataViewer";

export const Dashboard = () => {
  const navigate = useNavigate();
  const [selectedDatabase, setSelectedDatabase] = useState<string | null>(null);

  const handleDatabaseSelect = (databaseName: string) => {
    setSelectedDatabase(databaseName);
  };

  const handleQueryClick = (databaseName: string) => {
    navigate(`/query/${databaseName}`);
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Left column: Database list */}
      <div className="space-y-6">
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            数据库列表
          </h2>
          <DatabaseList
            onSelect={handleDatabaseSelect}
            onQuery={handleQueryClick}
          />
        </div>
      </div>

      {/* Right column: Metadata viewer */}
      <div className="space-y-6">
        {selectedDatabase ? (
          <div className="space-y-4">
            <MetadataViewer databaseName={selectedDatabase} />
            <button
              onClick={() => handleQueryClick(selectedDatabase)}
              className="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              <svg
                className="-ml-1 mr-2 h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              执行查询
            </button>
          </div>
        ) : (
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
              <h3 className="mt-2 text-sm font-medium text-gray-900">
                选择数据库
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                点击左侧数据库查看其结构
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
