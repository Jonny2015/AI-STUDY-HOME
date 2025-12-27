import React, { useRef, useEffect } from "react";

interface SqlEditorProps {
  value: string;
  onChange: (value: string) => void;
  onExecute: () => void;
  placeholder?: string;
  disabled?: boolean;
}

export const SqlEditor: React.FC<SqlEditorProps> = ({
  value,
  onChange,
  onExecute,
  placeholder = "输入 SQL 查询...",
  disabled = false,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.focus();
    }
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Execute query on Ctrl+Enter or Cmd+Enter
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      onExecute();
    }
  };

  return (
    <div className="relative">
      <div className="absolute top-3 right-3 z-10 flex space-x-2">
        <kbd className="hidden sm:inline-block px-2 py-1 text-xs font-semibold text-gray-700 bg-gray-100 border border-gray-300 rounded">
          Ctrl+Enter 执行
        </kbd>
      </div>
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        className="w-full h-64 p-4 font-mono text-sm bg-gray-50 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none disabled:bg-gray-100 disabled:cursor-not-allowed"
        spellCheck={false}
      />
    </div>
  );
};
