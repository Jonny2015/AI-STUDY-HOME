import React, { useState } from "react";

interface NaturalLanguageInputProps {
  onGenerate: (prompt: string) => Promise<void>;
  disabled: boolean;
}

export const NaturalLanguageInput: React.FC<NaturalLanguageInputProps> = ({
  onGenerate,
  disabled,
}) => {
  const [prompt, setPrompt] = useState("");
  const [generating, setGenerating] = useState(false);

  const handleSubmit = async () => {
    if (!prompt.trim()) return;

    setGenerating(true);
    try {
      await onGenerate(prompt);
      setPrompt(""); // Clear on success
    } catch (err) {
      console.error("Generation failed:", err);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="bg-white shadow rounded-lg p-6 mb-6">
      <h3 className="text-lg font-medium text-gray-900 mb-3">
        AI 生成 SQL
      </h3>
      <p className="text-sm text-gray-500 mb-4">
        用自然语言描述您想要查询的内容,AI 会为您生成 SQL 查询
      </p>
      <div className="space-y-3">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="例如: 查询所有状态为活跃的用户"
          disabled={disabled || generating}
          className="w-full h-24 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100 disabled:cursor-not-allowed resize-none"
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
              e.preventDefault();
              handleSubmit();
            }
          }}
        />
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-400">
            提示: Ctrl+Enter 快速生成
          </span>
          <button
            onClick={handleSubmit}
            disabled={disabled || generating || !prompt.trim()}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {generating ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                生成中...
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
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
                生成 SQL
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
