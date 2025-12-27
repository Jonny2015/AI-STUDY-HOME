import { useState } from "react";
import { Routes, Route } from "react-router-dom";
import { useInvalidate } from "@refinedev/core";
import { Dashboard } from "./pages/Dashboard";
import { QueryPage } from "./pages/QueryPage";
import { AddDatabaseModal } from "./components/AddDatabaseModal";

function App() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const invalidate = useInvalidate();

  const handleSuccess = () => {
    // Invalidate the dbs resource to trigger a refetch
    invalidate({
      resource: "dbs",
      invalidates: ["list"],
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">
            Database Query Tool
          </h1>
          <button
            onClick={() => setIsModalOpen(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
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
                d="M12 4v16m8-8H4"
              />
            </svg>
            添加数据库
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
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
