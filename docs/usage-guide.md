# Nexra 使用文档

## 1. 产品说明

Nexra 是一个面向 AI Agent 的 skill 搜索、评分与推荐平台。当前版本优先完善评分系统、推荐系统与技能治理能力，暂时不做路由转发，也不负责替 Agent 执行 skill。

当前重点能力：

- 每个 skill 同时拥有用户评分和系统评分
- 支持按关键词和功能搜索 skill
- 支持 recommendationScore 推荐排序
- skill 列表支持分页，并可配置每页数量
- skill 详情提供 provider 文档、鉴权说明与调用示例
- 普通用户可以提交新的 skill
- 管理员可以审核、批准、修改、删除 skill
- 管理员可以修改评分和 skill 详细信息
- 系统会定时从公开 MCP 目录拉取新的 skill 样本

## 2. 目录结构

- [backend](C:\Workspace\nexra\backend)：Spring Boot 后端
- [frontend](C:\Workspace\nexra\frontend)：前端控制台
- [Start-Nexra.ps1](C:\Workspace\nexra\Start-Nexra.ps1)：启动脚本
- [Stop-Nexra.ps1](C:\Workspace\nexra\Stop-Nexra.ps1)：停止脚本
- [usage-guide.md](C:\Workspace\nexra\docs\usage-guide.md)：本使用文档
- [product-spec.md](C:\Workspace\nexra\docs\product-spec.md)：产品说明文档

## 3. 环境要求

- Java 17+
- Maven 3.9+
- Python 3.9+

## 4. 启动方式

首次使用前，建议先打包一次后端：

```powershell
cd .\backend
mvn package
cd ..
```

之后可以直接用一键脚本：

```powershell
.\Start-Nexra.ps1
```

停止：

```powershell
.\Stop-Nexra.ps1
```

或者双击：

- [start-nexra.bat](C:\Workspace\nexra\start-nexra.bat)
- [stop-nexra.bat](C:\Workspace\nexra\stop-nexra.bat)

启动后访问：

- 前端：[http://127.0.0.1:4173](http://127.0.0.1:4173)
- 后端 API：[http://localhost:8080/api](http://localhost:8080/api)

## 5. 身份与角色

当前是轻量级身份管理，使用请求头 `X-User-Id` 标识用户。

内置示例用户：

- `admin_1`：管理员
- `user_1`：普通用户
- `user_2`：普通用户

可通过接口查看：

- `GET /api/users`

## 6. Skill 搜索与分页

接口：

- `GET /api/skills`

支持参数：

- `q`：按 skill 名称、分类、描述、功能、调用方式搜索
- `function`：按 skill 功能搜索
- `page`：页码，从 `0` 开始
- `pageSize`：每页数量，可配置

示例：

```text
GET /api/skills?q=search&page=0&pageSize=10
GET /api/skills?function=report&page=0&pageSize=5
```

返回结果包含：

- 用户评分 `userRatingAvg`
- 系统评分 `systemScore`
- 总信任分 `overallTrust`
- 推荐分 `recommendationScore`
- 能力匹配分 `matchScore`
- 推荐原因 `recommendationSummary`
- 功能列表 `functions`
- 调用方式 `invocationMethod`
- provider 文档地址 `apiDocsUrl`
- 鉴权说明 `authRequirement`
- 提交人 `submittedBy`
- 审核状态 `approvalStatus`

## 6.1 Skill 详情与外部调用说明

接口：

- `GET /api/skills/{id}`

重点字段：

- `providerName`：skill 提供方
- `providerUrl`：provider 地址
- `apiDocsUrl`：官方文档地址
- `authRequirement`：鉴权要求说明
- `operatingSystem`：运行环境
- `callExample`：给 Agent 参考的调用示例

使用方式：

1. Agent 先在 Nexra 搜索 skill
2. 打开 skill 详情读取推荐信号和调用说明
3. Agent 自己去调用 provider
4. 人工回 Nexra 提交评分与评论

## 7. 普通用户提交 Skill

接口：

- `POST /api/skills/submissions`

请求头：

- `X-User-Id: user_1`

请求示例：

```json
{
  "name": "Alert Summarizer",
  "category": "Operations",
  "description": "Summarizes alerts into operator-ready incident notes.",
  "pricePerCall": 0.04,
  "functions": ["alert summarization", "incident notes"],
  "invocationMethod": "REST API with JSON body",
  "successRate": 88,
  "latencyP95": 530,
  "costEfficiency": 81,
  "recentCalls": 0
}
```

提交后的 skill 会进入 `PENDING` 状态，等待管理员审核。

## 8. 管理员审核与维护 Skill

管理员请求头：

- `X-User-Id: admin_1`

主要接口：

- `GET /api/admin/skills/pending`
- `POST /api/admin/skills/{id}/approve`
- `PUT /api/admin/skills/{id}`
- `DELETE /api/admin/skills/{id}`

管理员可以：

- 查看待审核 skill
- 批准普通用户提交的 skill
- 修改 skill 的评分、功能、调用方式、描述、分类、价格等详细信息
- 删除 skill

## 9. Skill 定时同步

系统内置了 skill 自动同步任务，会按固定周期从公开 MCP 目录拉取新的 skill 数据，并写回本地 skill 数据文件。

默认配置：

- 是否开启：`nexra.skill-sync.enabled=true`
- 目标数量：`nexra.skill-sync.target-count=3000`
- 首次延迟：`nexra.skill-sync.initial-delay-ms=900000`
- 固定周期：`nexra.skill-sync.fixed-delay-ms=43200000`
- 数据文件：`nexra.skills.data-file=backend/src/main/resources/data/skills.json`

管理员接口：

- `GET /api/admin/skills/sync/status`
- `POST /api/admin/skills/sync`

请求头：

- `X-User-Id: admin_1`

用途说明：

- `GET /status`：查看当前同步状态、最近一次执行时间、最近一次成功时间、当前已导入数量
- `POST /sync`：立即手动触发一次 skill 拉取和本地数据刷新

## 10. 评分系统说明

每个 skill 都有三类分值：

- `userRatingAvg`：用户评分
- `systemScore`：系统评分，来自成功率、延迟、成本效率
- `overallTrust`：综合信任分

当前系统评分仍基于：

```text
systemScore = 0.5 * success_rate + 0.3 * latency_score + 0.2 * cost_score
```

综合分与推荐分共同用于排序和推荐。

## 11. 前端说明

前端目前已支持：

- 欢迎页
- 教程页
- 中英文语言切换
- 教程中的请求头示例、curl、Python、JavaScript 示例
- 一键复制代码块

## 12. 日志与运行状态

启动脚本会生成：

- [logs/backend.log](C:\Workspace\nexra\logs\backend.log)
- [logs/backend-error.log](C:\Workspace\nexra\logs\backend-error.log)
- [logs/frontend.log](C:\Workspace\nexra\logs\frontend.log)
- [logs/frontend-error.log](C:\Workspace\nexra\logs\frontend-error.log)
- [.runtime/nexra-services.json](C:\Workspace\nexra\.runtime\nexra-services.json)

如果服务无法正常启动，优先看日志。
