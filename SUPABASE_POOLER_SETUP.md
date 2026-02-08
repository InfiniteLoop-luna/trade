# Supabase 连接池配置指南

## 问题说明
GitHub Actions 不支持 IPv6 连接，需要使用 Supabase 的连接池（Connection Pooler）来解决连接问题。

## 获取连接池主机名

1. 访问您的 Supabase 项目控制台：
   https://supabase.com/dashboard/project/emjdqarihhjgaxxvffhh

2. 点击左侧菜单的 **"Database"** 或 **"Settings"** → **"Database"**

3. 找到 **"Connection string"** 或 **"Connection pooling"** 部分

4. 选择 **"Transaction Mode"** (端口 6543)

5. 复制连接字符串，格式类似：
   ```
   postgres://postgres.emjdqarihhjgaxxvffhh:[YOUR-PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres
   ```

6. 从连接字符串中提取主机名部分，例如：
   ```
   aws-0-us-east-1.pooler.supabase.com
   ```
   或
   ```
   aws-0-ap-southeast-1.pooler.supabase.com
   ```

## 配置 GitHub Secrets

在您的 GitHub 仓库中添加新的 Secret：

1. 访问：https://github.com/InfiniteLoop-luna/trade/settings/secrets/actions

2. 点击 **"New repository secret"**

3. 添加以下 Secret：
   - Name: `DB_POOLER_HOST`
   - Value: `aws-0-[your-region].pooler.supabase.com` (从上面获取的主机名)

## 更新 GitHub Actions 工作流

工作流文件已经配置好，会自动使用 `DB_POOLER_HOST`。

## 验证配置

配置完成后，手动触发工作流测试：
1. 访问：https://github.com/InfiniteLoop-luna/trade/actions/workflows/daily-update.yml
2. 点击 "Run workflow"
3. 选择 `main` 分支
4. 点击 "Run workflow" 开始测试

## 连接池格式说明

Supabase 连接池使用特殊的用户名格式：
- 格式：`[db-user].[project-ref]`
- 示例：`postgres.emjdqarihhjgaxxvffhh`

代码会自动处理这个格式转换，您只需要提供正确的 `DB_POOLER_HOST` 即可。
