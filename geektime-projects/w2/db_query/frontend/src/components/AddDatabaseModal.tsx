import React, { useState } from "react";
import { useCreate } from "@refinedev/core";

interface AddDatabaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export const AddDatabaseModal: React.FC<AddDatabaseModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { mutate } = useCreate();

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsSubmitting(true);

    try {
      await mutate(
        {
          resource: "dbs",
          values: { url, name },
        },
        {
          onSuccess: () => {
            setName("");
            setUrl("");
            onClose();
            onSuccess?.();
          },
          onError: (err: any) => {
            setError(
              err.response?.data?.detail || err.message || "添加数据库失败，请检查连接信息"
            );
          },
        }
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-10 overflow-y-auto">
      <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div
          className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity"
          onClick={onClose}
        ></div>

        <span className="hidden sm:inline-block sm:align-middle sm:h-screen">
          &#8203;
        </span>

        <div className="inline-block align-bottom bg-white rounded-2xl text-left overflow-hidden shadow-2xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full border border-sky-100">
          <form onSubmit={handleSubmit}>
            <div className="bg-gradient-to-r from-sky-50 to-blue-50 px-6 py-5 border-b border-sky-100">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-br from-sky-400 to-blue-500 rounded-xl flex items-center justify-center shadow-lg">
                  <svg
                    className="w-6 h-6 text-white"
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
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-800">
                    添加数据库连接
                  </h3>
                  <p className="text-xs text-gray-500 mt-0.5">
                    配置您的数据库连接信息
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white px-6 py-6">
              <div className="space-y-5">
                <div>
                  <label
                    htmlFor="db-name"
                    className="block text-sm font-semibold text-gray-700 mb-2"
                  >
                    连接名称
                  </label>
                  <input
                    type="text"
                    id="db-name"
                    required
                    className="block w-full rounded-xl border-sky-200 shadow-sm focus:border-sky-500 focus:ring-sky-500 sm:text-sm px-4 py-2.5 border focus:outline-none focus:ring-2 focus:ring-sky-500/20 transition-all duration-200"
                    placeholder="my_database"
                    value={name}
                    onChange={(e) => {
                      // Only allow alphanumeric, underscore, and hyphen
                      const value = e.target.value;
                      if (/^[a-zA-Z0-9_-]*$/.test(value)) {
                        setName(value);
                      }
                    }}
                  />
                  <p className="mt-1.5 text-xs text-gray-500 flex items-center">
                    <svg
                      className="w-3.5 h-3.5 mr-1 text-sky-500"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    仅允许字母、数字、下划线和连字符
                  </p>
                </div>

                <div>
                  <label
                    htmlFor="db-url"
                    className="block text-sm font-semibold text-gray-700 mb-2"
                  >
                    连接字符串
                  </label>
                  <input
                    type="text"
                    id="db-url"
                    required
                    className="block w-full rounded-xl border-sky-200 shadow-sm focus:border-sky-500 focus:ring-sky-500 sm:text-sm px-4 py-2.5 border focus:outline-none focus:ring-2 focus:ring-sky-500/20 transition-all duration-200"
                    placeholder="postgresql://user:password@localhost:5432/mydb"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                  />
                  <p className="mt-1.5 text-xs text-gray-500 flex items-center">
                    <svg
                      className="w-3.5 h-3.5 mr-1 text-sky-500"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    支持 PostgreSQL 和 MySQL
                  </p>
                </div>

                {error && (
                  <div className="rounded-xl bg-red-50 p-4 border border-red-200 flex items-start space-x-3">
                    <svg
                      className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5"
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
                    <p className="text-sm text-red-700 flex-1">{error}</p>
                  </div>
                )}
              </div>
            </div>
            <div className="bg-sky-50/50 px-6 py-4 sm:px-6 sm:flex sm:flex-row-reverse border-t border-sky-100">
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full inline-flex justify-center items-center rounded-xl border border-transparent shadow-sm px-6 py-2.5 bg-gradient-to-r from-sky-500 to-blue-600 text-base font-medium text-white hover:from-sky-600 hover:to-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-sky-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 hover:shadow-md"
              >
                {isSubmitting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    添加中...
                  </>
                ) : (
                  <>
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
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                    添加
                  </>
                )}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="mt-3 w-full inline-flex justify-center rounded-xl border border-sky-200 shadow-sm px-6 py-2.5 bg-white text-base font-medium text-gray-700 hover:bg-sky-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-sky-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm transition-all duration-200"
              >
                取消
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
