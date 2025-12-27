# API 测试文件说明

本目录包含用于测试 Database Query Tool API 的测试文件。

## 文件说明

- `test.rest` - REST Client 格式的 API 测试文件，包含所有 API 端点的测试用例

## 使用方法

### 1. 安装 VSCode REST Client 扩展

在 VSCode 中安装 [REST Client](https://marketplace.visualstudio.com/items?itemName=humao.rest-client) 扩展。

### 2. 启动后端服务器

在项目根目录运行：

```bash
make dev-backend
```

或者手动启动：

```bash
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

后端服务器将在 `http://localhost:8000` 启动。

### 3. 配置环境变量

确保设置了必要的环境变量：

```bash
export OPENAI_API_KEY=your_openai_api_key_here
```

或者在项目根目录创建 `.env` 文件：

```
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. 运行测试

1. 在 VSCode 中打开 `fixtures/test.rest` 文件
2. 每个请求上方会显示 "Send Request" 按钮
3. 点击按钮即可发送请求并查看响应
4. 响应结果会显示在右侧面板中

## 测试用例说明

### 健康检查
- 检查服务器是否正常运行

### 数据库管理 API
- **GET /api/v1/dbs** - 获取所有数据库列表
- **POST /api/v1/dbs** - 添加数据库（POST 方式）
- **PUT /api/v1/dbs/{name}** - 添加数据库（PUT 方式）
- **GET /api/v1/dbs/{name}** - 获取数据库元数据
- **DELETE /api/v1/dbs/{name}** - 删除数据库

### SQL 查询 API
- **POST /api/v1/dbs/{name}/query** - 执行 SQL 查询
- **POST /api/v1/dbs/{name}/query/export** - 导出查询结果为 CSV

### 自然语言生成 SQL
- **POST /api/v1/dbs/{name}/query/natural** - 使用自然语言生成 SQL

### 错误测试用例
- 测试各种错误场景和边界情况

### 完整工作流测试
- PostgreSQL 完整流程测试
- MySQL 完整流程测试

## 配置变量

在 `test.rest` 文件顶部定义了以下变量，可以根据实际情况修改：

```http
@baseUrl = http://localhost:8000
@apiPrefix = {{baseUrl}}/api/v1
@dbName = test_db
@mysqlDbName = interview_db
@postgresUrl = postgresql://postgres:postgres@localhost:5432/postgres
@mysqlUrl = mysql://root@localhost:3306/interview_db
```

### 修改数据库连接

根据你的实际数据库配置，修改以下变量：

- `@postgresUrl` - PostgreSQL 数据库连接字符串
- `@mysqlUrl` - MySQL 数据库连接字符串
- `@dbName` - 测试用的数据库名称
- `@mysqlDbName` - 测试用的 MySQL 数据库名称

## 测试顺序建议

### 基本功能测试
1. 健康检查
2. 获取数据库列表（应该为空）
3. 添加 PostgreSQL 数据库
4. 获取数据库元数据
5. 执行简单 SQL 查询
6. 使用自然语言生成 SQL

### MySQL 测试
1. 添加 MySQL 数据库
2. 获取 MySQL 数据库元数据
3. 执行 MySQL 查询
4. 使用自然语言生成 MySQL SQL

### 错误场景测试
1. 测试无效的 SQL 语法
2. 测试非 SELECT 语句（应该被拒绝）
3. 测试不存在的数据库
4. 测试无效的数据库 URL

## 注意事项

1. **数据库连接**：确保你的数据库服务正在运行，并且连接字符串正确
2. **OpenAI API Key**：自然语言生成 SQL 功能需要有效的 OpenAI API Key
3. **端口冲突**：确保 8000 端口没有被其他服务占用
4. **CORS**：后端已配置允许所有来源的 CORS，前端可以正常访问

## 常见问题

### 1. 连接被拒绝
- 检查后端服务器是否正在运行
- 确认端口 8000 是否被占用

### 2. 数据库连接失败
- 检查数据库服务是否运行
- 验证连接字符串格式是否正确
- 确认数据库用户权限

### 3. 自然语言生成失败
- 检查 `OPENAI_API_KEY` 环境变量是否设置
- 确认 API Key 是否有效且有足够的额度

### 4. SQL 查询被拒绝
- 确认 SQL 语句是 SELECT 查询
- 检查 SQL 语法是否正确
- 验证表名和列名是否存在

## 相关文档

- [FastAPI 文档](http://localhost:8000/docs) - 启动后端后访问
- [项目说明](../specs/instructions.md)
- [后端 README](../backend/README.md)

