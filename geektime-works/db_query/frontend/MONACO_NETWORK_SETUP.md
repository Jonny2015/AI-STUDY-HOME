# Monaco Editor 网络配置说明

## 问题描述

Monaco Editor 默认从 `cdn.jsdelivr.net` 加载资源,在某些网络环境下可能无法访问。

## 当前解决方案 (✅ 推荐)

项目已采用**完全本地化**方案,Monaco Editor 文件存储在 `public/monaco-editor/` 目录,完全不依赖 CDN。

**配置位置**: `frontend/index.html:10-24`

```html
<script>
  (function() {
    // Configure Monaco to use local files instead of CDN
    window.require = {
      paths: {
        'vs': '/monaco-editor/min/vs'
      }
    };

    window.MonacoEnvironment = {
      getWorkerUrl: function(workerId, label) {
        return '/monaco-editor/min/vs/base/worker/' + workerId;
      }
    };
  })();
</script>
```

### 初始化本地文件

如果 `public/monaco-editor` 目录不存在,运行以下命令:

```bash
# 方法 1: 使用设置脚本 (推荐)
cd frontend
./scripts/setup-monaco-local.sh

# 方法 2: 手动复制
cd frontend/public
mkdir -p monaco-editor
cp -r ../node_modules/monaco-editor/min ./monaco-editor/
```

### 文件大小

本地化后的 Monaco Editor 文件大小约为 **40-50 MB**。

## 替代方案

如果本地化方案不适用,可以考虑以下替代方案:

### 方案 1: 使用国内 CDN

修改 `index.html` 使用国内 CDN:

```html
<script>
  window.require = {
    paths: {
      'vs': 'https://cdn.bootcdn.net/ajax/libs/monaco-editor/0.45.0/min/vs'
    }
  };
</script>
```

**可用国内 CDN**:
- bootcdn: `https://cdn.bootcdn.net/ajax/libs/monaco-editor/0.45.0/min/vs`
- staticfile: `https://cdn.staticfile.net/monaco-editor/0.45.0/min/vs`

### 方案 2: 使用系统代理

开发时可以使用代理工具:

```bash
# 使用系统代理
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
```

### 方案 3: 修改 hosts

如果 jsdelivr CDN 无法访问,可以修改系统 hosts 文件:

**Windows**: `C:\Windows\System32\drivers\etc\hosts`
**Mac/Linux**: `/etc/hosts`

添加:
```
104.16.85.20  cdn.jsdelivr.net
```

## 验证配置

启动开发服务器后:

1. **打开浏览器控制台** (F12)
2. **正常情况**: SQL 编辑器正常显示,有语法高亮
3. **网络错误**: 看到 `ERR_CONNECTION_TIMED OUT` 或 `loader.js` 加载失败

如果看到网络错误:
1. 检查 `public/monaco-editor` 目录是否存在
2. 重新运行设置脚本
3. 清除浏览器缓存

## 故障排查

### 错误: `GET https://cdn.jsdelivr.net/... net::ERR_CONNECTION_TIMED_OUT`

**原因**: 仍在尝试从 CDN 加载

**解决**:
1. 确认 `public/monaco-editor` 目录存在
2. 检查 `index.html` 配置是否正确
3. 清除浏览器缓存并重启开发服务器

### 错误: `Failed to load resource: /monaco-editor/min/vs/...`

**原因**: 本地文件缺失

**解决**:
```bash
cd frontend
./scripts/setup-monaco-local.sh
```

### 错误: `Uncaught TypeError: loader.config is not a function`

**原因**: API 使用错误 (已修复)

**解决**: 确保使用最新的 `index.html` 配置

### 编辑器显示空白

**原因**: Monaco 初始化失败

**解决**:
1. 检查浏览器控制台的错误信息
2. 确认本地文件完整性
3. 尝试清除 Vite 缓存: `rm -rf node_modules/.vite`

## 生产环境

生产环境部署时:

1. **确保 `public/monaco-editor` 目录包含在构建产物中**
2. **添加到 `.gitignore`**: `public/monaco-editor` (已在配置中)
3. **CI/CD 中添加构建步骤**:

```yaml
# .github/workflows/deploy.yml 示例
- name: Setup Monaco Editor
  run: |
    cd frontend
    ./scripts/setup-monaco-local.sh
```

## 常用 CDN 源 (参考)

如果需要切换回 CDN 方案:

- **jsdelivr** (默认): `https://cdn.jsdelivr.net/npm/monaco-editor@0.54.0/min/vs`
- **cdnjs**: `https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.54.0/min/vs`
- **unpkg**: `https://unpkg.com/monaco-editor@0.54.0/min/vs`
- **bootcdn** (国内): `https://cdn.bootcdn.net/ajax/libs/monaco-editor/0.45.0/min/vs`
- **staticfile** (国内): `https://cdn.staticfile.net/monaco-editor/0.45.0/min/vs`

