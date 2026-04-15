# Nexra 部署到 Vercel 指南

这份文档说明如何把当前的 Nexra 前后端一起部署到 Vercel，并接入 Postgres 持久化。

## 1. 当前架构

当前项目已经改造成：

- 前端静态页面由 Vercel 直接托管
- 后端通过 Vercel Python Function 提供 `/api`
- 运行态状态通过 Postgres 持久化
- 本地开发时仍可以回退到 JSON 状态文件

推荐架构：

```text
Browser
  -> Vercel Static Frontend
  -> /api
  -> Vercel Python Function
  -> Postgres state store
```

## 2. 仓库里已经包含的部署文件

- `api/index.py`
- `vercel.json`
- `requirements.txt`
- `runtime.txt`
- `.vercelignore`
- `.env.example`
- `backend_py/config.example.json`

## 3. 部署前准备

你需要准备：

- 一个 Vercel 账号
- 一个 Git 仓库
- 一个 Postgres 数据库连接串

推荐做法：

- 使用 Vercel Marketplace 的 Neon Postgres 免费实例
- 或者使用任意兼容 PostgreSQL 的托管数据库

## 4. 导入项目到 Vercel

### 方式 1：Vercel 后台导入 Git 仓库

1. 打开 Vercel 控制台。
2. 点击 `Add New Project`。
3. 选择你的 Git 仓库。
4. 使用仓库根目录直接导入。
5. Framework Preset 选择 `Other`。

### 方式 2：使用 Vercel CLI

```bash
npm i -g vercel
vercel
```

## 5. 配置环境变量

至少配置这些变量：

- `POSTGRES_URL`
- `NEXRA_STATE_BACKEND=postgres`
- `NEXRA_STATE_KEY=primary`

可选：

- `DATABASE_URL`

说明：

- `POSTGRES_URL` 或 `DATABASE_URL` 用于保存应用运行态
- 如果线上没有数据库，函数会在某些场景下回退到内存态，数据不能长期保存
- `NEXRA_STATE_KEY` 用于区分不同环境的状态快照

## 6. 本地配置与开源约定

仓库已经把本地私有文件加入 `.gitignore`：

- `.env.local`
- `backend_py/config.json`
- `backend_py/data/`
- `.runtime/`
- `logs/`

对外公开的模板文件：

- `.env.example`
- `backend_py/config.example.json`

后端启动时会优先读取：

1. `backend_py/config.json`
2. 如果不存在，再读取 `backend_py/config.example.json`

## 7. 域名访问

部署成功后，Vercel 会先给你一个默认域名，例如：

- `https://your-project.vercel.app`

如果要绑定正式域名：

1. 打开项目 `Settings`
2. 进入 `Domains`
3. 添加你的域名，例如 `nexra.example.com`
4. 按提示完成 DNS 解析

说明：

- Vercel 不提供固定 `IP + 端口` 暴露方式
- 线上访问应使用域名

## 8. 已验证的线上地址

当前项目已部署到：

- Web: [https://nexra-one.vercel.app](https://nexra-one.vercel.app)
- API: [https://nexra-one.vercel.app/api/dashboard](https://nexra-one.vercel.app/api/dashboard)

## 9. 上线后验证

建议按下面顺序检查：

1. 打开前端首页。
2. 检查 marketplace 页面是否能加载 skill 列表。
3. 直接访问 `/api/dashboard`。
4. 测试注册、登录和 token 鉴权。
5. 测试 skill 搜索、评分、提交 skill。
6. 测试管理员审核流程。

## 10. 常见问题

### 页面能打开，但接口 404

通常是：

- `vercel.json` 路由未生效
- `api/index.py` 没有被识别为 Python Function
- 静态路由覆盖了 `/api`

### 接口超时或报数据库错误

通常是：

- `POSTGRES_URL` 不可用
- `psycopg` 没有正确安装
- 函数初始化时连接数据库失败

### 能访问页面，但数据不持久

通常是：

- 没有配置 `POSTGRES_URL` 或 `DATABASE_URL`
- `NEXRA_STATE_BACKEND` 未设置为 `postgres`

## 11. 参考资料

- [Vercel Functions](https://vercel.com/docs/functions)
- [Vercel Runtimes](https://vercel.com/docs/functions/runtimes)
- [vercel.json](https://vercel.com/docs/project-configuration/vercel-json)
- [Custom Domains](https://vercel.com/docs/projects/domains/add-a-domain)
