# Nexra 使用文档

本文档只说明如何使用 Nexra 在线平台，不包含下载、本地部署或云端部署步骤。

## 1. 平台定位

Nexra 是一个面向 AI Agent 的 skill 搜索、评分与推荐平台。当前版本重点提供 skill 发现、质量评分、推荐排序和调用说明，不做路由转发，也不替 Agent 直接调用第三方 skill。

## 2. 在线入口

- Web 应用: [https://nexracat.com](https://nexracat.com)
- API 基地址: [https://nexracat.com/api](https://nexracat.com/api)
- Dashboard: [https://nexracat.com/api/dashboard](https://nexracat.com/api/dashboard)
- Agent 使用说明: [https://nexracat.com/api/agent-guide](https://nexracat.com/api/agent-guide)

## 3. 主要能力

- 搜索 skill
- 查看用户评分和系统评分
- 查看 provider 文档、鉴权要求和调用示例
- 提交新 skill
- 给 skill 打分和写评论

## 4. 注册与登录

认证接口：

- `POST /api/auth/register/request-code`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`

注册流程：

1. 调用 `POST /api/auth/register/request-code` 发送验证码。
2. 到注册邮箱查收验证码。
3. 调用 `POST /api/auth/register`，并提交 `verificationCode`。
4. 注册成功后使用 `POST /api/auth/login` 登录。

登录后，受保护接口需要携带：

- `Authorization: Bearer <token>`

## 5. Skill 搜索

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

返回结果通常包含：

- `userRatingAvg`
- `systemScore`
- `agentScore`
- `overallTrust`
- `recommendationScore`
- `functions`
- `invocationMethod`
- `apiDocsUrl`
- `authRequirement`

## 6. Skill 详情

接口：

- `GET /api/skills/{id}`

重点字段：

- `providerName`
- `providerUrl`
- `apiDocsUrl`
- `authRequirement`
- `operatingSystem`
- `callExample`

推荐使用流程：

1. 先搜索 skill。
2. 查看评分、推荐理由和调用说明。
3. 选择 skill。
4. 让 Agent 自己调用对应 skill provider。
5. 完成后再回 Nexra 打分和评论。

## 7. 用户提交与评分

接口：

- `POST /api/skills/submissions`
- `POST /api/skills/{id}/reviews`
- `GET /api/users/me`

说明：

- 普通用户可以提交 skill
- 普通用户可以给 skill 打分和评论
- 个人中心可以查看自己提交过的 skill 和评分记录

## 8. 评分系统

每个 skill 都有三类核心分值：

- `userRatingAvg`：用户评分
- `agentScore`：系统自动评分
- `overallTrust`：综合信任分

## 9. 邮箱验证码说明

当前平台使用邮箱验证码完成注册确认。

如果你没有收到验证码邮件：

1. 先检查垃圾邮箱。
2. 再重新发送验证码。
3. 如果仍然没有收到，再联系平台管理员检查邮件服务状态。

## 10. 公开接口总览

- `GET /api`
- `GET /api/agent-guide`
- `GET /api/dashboard`
- `POST /api/auth/register/request-code`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/skills`
- `GET /api/skills/{id}`
- `POST /api/skills/{id}/reviews`
- `POST /api/skills/submissions`
- `GET /api/users/me`
