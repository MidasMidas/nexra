# Nexra

[English](./README.md) | **中文**

Nexra 是一个面向 AI Skill 搜索、评分与推荐的开放平台。

使用 Nexra 的正确方式，应该是直接调用 Nexra 平台提供的在线接口，而不是先下载这个仓库到本地部署。

## 在线使用 Nexra

从这里开始：

- Web 应用: [https://nexra-one.vercel.app](https://nexra-one.vercel.app)
- API 基地址: [https://nexra-one.vercel.app/api](https://nexra-one.vercel.app/api)
- Dashboard 示例: [https://nexra-one.vercel.app/api/dashboard](https://nexra-one.vercel.app/api/dashboard)
- Agent 使用说明: [https://nexra-one.vercel.app/api/agent-guide](https://nexra-one.vercel.app/api/agent-guide)

如果你想让自己的 agent 使用 Nexra，推荐流程是：

1. 先调用 Nexra 的 API 搜索 skill。
2. 读取返回的评分、推荐信号和 provider 信息。
3. 选择合适的 skill。
4. 让 agent 自己去调用该 skill provider。
5. 再把评分和反馈提交回 Nexra。

当前阶段的 Nexra 不是 skill 的代理执行层，而是 skill 发现、推荐和治理平台。

## Nexra 能帮你做什么

- 按关键词、功能、分类、调用方式和可用性搜索 skill
- 区分用户评分和系统自动评分
- 按匹配度、信任度、热度和成本效率进行排序推荐
- 查看 provider 文档、鉴权说明和调用示例
- 提交新的 skill 进入审核流程
- 通过管理员流程审核、修改和下架 skill

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

## 使用场景

- Agent 开发者想找一个更适合改写、总结、写作的 skill
- 团队希望让真实用户给 skill 体验打分
- 管理员希望在 skill 对外展示前进行审核
- 平台想在 Agent 接入第三方能力前先建立信任层

## 适合谁使用

- 正在构建 skill 型 Agent 的 AI 产品团队
- 需要 marketplace 和审核流程的 Agent 平台开发者
- 希望建设内部 skill 目录和治理能力的运维团队
- 正在探索 MCP 生态和外部工具调用体系的开发者

## 自托管与本地开发

这个仓库主要面向贡献者、自托管部署者和本地开发者。

只有在以下情况你才需要直接使用源码：

- 你想参与 Nexra 开发
- 你想自托管自己的 Nexra 实例
- 你想修改前后端逻辑
- 你想在本地跑完整开发环境

本地开发方式：

```powershell
Copy-Item backend_py\config.example.json backend_py\config.json
Copy-Item .env.example .env.local
.\Start-Nexra.ps1
```

启动后：

- 前端: `http://127.0.0.1:4173`
- 本地 API: `http://localhost:8080/api`

## 项目结构

- `frontend/`: 用户界面
- `backend_py/`: 分层 Python 后端
- `api/`: Vercel Python Function 入口
- `docs/`: 使用、部署和产品文档

技术栈：

- 前端：HTML、CSS、JavaScript
- 后端：Python
- 部署：Vercel
- 存储：本地 JSON，线上 Postgres

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

## 开源与隐私说明

这个仓库已经按开源方式清理过：

- 本地私密配置已忽略
- 本地运行日志和快照已忽略
- 本地图片 `硬件参数.png` 已忽略，不会上传

应仅保留在本地的文件：

- `.env.local`
- `backend_py/config.json`
- `backend_py/data/nexra-state.json`
- `.runtime/`
- `logs/`
- `硬件参数.png`

## 文档

- `docs/usage-guide.md`
- `docs/vercel-deployment.md`
- `docs/cloud-deployment.md`
- `docs/product-spec.md`

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

## 参与贡献

欢迎贡献。详情见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## License

MIT License. See `LICENSE`.
