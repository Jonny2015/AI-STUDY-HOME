import { test, expect } from '@playwright/test';

/**
 * Database Query Tool E2E 测试
 *
 * 测试主要功能：
 * 1. 应用加载
 * 2. 数据库列表显示
 * 3. 添加数据库
 * 4. 查询执行
 * 5. 删除数据库
 */

test.describe('Database Query Tool - 基础功能', () => {
  test.beforeEach(async ({ page }) => {
    // 访问应用主页
    await page.goto('/');

    // 等待页面加载完成
    await page.waitForLoadState('networkidle');
  });

  test('应该显示应用标题', async ({ page }) => {
    // 验证页面标题
    await expect(page).toHaveTitle(/Database Query Tool/);

    // 验证页面内容
    const heading = page.locator('h1, h2, .ant-typography').first();
    await expect(heading).toBeVisible();
  });

  test('应该显示数据库列表', async ({ page }) => {
    // 检查是否有数据库列表容器 - 使用更通用的选择器
    // DatabaseList 组件渲染 <ul> 列表，包含数据库名称
    const dbList = page.locator('ul:has(li:has-text("已连接")), ul:has(li:has-text("未连接")), .divide-y');
    await expect(dbList.first()).toBeVisible({ timeout: 10000 });
  });

  test('应该有添加数据库的按钮', async ({ page }) => {
    // 查找添加数据库按钮
    const addButton = page.locator('button:has-text("添加"), button:has-text("Add"), [data-testid="add-database-button"]');
    await expect(addButton.first()).toBeVisible();
  });
});

test.describe('Database Query Tool - API 集成测试', () => {
  test('后端 API 健康检查', async ({ request }) => {
    const response = await request.get('http://localhost:8000/health');

    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty('status', 'healthy');
  });

  test('应该获取数据库列表', async ({ request }) => {
    const response = await request.get('http://localhost:8000/api/v1/dbs');

    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty('data');
    expect(data).toHaveProperty('total');
    expect(Array.isArray(data.data)).toBe(true);
  });

  test('应该执行简单 SQL 查询', async ({ request }) => {
    const queryData = {
      sql: 'SELECT 1 as test_column, 2 as another_column'
    };

    const response = await request.post(
      'http://localhost:8000/api/v1/dbs/test_db/query',
      {
        data: queryData,
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data).toHaveProperty('columns');
    expect(data).toHaveProperty('rows');
    expect(data).toHaveProperty('rowCount');
    expect(data.rowCount).toBeGreaterThan(0);
  });

  test('应该拒绝非 SELECT 查询', async ({ request }) => {
    const queryData = {
      sql: 'INSERT INTO test VALUES (1)'
    };

    const response = await request.post(
      'http://localhost:8000/api/v1/dbs/test_db/query',
      {
        data: queryData,
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    expect(response.status()).toBe(400); // 或者其他预期的错误状态码
  });
});

test.describe('Database Query Tool - 用户交互测试', () => {
  test('数据库添加和删除工作流', async ({ page, request }) => {
    await page.goto('/');

    // 创建一个唯一的测试数据库名称
    const testDbName = `e2e_test_${Date.now()}`;

    // 1. 通过 API 添加测试数据库
    const addResponse = await request.put(
      `http://localhost:8000/api/v1/dbs/${testDbName}`,
      {
        data: {
          url: 'postgresql://postgres:123456@localhost:5432/test_db'
        },
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    expect(addResponse.status()).toBe(200);

    // 2. 刷新页面并验证新数据库出现在列表中
    await page.reload();
    await page.waitForLoadState('networkidle');

    // 3. 查找新添加的数据库
    const dbItem = page.locator(`text=${testDbName}`);
    await expect(dbItem.first()).toBeVisible({ timeout: 10000 });

    // 4. 删除测试数据库
    const deleteResponse = await request.delete(
      `http://localhost:8000/api/v1/dbs/${testDbName}`
    );

    // DELETE 操作成功返回 204 (No Content)
    expect(deleteResponse.status()).toBe(204);
  });
});
