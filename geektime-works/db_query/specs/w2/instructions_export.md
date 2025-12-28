# Instructions

## 基本思路

这是一个数据库查询工具，在现有系统功能的基础上新增一个数据导出功能模块。用户可以将查询结果导出多种格式（例如：CSV 文件、JSON 文件、MD 文件），支持导出当前页面的数据，也支持导出所有数据。也可以使用AI助手来协助导出功能。

基本想法：

- 新增一个数据导出功能模块。用户可以将查询结果导出多种格式（例如：CSV 文件、JSON 文件、MD 文件），支持导出当前页面的数据，也支持导出所有数据。
- 在前端页面新增一个开关，用户可以开启或关闭AI助手（点亮即为开启，熄灭即为关闭），在AI助手开启时，发起查询后若数据存在，则提示“需要将这次查询结果导出为 CSV/JSON/MD 文件吗？”, 用户选择是，则数据导出功能开始执行（页面需要有进度条提示），导出完成后，提示“数据导出完成”。用户选择否，则不进行数据导出。
- 当用户使用 AI 助手来协助导出功能时，我们需要把系统中的表和视图的信息作为 context 传递给 AI 助手，然后 AI 助手会根据这些信息来生成导出文件的 sql 查询。若查询结果页面没有全部显示时， 需要提示用户是否需要全部导出，用户选择是，则继续执行导出功能，用户选择否，则仅进行当前页面的数据导出。导出完成后，提示“数据导出完成”。

后端 API 需要支持 cors，允许所有 origin。大致 API 如下：

```bash
# 导出当前页的查询结果
POST /api/v1/dbs/{name}/export/current

{
  "sql": "SELECT * FROM users"，
  "format": "csv"
}

# 导出可以查询的所有可以查询的结果
POST /api/v1/dbs/{name}/export/all

{
  "sql": "SELECT * FROM users"，
  "format": "csv"
}
```

# 任务分解
/speckit.specify
/speckit.plan

/speckit.tasks 任务分解粒度小一些, 按过程中的事件或动作维度分解，比如：“获取查询结果”、“格式化数据”、“创建文件”等，制定执行的子任务项。要求每个任务是可执行的且相对独立的，不可循环依赖。 

# 功能实现
/speckit.implement 开始执行 phase 1-3 


📊 总览统计

  总任务数: 122 个任务

  按阶段分解:
  - Phase 1 (Setup): 4 个任务
  - Phase 2 (Foundational): 40 个任务
  - Phase 3 (User Story 1 - 手动导出): 30 个任务 (15 测试 + 15 实现)
  - Phase 4 (User Story 2 - AI 助手): 22 个任务 (10 测试 + 12 实现)
  - Phase 5 (User Story 3 - AI SQL 生成): 14 个任务 (7 测试 + 7 实现)
  - Phase 6 (Polish): 12 个任务

## 测试
仔细阅读 db_query 下面的代码，然后运行后端和前端，根据@fixtures/test.rest 用 curl 测试后端已实现的路由；然后用 playwright 开前端进行测试，任何测试问题，think ultra hard and fix

## db migration & unit test

`make setup` 会出错，修复它；确保前后端 unit test 都通过。
