# Nexra

[English](./README.md) | **中文**

Nexra 是一个开源的 AI Skill 搜索、评分与推荐平台。

它解决的是调用前的关键问题：应该信任哪个 skill，为什么推荐它，以及 Agent 应该如何调用它。

当前公开演示地址：

- Web: [https://nexra-one.vercel.app](https://nexra-one.vercel.app)
- API: [https://nexra-one.vercel.app/api/dashboard](https://nexra-one.vercel.app/api/dashboard)

## 为什么是 Nexra

AI 工具生态正在快速膨胀。Skill、MCP Server、API 封装、插件和代理工具越来越多，大多数团队很难靠人工逐个评估。

Nexra 把这些能力整理成一个带有信任信号的 skill marketplace：

- 按关键词、功能、分类、调用方式和可用性搜索 skill
- 区分用户评分和系统自动评分
- 按匹配度、信任度、热度和成本效率进行推荐排序
- 展示 provider 文档、鉴权说明和调用示例
- 支持普通用户提交 skill，管理员审核后再进入 marketplace

当前阶段的 Nexra 不做第三方 skill 的代理执行，而是帮助 Agent 找到正确的 skill，再由 Agent 自己去调用 provider。

## 适合谁使用

- 正在构建 skill 型 Agent 的 AI 产品团队
- 需要 marketplace 和审核流程的 Agent 平台开发者
- 希望建设内部 skill 目录和治理能力的运维团队
- 正在探索 MCP 生态和外部工具调用体系的开发者

## 核心能力

- 带搜索和分页的 skill marketplace
- 每个 skill 都有用户评分和 agent/system 评分
- 推荐排序和推荐理由展示
- skill 详情页展示 provider 信息和调用指引
- 支持邮箱注册和 token 登录
- 普通用户提交新 skill
- 管理员审核、修改、删除 skill
- 前端支持中英文引导
- 本地可用 JSON 状态存储，线上可切换 Postgres

## 当前产品范围

当前已经支持：

- Skill 搜索
- Skill 推荐
- Skill 评分和评论
- Skill 治理和审核
- 用户注册、登录和个人信息

当前明确不做：

- 路由转发
- 代表 Agent 执行第三方 skill
- 作为 skill 的代理调用层

## 使用场景

- Agent 开发者想找一个更适合改写、总结、写作的 skill
- 团队希望让真实用户给 skill 体验打分
- 管理员希望在 skill 对外展示前进行审核
- 平台想在 Agent 接入第三方能力前先建立信任层

## 项目结构

- `frontend/`: marketplace、引导页、教程页和管理界面
- `backend_py/`: 分层 Python 后端
- `api/`: Vercel Python Function 入口
- `docs/`: 使用、部署和产品文档

技术栈：

- 前端：HTML、CSS、JavaScript
- 后端：Python
- 部署：Vercel
- 存储：本地 JSON，线上 Postgres

## 快速开始

### 1. 准备本地配置

```powershell
Copy-Item backend_py\config.example.json backend_py\config.json
Copy-Item .env.example .env.local
```

### 2. 启动项目

```powershell
.\Start-Nexra.ps1
```

启动后访问：

- 前端：`http://127.0.0.1:4173`
- 后端 API：`http://localhost:8080/api`

停止：

```powershell
.\Stop-Nexra.ps1
```

## 主要接口

公开和用户接口：

- `GET /api`
- `GET /api/agent-guide`
- `GET /api/dashboard`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/skills?q=&function=&page=&pageSize=`
- `GET /api/skills/{id}`
- `POST /api/skills/{id}/reviews`
- `POST /api/skills/submissions`
- `GET /api/users/me`

管理员接口：

- `GET /api/admin/skills/pending`
- `POST /api/admin/skills/{id}/approve`
- `PUT /api/admin/skills/{id}`
- `DELETE /api/admin/skills/{id}`
- `GET /api/admin/skills/sync/status`
- `POST /api/admin/skills/sync`

## 部署

仓库已经准备好了 Vercel 部署所需文件：

- `api/index.py`
- `vercel.json`
- `requirements.txt`
- `runtime.txt`

推荐环境变量：

- `POSTGRES_URL`
- `NEXRA_STATE_BACKEND=postgres`
- `NEXRA_STATE_KEY=primary`

说明：

- Vercel 不提供固定 `IP + port`
- 线上访问应使用域名

## 开源发布约定

这个仓库已经按开源方式清理过：

- 本地私密配置已忽略
- 本地运行日志和快照已忽略
- 本地图片 `硬件参数.png` 已忽略，不会上传
- 保留了公开的样本 skill 数据，方便其他开发者快速运行

应仅保留在本地的文件：

- `.env.local`
- `backend_py/config.json`
- `backend_py/data/nexra-state.json`
- `.runtime/`
- `logs/`
- `硬件参数.png`

模板文件：

- `.env.example`
- `backend_py/config.example.json`

## 推荐的 GitHub 仓库描述

`Open-source AI skill marketplace for discovery, scoring, recommendation, and governance.`

## 推荐的 GitHub Topics

- `ai`
- `agent`
- `ai-agents`
- `marketplace`
- `mcp`
- `skill-discovery`
- `recommendation-system`
- `python`
- `vercel`
- `postgres`

## 文档

- [使用文档](./docs/usage-guide.md)
- [Vercel 部署文档](./docs/vercel-deployment.md)
- [云服务器部署文档](./docs/cloud-deployment.md)
- [产品设计文档](./docs/product-spec.md)

## 参与贡献

欢迎贡献。

适合作为 first contribution 的方向：

- 优化推荐排序策略
- 提升管理员审核体验
- 增加更多语言支持
- 提升 skill 导入和去重质量
- 优化新用户引导和教程体验

详情见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## License

MIT License. See `LICENSE`.
