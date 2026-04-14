# Nexra 部署到 Vercel 指南

这份文档说明怎么把 `Nexra` 部署到 `Vercel`。

先说结论：

- 当前这个项目的 `前端` 可以直接部署到 `Vercel`
- 当前这个项目的 `后端` 是 `Java + Spring Boot + H2 文件数据库`，不适合原样部署到 `Vercel`
- 最稳妥的方案是：
  - `前端部署到 Vercel`
  - `后端部署到云服务器 / Railway / Render / Fly.io`
  - 在 `Vercel` 上把 `/api` 重写到外部后端地址

## 为什么不能把当前后端直接部署到 Vercel

当前后端不建议直接放到 Vercel，主要有两个原因：

1. `Vercel Functions` 官方运行时以 `Node.js / Bun / Python / Rust` 等为主，没有把 `Spring Boot` 作为官方一等运行时来支持。  
来源：
- [Vercel Runtimes](https://vercel.com/docs/functions/runtimes)
- [Configuring the Runtime for Vercel Functions](https://vercel.com/docs/functions/configuring-functions/runtime)

2. 当前项目使用的是 `H2 文件数据库`，而 `Vercel Functions` 的文件系统是只读的，只提供临时 `/tmp` 空间，不适合持久保存 `nexra-db.mv.db`。  
来源：
- [Vercel Runtimes](https://vercel.com/docs/functions/runtimes)

所以，**当前项目不能把 Spring Boot + H2 这一套原样整包丢进 Vercel 就长期稳定运行**。

## 推荐部署架构

推荐你按下面这套方式部署：

```text
Browser
  -> Vercel Frontend
  -> /api rewrite
  -> External Spring Boot Backend
  -> H2 / PostgreSQL / MySQL
```

也就是：

- Vercel 负责静态前端页面
- Java 后端放在真正适合长进程运行的平台
- 前端仍然通过同域名 `/api` 访问接口
- Vercel 用 `rewrites` 把 `/api/*` 转发到你的后端

## 推荐的后端承载方式

当前项目最适合的后端承载方式：

1. 云服务器
   - 适合你现在已经有的 `deploy-cloud.sh`
   - 最容易保留 Spring Boot + H2
2. Railway / Render / Fly.io
   - 更接近托管型后端服务
   - 更适合后面升级到 PostgreSQL

如果你只是想先最快上线，建议：

- 前端：`Vercel`
- 后端：`Ubuntu 云服务器`

## 部署前要准备什么

你需要准备：

- 一个 `Vercel` 账号
- 一个 Git 仓库，里面有当前项目代码
- 一个已经能公网访问的后端地址，例如：
  - `https://api.nexra.example.com`
  - 或 `http://YOUR_SERVER_IP:8080`

如果你的后端还没部署，可以先参考：
- [cloud-deployment.md](/C:/Workspace/nexra/docs/cloud-deployment.md)

## 一、先部署后端

先把 Spring Boot 后端部署到云服务器或者别的后端平台，并确保下面这个地址能通：

```bash
http://YOUR_BACKEND/api/dashboard
```

或者：

```bash
https://api.nexra.example.com/api/dashboard
```

确认标准：

- `GET /api/dashboard` 返回 `200`
- `GET /api/skills?page=0&pageSize=5` 返回 `200`

## 二、把前端部署到 Vercel

### 方式 1：在 Vercel 后台导入 Git 仓库

1. 打开 Vercel 控制台
2. 点击 `Add New Project`
3. 选择你的 Git 仓库
4. 在项目配置里，建议这样填：

- Framework Preset: `Other`
- Root Directory: `frontend`
- Build Command: 留空
- Output Directory: `.`
- Install Command: 留空

原因是当前前端就是纯静态 HTML/CSS/JS，不需要构建。

### 方式 2：用 Vercel CLI

先安装 CLI：

```bash
npm i -g vercel
```

然后在项目根目录执行：

```bash
vercel
```

如果你只想把前端目录当成项目根目录，也可以：

```bash
cd frontend
vercel
```

## 三、配置 Vercel 代理 `/api`

为了让前端在 Vercel 上仍然通过 `/api` 访问你自己的 Spring Boot 后端，建议在项目根目录新增一个 `vercel.json`，内容类似这样：

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

如果你的后端还是 HTTP，也可以先这样：

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

说明：

- 用户访问 `https://your-frontend.vercel.app/api/skills`
- Vercel 会把请求转发到你的真实后端
- 浏览器地址栏不会变化

官方参考：
- [Rewrites on Vercel](https://vercel.com/docs/rewrites)
- [vercel.json](https://vercel.com/docs/project-configuration/vercel-json)

## 四、前端为什么现在可以这样工作

我已经把当前前端改成了：

- 本地开发时，默认请求 `http://localhost:8080/api`
- 部署到云上时，默认请求当前域名下的 `/api`

这意味着：

- 本地仍然不受影响
- 上线到 Vercel 后，只要你配置了 `/api` rewrite，就不需要再改前端代码

## 五、配置自定义域名

前端部署到 Vercel 后，你会先拿到一个：

- `https://your-project.vercel.app`

如果你要绑定自己的域名：

1. 进入 Vercel 项目
2. 打开 `Settings`
3. 打开 `Domains`
4. 添加你的域名，例如：
   - `nexra.example.com`
   - `www.nexra.example.com`

然后按 Vercel 提示添加 DNS 记录：

- 子域名通常用 `CNAME`
- Apex 根域通常用 `A` 记录

官方参考：
- [Adding & Configuring a Custom Domain](https://vercel.com/docs/projects/domains/add-a-domain)
- [Setting up a custom domain](https://vercel.com/docs/domains/set-up-custom-domain)

## 六、推荐的域名规划

推荐这样分：

- 前端：`https://nexra.example.com`
- 后端：`https://api.nexra.example.com`

然后在 Vercel 里做 rewrite：

- `/api/*` -> `https://api.nexra.example.com/api/*`

这样对用户来说仍然是一个统一站点。

## 七、上线后怎么验证

部署完成后，按下面顺序验证：

1. 打开前端首页
   - `https://nexra.example.com`
2. 看页面是否正常加载
3. 打开浏览器开发者工具，确认前端请求的是：
   - `/api/dashboard`
   - `/api/skills`
4. 直接访问：
   - `https://nexra.example.com/api/dashboard`
5. 确认返回 `200`
6. 测试登录、搜索、提审、管理员审核

## 八、常见问题

### 1. 为什么页面打开了，但接口 404

通常是因为：

- 没配 `vercel.json` rewrite
- rewrite 目标地址写错
- 后端 `/api` 没启动

### 2. 为什么接口超时

通常是因为：

- Vercel 能访问前端，但访问不到你的后端
- 后端云服务器安全组没放通
- 后端只监听了本地回环地址

### 3. 为什么不建议继续用 H2

如果只是演示，`H2` 可以继续用。  
如果你要正式对外提供服务，更建议换成：

- `PostgreSQL`
- `MySQL`

因为：

- 更稳定
- 更适合并发访问
- 更适合云环境备份和迁移

## 九、最简上线结论

如果你现在只想最快把这个项目挂到 Vercel，最可行的方式是：

1. 后端先部署到云服务器
2. 前端部署到 Vercel
3. Vercel 用 `rewrites` 代理 `/api`
4. 域名绑定到 Vercel 前端
5. 后端用独立子域名或服务器地址提供服务

## 参考资料

- [Vercel Functions](https://vercel.com/docs/functions)
- [Vercel Runtimes](https://vercel.com/docs/functions/runtimes)
- [Configuring the Runtime for Vercel Functions](https://vercel.com/docs/functions/configuring-functions/runtime)
- [Rewrites on Vercel](https://vercel.com/docs/rewrites)
- [vercel.json](https://vercel.com/docs/project-configuration/vercel-json)
- [Adding & Configuring a Custom Domain](https://vercel.com/docs/projects/domains/add-a-domain)
- [Setting up a custom domain](https://vercel.com/docs/domains/set-up-custom-domain)
