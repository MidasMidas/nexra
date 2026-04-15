# Nexra 使用文档

## 1. 产品说明

Nexra 是一个面向 AI Agent 的 skill 搜索、评分与推荐平台。当前第一期版本专注于 skill 发现、质量评分、推荐排序和治理能力，不做路由转发，也不替 Agent 直接调用第三方 skill。

当前重点能力：

- 每个 skill 同时拥有用户评分和系统自动评分
- 支持按关键词、功能、分类、调用方式搜索 skill
- 支持分页浏览 marketplace，并允许配置每页数量
- skill 详情包含 provider 信息、鉴权说明和调用示例
- 普通用户可以提交新的 skill
- 管理员可以审核、批准、修改、删除 skill
- 支持邮箱注册、登录和 token 校验
- 支持本地 JSON 持久化和云端 Postgres 持久化

## 2. 目录结构

- `backend_py/`：Python 后端
- `frontend/`：前端控制台
- `api/`：Vercel Python Function 入口
- `docs/usage-guide.md`：本使用文档
- `docs/product-spec.md`：产品设计文档
- `Start-Nexra.ps1`：启动脚本
- `Stop-Nexra.ps1`：停止脚本

## 3. 环境要求

- Python 3.9+

## 4. 首次使用

建议先复制本地配置模板：

```powershell
Copy-Item backend_py\config.example.json backend_py\config.json
Copy-Item .env.example .env.local
```

说明：

- `backend_py/config.example.json` 是公开模板
- `backend_py/config.json` 是你的本地私有配置，已经被 `.gitignore` 忽略
- `.env.local` 用来保存数据库等私有环境变量，也已经被 `.gitignore` 忽略
- 如果没有创建 `backend_py/config.json`，后端也会自动回退到 `backend_py/config.example.json`

## 5. 启动方式

可以直接用一键脚本：

```powershell
.\Start-Nexra.ps1
```

停止：

```powershell
.\Stop-Nexra.ps1
```

或者双击：

- `start-nexra.bat`
- `stop-nexra.bat`

启动后访问：

- 前端：[http://127.0.0.1:4173](http://127.0.0.1:4173)
- 后端 API：[http://localhost:8080/api](http://localhost:8080/api)

## 6. 身份与角色

当前使用邮箱注册和 token 登录。

公开认证接口：

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`

登录后，前端会自动携带：

- `Authorization: Bearer <token>`

除公开接口外，所有需要用户身份的接口都要求 token 校验。

## 7. Skill 搜索与分页

接口：

- `GET /api/skills`

支持参数：

- `q`：按名称、分类、描述、功能、调用方式搜索
- `function`：按功能搜索
- `page`：页码，从 `0` 开始
- `pageSize`：每页数量

示例：

```text
GET /api/skills?q=search&page=0&pageSize=10
GET /api/skills?function=report&page=0&pageSize=5
```

返回结果包含：

- 用户评分 `userRatingAvg`
- 系统评分 `systemScore`
- Agent 评分 `agentScore`
- 综合信任分 `overallTrust`
- 推荐分 `recommendationScore`
- 功能列表 `functions`
- 调用方式 `invocationMethod`
- provider 文档地址 `apiDocsUrl`
- 鉴权说明 `authRequirement`
- 提交人 `submittedBy`
- 审核状态 `approvalStatus`

## 8. Skill 详情与调用说明

接口：

- `GET /api/skills/{id}`

重点字段：

- `providerName`：skill 提供方
- `providerUrl`：provider 地址
- `apiDocsUrl`：官方文档地址
- `authRequirement`：鉴权要求说明
- `operatingSystem`：运行环境
- `callExample`：给 Agent 参考的调用示例

推荐使用流程：

1. Agent 先在 Nexra 搜索 skill。
2. 读取 skill 详情页中的评分、推荐理由和调用说明。
3. Agent 自己去调用 skill provider。
4. 用户再回到 Nexra 提交评分与评论。

## 9. 普通用户提交 Skill

接口：

- `POST /api/skills/submissions`

请求头：

- `Authorization: Bearer <token>`

提交后的 skill 会进入 `PENDING` 状态，等待管理员审核。

## 10. 管理员审核与维护 Skill

管理员接口：

- `GET /api/admin/skills/pending`
- `POST /api/admin/skills/{id}/approve`
- `PUT /api/admin/skills/{id}`
- `DELETE /api/admin/skills/{id}`
- `GET /api/admin/skills/sync/status`
- `POST /api/admin/skills/sync`

管理员可以：

- 查看待审核 skill
- 批准普通用户提交的 skill
- 修改 skill 的评分、功能、调用方式、描述、分类、价格等详细信息
- 删除 skill
- 手动触发一次 skill 同步

## 11. 评分系统说明

每个 skill 都有三类分值：

- `userRatingAvg`：用户评分
- `agentScore`：系统自动评分
- `overallTrust`：综合信任分

当前系统评分主要由成功率、延迟和成本效率共同计算。

## 12. 数据存储模式

本地开发默认使用：

- `backend_py/data/nexra-state.json`

云端部署推荐使用：

- `POSTGRES_URL` 或 `DATABASE_URL`

技能样本种子文件来自：

- `backend/src/main/resources/data/skills.json`

说明：

- 运行态数据和私有配置已经被 `.gitignore` 忽略
- 样本 skill 文件保留在仓库里，作为公开演示数据使用

## 13. 日志与运行状态

启动脚本会生成：

- `logs/backend.log`
- `logs/backend-error.log`
- `logs/frontend.log`
- `logs/frontend-error.log`
- `.runtime/nexra-services.json`

如果服务无法正常启动，优先看日志。

## 14. Vercel 部署模式

当前仓库已经包含 Vercel 所需文件：

- `api/index.py`
- `vercel.json`
- `requirements.txt`
- `runtime.txt`

推荐环境变量：

- `POSTGRES_URL`
- `NEXRA_STATE_BACKEND=postgres`
- `NEXRA_STATE_KEY=primary`

说明：

- 本地开发默认仍然用 JSON 状态文件
- Vercel 上建议使用 Postgres 持久化状态
- Vercel 的 serverless 运行环境不会长期持有后台线程，线上更适合手动触发同步
- 线上公开地址当前为 [https://nexra-one.vercel.app](https://nexra-one.vercel.app)
