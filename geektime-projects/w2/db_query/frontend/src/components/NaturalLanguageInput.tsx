import React, { useState } from "react";
import { message } from "antd";

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
      // Keep the prompt value for user convenience
    } catch (err) {
      console.error("Generation failed:", err);
      const errorMessage = err instanceof Error ? err.message : "SQL 生成失败,请重试";
      message.error(errorMessage);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="rounded-2xl bg-white shadow-sm ring-1 ring-slate-200 p-6 mb-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center">
          <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.456 2.456L21.75 6l-1.035.259a3.375 3.375 0 00-2.456 2.456zM16.894 20.567L16.5 21.75l-.394-1.183a2.25 2.25 0 00-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 001.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 001.423 1.423l1.183.394-1.183.394a2.25 2.25 0 00-1.423 1.423z" />
          </svg>
        </div>
        <div>
          <h3 className="text-lg font-semibold text-slate-900">AI 生成 SQL</h3>
          <p className="text-sm text-slate-600">用自然语言描述查询，AI 自动生成 SQL</p>
        </div>
      </div>

      <div className="space-y-4">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="例如: 查询所有状态为活跃的用户"
          disabled={disabled || generating}
          className="w-full h-24 px-4 py-3 rounded-xl border border-slate-300 focus:border-violet-500 focus:ring-2 focus:ring-violet-200 focus:bg-white transition-all disabled:bg-slate-100 disabled:cursor-not-allowed bg-slate-50 resize-none text-sm"
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
              e.preventDefault();
              handleSubmit();
            }
          }}
        />
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-500">
            💡 提示: Ctrl+Enter 快速生成
          </span>
          <button
            onClick={handleSubmit}
            disabled={disabled || generating || !prompt.trim()}
            className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-violet-500 to-purple-600 px-6 py-2.5 text-sm font-semibold text-white shadow-lg shadow-violet-200 hover:shadow-xl hover:shadow-violet-300 transition-all hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none"
          >
            {generating ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                生成中...
              </>
            ) : (
              <>
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 12h14m-7-7 7 7-7 7" />
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
