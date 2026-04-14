# Nexra 部署到 Vercel 指南

这份文档说明怎么把当前的 `Nexra` 项目前端部署到 `Vercel`，并把 Python 后端部署到独立服务器后再通过 `/api` 代理接入。

## 结论

当前项目最稳妥的上线方式是：

- 前端部署到 `Vercel`
- Python 后端部署到云服务器、Railway、Render 或 Fly.io
- 在 `Vercel` 上把 `/api/*` rewrite 到你的后端地址

不建议把当前整套后端直接放进 Vercel Functions，因为这版后端是长驻进程型 `Python HTTP Server`，同时依赖本地状态文件持续写入。

## 推荐架构

```text
Browser
  -> Vercel Frontend
  -> /api rewrite
  -> External Python Backend
  -> JSON state file / future database
```

## 部署前准备

你需要准备：

- 一个 `Vercel` 账号
- 一个 Git 仓库
- 一个已可公网访问的后端地址，例如：
  - `https://api.nexra.example.com`
  - `http://YOUR_SERVER_IP:8080`

如果后端还没部署，可以先参考：

- [cloud-deployment.md](/C:/Workspace/nexra/docs/cloud-deployment.md)

## 1. 先部署后端

先把 Python 后端部署到服务器，确保下面地址可访问：

```text
https://api.nexra.example.com/api/dashboard
```

或者：

```text
http://YOUR_SERVER_IP:8080/api/dashboard
```

验证标准：

- `GET /api/dashboard` 返回 `200`
- `GET /api/skills?page=0&pageSize=5` 返回 `200`
- `POST /api/auth/login` 可以正常登录

## 2. 把前端部署到 Vercel

### 方式 1：Vercel 后台导入 Git 仓库

1. 打开 Vercel 控制台
2. 点击 `Add New Project`
3. 选择你的 Git 仓库
4. 填写项目配置：

- Framework Preset: `Other`
- Root Directory: `frontend`
- Build Command: 留空
- Output Directory: `.`
- Install Command: 留空

当前前端是纯静态 `HTML/CSS/JS`，不需要构建。

### 方式 2：用 Vercel CLI

```bash
npm i -g vercel
cd frontend
vercel
```

## 3. 配置 `/api` 代理

建议在项目根目录添加 `vercel.json`：

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": null,
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "https://api.nexra.example.com/api/:path*"
    }
  ]
}
```

如果你暂时还没有 HTTPS，也可以先写成：

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": null,
  "rewrites": [
    {
      "source": "/api/:path*",
      "destination": "http://YOUR_SERVER_IP:8080/api/:path*"
    }
  ]
}
```

这样用户访问：

- `https://your-project.vercel.app/api/skills`

Vercel 会把请求转发到你的真实后端。

## 4. 域名映射

推荐这样规划：

- 前端：`https://nexra.example.com`
- 后端：`https://api.nexra.example.com`

然后在 Vercel 上绑定前端域名，在 DNS 服务商那里把：

- `nexra.example.com` 指向 Vercel
- `api.nexra.example.com` 指向你的服务器或后端平台

## 5. 上线后验证

部署完成后按这个顺序检查：

1. 打开前端首页
   - `https://nexra.example.com`
2. 检查前端接口请求是否走 `/api`
3. 直接访问：
   - `https://nexra.example.com/api/dashboard`
4. 登录一个普通用户账号
5. 测试 skill 搜索、评分、提交 skill
6. 测试管理员登录和审核

## 6. 常见问题

### 页面能打开，但接口 404

通常是：

- 没有配置 `vercel.json`
- rewrite 目标地址写错
- 后端没有启动

### 接口超时

通常是：

- Vercel 能访问前端，但访问不到你的后端
- 服务器安全组没有放行端口
- 后端只绑定了本地回环地址

### 能读数据，但重启后状态丢失

当前 Python 后端默认把运行状态写入本地 JSON 文件。如果你部署的平台文件系统不持久，重启后状态会丢失。正式环境建议后续升级到真正数据库。

## 参考资料

- [Vercel Functions](https://vercel.com/docs/functions)
- [Vercel Runtimes](https://vercel.com/docs/functions/runtimes)
- [vercel.json](https://vercel.com/docs/project-configuration/vercel-json)
- [Rewrites](https://vercel.com/docs/rewrites)
- [Custom Domains](https://vercel.com/docs/projects/domains/add-a-domain)
