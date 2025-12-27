import React, { useState, useRef, useEffect, useCallback } from "react";
import type { TableMetadata } from "../types";

interface SqlEditorWithAutocompleteProps {
  value: string;
  onChange: (value: string) => void;
  onExecute: () => void;
  tables?: TableMetadata[];
  placeholder?: string;
  disabled?: boolean;
}

interface Suggestion {
  text: string;
  type: "table" | "column" | "keyword";
  tableName?: string;
  columnName?: string;
  dataType?: string;
}

const SQL_KEYWORDS = [
  "SELECT", "FROM", "WHERE", "AND", "OR", "NOT", "IN", "LIKE", "ORDER BY", "GROUP BY",
  "HAVING", "LIMIT", "OFFSET", "JOIN", "LEFT JOIN", "RIGHT JOIN", "INNER JOIN",
  "ON", "AS", "DISTINCT", "COUNT", "SUM", "AVG", "MAX", "MIN", "ASC", "DESC"
];

export const SqlEditorWithAutocomplete: React.FC<SqlEditorWithAutocompleteProps> = ({
  value,
  onChange,
  onExecute,
  tables = [],
  placeholder = "输入 SQL 查询...",
  disabled = false,
}) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);

  // 获取光标位置
  const getCursorCoordinates = useCallback(() => {
    const textarea = textareaRef.current;
    if (!textarea) return { top: 0, left: 0 };

    const { selectionStart } = textarea;
    const text = textarea.value.substring(0, selectionStart);
    const lines = text.split("\n");

    // 简单估算位置
    const fontSize = parseInt(getComputedStyle(textarea).fontSize);
    const lineHeight = fontSize * 1.5;
    const top = lines.length * lineHeight + 40; // 40是顶部padding

    // 估算左侧位置
    const lastLine = lines[lines.length - 1] || "";
    const charWidth = fontSize * 0.6;
    const left = lastLine.length * charWidth + 20;

    return { top, left };
  }, []);

  // 获取当前输入的单词
  const getCurrentWord = useCallback((): { word: string; start: number; end: number } => {
    const textarea = textareaRef.current;
    if (!textarea) return { word: "", start: 0, end: 0 };

    const { selectionStart } = textarea;
    const text = textarea.value;

    // 向前查找单词边界
    let start = selectionStart - 1;
    while (start >= 0 && /[\w.]/.test(text[start])) {
      start--;
    }
    start++;

    // 向后查找单词边界
    let end = selectionStart;
    while (end < text.length && /[\w.]/.test(text[end])) {
      end++;
    }

    const word = text.substring(start, end);
    return { word, start, end };
  }, []);

  // 生成建议列表
  const generateSuggestions = useCallback((word: string) => {
    if (!word) return [];

    const upperWord = word.toUpperCase();
    const suggestions: Suggestion[] = [];

    // 添加 SQL 关键字 (优先级最高)
    SQL_KEYWORDS.filter(keyword => keyword.startsWith(upperWord))
      .forEach(keyword => {
        suggestions.push({ text: keyword, type: "keyword" });
      });

    // 按 schema 分组表
    const schemaMap = new Map<string, typeof tables>();
    tables.forEach(table => {
      const schema = table.schemaName || "public";
      if (!schemaMap.has(schema)) {
        schemaMap.set(schema, []);
      }
      schemaMap.get(schema)!.push(table);
    });

    // 添加表名 (按 schema 排序,public 优先)
    const sortedSchemas = Array.from(schemaMap.keys()).sort((a, b) => {
      if (a === "public") return -1;
      if (b === "public") return 1;
      return a.localeCompare(b);
    });

    sortedSchemas.forEach(schema => {
      schemaMap.get(schema)!.forEach(table => {
        if (table.tableName.toUpperCase().startsWith(upperWord)) {
          suggestions.push({
            text: table.tableName,
            type: "table",
            tableName: table.tableName
          });
        }
      });
    });

    // 检查是否是 table.column 或 schema.table.column 格式
    if (word.includes(".")) {
      const parts = word.split(".");

      if (parts.length === 2) {
        // 可能是 table.column 或 schema.table
        const [first, second] = parts;

        // 先尝试作为 table.column
        const table = tables.find(t =>
          t.tableName.toUpperCase() === first.toUpperCase()
        );

        if (table) {
          table.columns.forEach(column => {
            if (!second || column.columnName.toUpperCase().startsWith(second.toUpperCase())) {
              suggestions.push({
                text: `${table.tableName}.${column.columnName}`,
                type: "column",
                tableName: table.tableName,
                columnName: column.columnName,
                dataType: column.dataType
              });
            }
          });
        }
      } else if (parts.length === 3) {
        // schema.table.column
        const [schema, tableName, columnName] = parts;
        const table = tables.find(t =>
          t.schemaName.toUpperCase() === schema.toUpperCase() &&
          t.tableName.toUpperCase() === tableName.toUpperCase()
        );

        if (table) {
          table.columns.forEach(column => {
            if (!columnName || column.columnName.toUpperCase().startsWith(columnName.toUpperCase())) {
              suggestions.push({
                text: `${table.schemaName}.${table.tableName}.${column.columnName}`,
                type: "column",
                tableName: table.tableName,
                columnName: column.columnName,
                dataType: column.dataType
              });
            }
          });
        }
      }
    } else {
      // 添加所有列 (按表分组)
      sortedSchemas.forEach(schema => {
        schemaMap.get(schema)!.forEach(table => {
          table.columns.forEach(column => {
            if (column.columnName.toUpperCase().startsWith(upperWord)) {
              suggestions.push({
                text: column.columnName,
                type: "column",
                tableName: table.tableName,
                columnName: column.columnName,
                dataType: column.dataType
              });
            }
          });
        });
      });
    }

    return suggestions.slice(0, 10); // 限制显示数量
  }, [tables]);

  // 处理输入变化
  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value;
    onChange(newValue);

    // 检查是否应该显示建议
    const { word } = getCurrentWord();
    if (word.length >= 1) {
      const newSuggestions = generateSuggestions(word);
      if (newSuggestions.length > 0) {
        setSuggestions(newSuggestions);
        setSelectedIndex(0);
        setShowSuggestions(true);
      } else {
        setShowSuggestions(false);
      }
    } else {
      setShowSuggestions(false);
    }
  };

  // 应用建议
  const applySuggestion = (suggestion: Suggestion) => {
    const { start, end } = getCurrentWord();
    const newValue =
      value.substring(0, start) +
      suggestion.text +
      value.substring(end);

    onChange(newValue);
    setShowSuggestions(false);

    // 重新聚焦并移动光标
    setTimeout(() => {
      const textarea = textareaRef.current;
      if (textarea) {
        const newPosition = start + suggestion.text.length;
        textarea.focus();
        textarea.setSelectionRange(newPosition, newPosition);
      }
    }, 0);
  };

  // 处理键盘事件
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (showSuggestions) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex(prev =>
          prev < suggestions.length - 1 ? prev + 1 : 0
        );
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex(prev =>
          prev > 0 ? prev - 1 : suggestions.length - 1
        );
      } else if (e.key === "Enter" || e.key === "Tab") {
        e.preventDefault();
        if (suggestions[selectedIndex]) {
          applySuggestion(suggestions[selectedIndex]);
        }
      } else if (e.key === "Escape") {
        setShowSuggestions(false);
      }
    } else {
      // 执行查询
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        onExecute();
      }
    }
  };

  // 点击外部关闭建议
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(e.target as Node) &&
        textareaRef.current &&
        !textareaRef.current.contains(e.target as Node)
      ) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="relative">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        className="w-full h-64 p-4 font-mono text-sm bg-gray-900 text-gray-100 border border-gray-700 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none disabled:bg-gray-800 disabled:cursor-not-allowed transition-all"
        spellCheck={false}
        autoComplete="off"
      />

      {/* 建议下拉框 */}
      {showSuggestions && suggestions.length > 0 && (
        <div
          ref={suggestionsRef}
          className="absolute z-50 w-80 max-h-64 overflow-auto bg-white border border-slate-300 rounded-lg shadow-xl"
          style={{
            top: `${Math.min(getCursorCoordinates().top, 300)}px`,
            left: `${Math.min(getCursorCoordinates().left, 400)}px`,
          }}
        >
          {suggestions.map((suggestion, index) => (
            <div
              key={index}
              className={`px-4 py-2 cursor-pointer transition-colors ${
                index === selectedIndex
                  ? "bg-blue-50 text-blue-700"
                  : "hover:bg-slate-50"
              }`}
              onClick={() => applySuggestion(suggestion)}
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-sm">{suggestion.text}</span>
                <span
                  className={`ml-2 px-2 py-0.5 text-xs rounded ${
                    suggestion.type === "keyword"
                      ? "bg-purple-100 text-purple-700"
                      : suggestion.type === "table"
                      ? "bg-blue-100 text-blue-700"
                      : "bg-green-100 text-green-700"
                  }`}
                >
                  {suggestion.type === "keyword"
                    ? "关键字"
                    : suggestion.type === "table"
                    ? "表"
                    : "字段"}
                </span>
              </div>
              {suggestion.type === "column" && suggestion.dataType && (
                <div className="mt-1 text-xs text-slate-500">
                  {suggestion.tableName} • {suggestion.dataType}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* 提示信息 */}
      <div className="absolute top-3 right-3 z-10 flex space-x-2 pointer-events-none">
        <kbd className="hidden sm:inline-block px-2 py-1 text-xs font-semibold text-slate-600 bg-slate-100 border border-slate-300 rounded">
          Tab: 自动完成
        </kbd>
        <kbd className="hidden sm:inline-block px-2 py-1 text-xs font-semibold text-slate-600 bg-slate-100 border border-slate-300 rounded">
          Ctrl+Enter: 执行
        </kbd>
      </div>
    </div>
  );
};
