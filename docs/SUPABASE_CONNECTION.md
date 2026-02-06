# Supabase连接配置指南

## 问题：IPv6连接失败

如果遇到 "Network is unreachable" 错误且显示IPv6地址，说明GitHub Actions无法通过IPv6连接到Supabase。

## 解决方案：使用连接池（Connection Pooler）

### 1. 获取正确的连接信息

登录Supabase项目：
1. 进入 **Settings** → **Database**
2. 找到 **Connection string** 部分
3. 选择 **Connection pooling** 标签（不是Direct connection）
4. 模式选择：**Transaction** 或 **Session**
5. 复制连接信息

### 2. 连接池URL格式

连接池URL通常是：
```
Host: aws-0-ap-southeast-1.pooler.supabase.com
Port: 6543  # 注意：连接池使用6543端口，不是5432
```

### 3. 更新GitHub Secrets

在GitHub仓库的Secrets中更新：
- `DB_HOST`: 使用连接池的host（通常包含 `.pooler.supabase.com`）
- `DB_PORT`: 改为 `6543`（连接池端口）
- `DB_NAME`: 保持 `postgres`
- `DB_USER`: 使用 `postgres.项目引用ID` 格式
- `DB_PASSWORD`: 你的数据库密码

### 4. 连接池 vs 直接连接

| 特性 | 直接连接 | 连接池 |
|------|---------|--------|
| 端口 | 5432 | 6543 |
| IPv6 | 可能使用 | 通常IPv4 |
| 并发连接 | 有限 | 更多 |
| 适用场景 | 本地开发 | 生产环境/CI |

### 5. 验证连接

更新配置后，在GitHub Actions中重新运行工作流。

如果还有问题，可以尝试：
1. 在Supabase中启用IPv4优先
2. 使用Supabase的API而不是直接数据库连接
3. 联系Supabase支持获取IPv4地址

## 本地测试

本地测试时，可以使用直接连接（端口5432）或连接池（端口6543）都可以。
