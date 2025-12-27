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
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          onClick={onClose}
        ></div>

        <span className="hidden sm:inline-block sm:align-middle sm:h-screen">
          &#8203;
        </span>

        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <form onSubmit={handleSubmit}>
            <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
              <div className="sm:flex sm:items-start">
                <div className="mt-3 text-center sm:mt-0 sm:mt-0 sm:ml-4 sm:text-left w-full">
                  <h3 className="text-lg leading-6 font-medium text-gray-900">
                    添加数据库连接
                  </h3>
                  <div className="mt-4 space-y-4">
                    <div>
                      <label
                        htmlFor="db-name"
                        className="block text-sm font-medium text-gray-700"
                      >
                        连接名称
                      </label>
                      <input
                        type="text"
                        id="db-name"
                        required
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border"
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
                      <p className="mt-1 text-xs text-gray-500">
                        仅允许字母、数字、下划线和连字符
                      </p>
                    </div>

                    <div>
                      <label
                        htmlFor="db-url"
                        className="block text-sm font-medium text-gray-700"
                      >
                        连接字符串
                      </label>
                      <input
                        type="text"
                        id="db-url"
                        required
                        className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-3 py-2 border"
                        placeholder="postgresql://user:password@localhost:5432/mydb"
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                      />
                      <p className="mt-1 text-xs text-gray-500">
                        支持 PostgreSQL 和 MySQL
                      </p>
                    </div>

                    {error && (
                      <div className="rounded-md bg-red-50 p-4">
                        <p className="text-sm text-red-800">{error}</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
            <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-indigo-600 text-base font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
              >
                {isSubmitting ? "添加中..." : "添加"}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
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
