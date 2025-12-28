# Database Query Tool - Frontend

React 前端应用,提供数据库连接管理、SQL 查询编辑器、结果展示和自然语言查询界面。

## 技术栈

- **框架**: React 19 + TypeScript 5
- **构建工具**: Vite 7
- **UI 框架**: Refine 5 + Ant Design 5
- **代码编辑器**: Monaco Editor
- **样式**: Tailwind CSS 4
- **路由**: React Router v7
- **HTTP 客户端**: Axios
- **测试**: Vitest + React Testing Library

## 项目结构

```
frontend/
├── src/
│   ├── main.tsx              # Vite 入口
│   ├── App.tsx               # 主应用组件 (Refine 配置)
│   ├── types/                # TypeScript 类型定义
│   │   ├── database.ts       # 数据库连接类型
│   │   ├── metadata.ts       # 元数据类型
│   │   └── query.ts          # 查询和结果类型
│   ├── services/             # API 服务
│   │   ├── api.ts            # Axios 实例配置
│   │   └── dataProvider.ts   # Refine 数据提供者
│   ├── pages/                # 页面组件
│   │   ├── databases/
│   │   │   ├── list.tsx      # 数据库列表
│   │   │   ├── create.tsx    # 创建数据库连接
│   │   │   ├── show.tsx      # 数据库详情 (元数据)
│   │   │   └── edit.tsx      # 编辑数据库连接
│   │   └── queries/
│   │       └── execute.tsx   # 查询执行页面
│   ├── components/           # 可复用组件
│   │   ├── SqlEditor.tsx     # Monaco SQL 编辑器
│   │   ├── ResultTable.tsx   # 查询结果表格
│   │   ├── MetadataTree.tsx  # 元数据树形视图
│   │   └── NaturalLanguageInput.tsx  # 自然语言输入
│   └── styles/
│       └── index.css         # Tailwind 样式入口
├── public/                   # 静态资源
├── index.html                # HTML 模板
├── package.json              # 项目依赖
├── tsconfig.json             # TypeScript 配置
├── vite.config.ts            # Vite 配置
├── tailwind.config.js        # Tailwind 配置
└── .env.local.example        # 环境变量模板
```

## 快速开始

### 1. 安装依赖

推荐使用 `npm`、`yarn` 或 `pnpm`:

```bash
# 使用 npm
npm install

# 使用 yarn
yarn install

# 使用 pnpm
pnpm install
```

### 2. 配置环境变量

复制 `.env.local.example` 为 `.env.local`:

```bash
cp .env.local.example .env.local
```

编辑 `.env.local` 文件:

```env
# 后端 API 基础 URL
VITE_API_BASE_URL=http://localhost:8000
```

### 3. 启动开发服务器

```bash
# 使用 npm
npm run dev

# 使用 yarn
yarn dev

# 使用 pnpm
pnpm dev
```

开发服务器默认运行在 http://localhost:5173

### 4. 构建生产版本

```bash
# 使用 npm
npm run build

# 使用 yarn
yarn build

# 使用 pnpm
pnpm build
```

构建产物将输出到 `dist/` 目录。

### 5. 预览生产构建

```bash
# 使用 npm
npm run preview

# 使用 yarn
yarn preview

# 使用 pnpm
pnpm preview
```

## 开发工具

### 代码检查

```bash
# 运行 ESLint
npm run lint

# 自动修复问题
npm run lint -- --fix
```

### 运行测试

```bash
# 运行测试
npm run test

# 运行测试并监听文件变化
npm run test -- --watch

# 生成覆盖率报告
npm run test -- --coverage
```

## 核心功能

### 1. 数据库连接管理

- 添加/编辑/删除数据库连接
- 支持 PostgreSQL 和 MySQL
- 连接测试功能
- 数据库列表展示

### 2. 元数据浏览

- 树形结构展示数据库结构
- 表和列信息展示
- 数据类型和约束显示
- 行数统计信息

### 3. SQL 查询编辑器

- Monaco Editor 集成
- SQL 语法高亮
- 自动完成和提示
- 格式化支持

### 4. 查询结果展示

- 表格形式展示结果
- 分页支持
- 排序功能
- 导出为 CSV/JSON

### 5. 自然语言查询

- 中英文自然语言输入
- AI 生成 SQL
- 生成的 SQL 可编辑
- 查询历史记录

## 使用示例

### 1. 添加数据库连接

1. 点击"添加数据库"按钮
2. 填写连接信息:
   - **名称**: mydb
   - **连接字符串**: `postgresql://user:password@localhost:5432/mydb`
   - **数据库类型**: PostgreSQL
3. 点击"保存"按钮
4. 点击"测试连接"验证配置

### 2. 浏览数据库元数据

1. 在数据库列表中点击数据库名称
2. 查看树形结构的表和列信息
3. 点击表名查看列详情
4. 点击"刷新元数据"获取最新结构

### 3. 执行 SQL 查询

1. 选择数据库
2. 在 SQL 编辑器中输入查询:
   ```sql
   SELECT * FROM users LIMIT 10
   ```
3. 点击"执行查询"按钮
4. 在结果表格中查看数据
5. 使用分页控件浏览更多结果

### 4. 导出查询结果

1. 执行查询后,点击"导出"按钮
2. 选择导出格式 (CSV 或 JSON)
3. 文件将自动下载,包含时间戳:
   - `query_results_20250128_143022.csv`

### 5. 自然语言查询

1. 切换到"自然语言"标签
2. 输入查询描述:
   - 中文: "查询所有邮箱以 example.com 结尾的用户"
   - 英文: "Find all users whose email ends with example.com"
3. 点击"生成 SQL"按钮
4. 查看生成的 SQL,可手动编辑
5. 点击"执行查询"运行

## 组件使用说明

### SqlEditor

Monaco Editor SQL 编辑器组件:

```tsx
import { SqlEditor } from "@/components/SqlEditor";

<SqlEditor
  value={sql}
  onChange={setSql}
  language="sql"
  height="400px"
  options={{
    minimap: { enabled: false },
    fontSize: 14,
  }}
/>
```

### ResultTable

查询结果表格组件:

```tsx
import { ResultTable } from "@/components/ResultTable";

<ResultTable
  columns={["id", "name", "email"]}
  rows={[[1, "John", "john@example.com"]]}
  loading={false}
  pagination={{
    current: 1,
    pageSize: 10,
    total: 100,
    onChange: (page) => console.log(page),
  }}
/>
```

### MetadataTree

元数据树形视图组件:

```tsx
import { MetadataTree } from "@/components/MetadataTree";

<MetadataTree
  tables={[
    {
      name: "users",
      columns: [
        { name: "id", type: "integer", isPrimaryKey: true },
        { name: "email", type: "varchar", isPrimaryKey: false },
      ],
    },
  ]}
  onSelectTable={(table) => console.log(table)}
/>
```

## TypeScript 类型定义

### Database Types

```typescript
// src/types/database.ts
export interface DatabaseConnection {
  name: string;
  connectionString: string;
  dbType: "postgresql" | "mysql";
  createdAt: string;
}

export interface DatabaseMetadata {
  name: string;
  dbType: string;
  metadata: {
    tables: TableMetadata[];
  };
}
```

### Query Types

```typescript
// src/types/query.ts
export interface QueryRequest {
  sql: string;
}

export interface QueryResult {
  columns: string[];
  rows: unknown[][];
  rowCount: number;
}

export interface QueryHistory {
  id: number;
  databaseName: string;
  sql: string;
  executedAt: string;
  executionTime?: number;
}
```

## 配置说明

### Vite 配置

```typescript
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
```

### TypeScript 配置

TypeScript 严格模式已启用:

```json
{
  "compilerOptions": {
    "strict": true,
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "bundler"
  }
}
```

### Tailwind CSS

Tailwind CSS 4 配置:

```javascript
// tailwind.config.js
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};
```

## 样式规范

### Tailwind 类命名

使用 Utility-first 类名:

```tsx
<div className="flex items-center justify-between p-4 bg-white rounded-lg shadow">
  <h2 className="text-xl font-semibold text-gray-900">标题</h2>
  <button className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">
    按钮
  </button>
</div>
```

### Ant Design 主题

可以通过 Refine 配置自定义 Ant Design 主题:

```tsx
<Refine
  dataProvider={dataProvider}
  options={{
    syncWithLocation: true,
    warnWhenUnsavedChanges: true,
    useNewQueryKeys: true,
    projectId: "db-query-tool",
  }}
/>
```

## 性能优化

- 代码分割: React.lazy + Suspense
- 虚拟滚动: 大数据集使用虚拟列表
- 查询分页: 避免一次性加载大量数据
- 缓存策略: 元数据和查询历史缓存
- 懒加载: 组件按需加载

## 故障排查

### 1. API 连接失败

检查 `.env.local` 中的 `VITE_API_BASE_URL` 是否正确:

```env
VITE_API_BASE_URL=http://localhost:8000
```

确保后端服务正在运行:

```bash
# 在 backend 目录
uvicorn app.main:app --reload
```

### 2. Monaco Editor 加载失败

清除缓存并重新安装依赖:

```bash
rm -rf node_modules package-lock.json
npm install
```

### 3. TypeScript 类型错误

运行类型检查:

```bash
npx tsc --noEmit
```

确保所有类型定义正确导入。

### 4. 构建失败

检查 Node.js 版本 (推荐 >= 18):

```bash
node --version
```

清除 Vite 缓存:

```bash
rm -rf dist .vite
npm run build
```

## 相关文档

- [Refine 文档](https://refine.dev/docs/)
- [Ant Design 组件](https://ant.design/components/)
- [Monaco Editor API](https://microsoft.github.io/monaco-editor/)
- [后端 README](../backend/README.md)

## License

MIT
