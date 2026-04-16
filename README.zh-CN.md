# Nexra

[English](./README.md) | **中文**

Nexra 是一个面向 AI Skill 搜索、评分与推荐的在线平台。

请直接通过 Nexra 在线产品和 API 使用它：

- Web 应用: [https://nexracat.com](https://nexracat.com)
- API 基地址: [https://nexracat.com/api](https://nexracat.com/api)
- Dashboard: [https://nexracat.com/api/dashboard](https://nexracat.com/api/dashboard)
- Agent 使用说明: [https://nexracat.com/api/agent-guide](https://nexracat.com/api/agent-guide)

## Nexra 能做什么

- 按关键词、功能、分类、调用方式和可用性搜索 skill
- 分开展示用户评分和系统自动评分
- 按相关度、信任度、热度和成本效率排序推荐
- 展示 provider 文档、鉴权要求和调用示例
- 支持用户提交 skill 和评分评论
- 支持管理员审核和批准 skill

当前阶段的 Nexra 不是 skill 代理执行层。Agent 在 Nexra 找到 skill 后，需要自己去调用对应 provider。

## 主要接口

公开和用户接口：

- `GET /api`
- `GET /api/agent-guide`
- `GET /api/dashboard`
- `POST /api/auth/register/request-code`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/skills?q=&function=&page=&pageSize=`
- `GET /api/skills/{id}`
- `POST /api/skills/{id}/reviews`
- `POST /api/skills/submissions`
- `GET /api/users/me`

管理员接口：

- `GET /api/admin/skills?status=PENDING|APPROVED|REJECTED&q=&page=&pageSize=`
- `POST /api/admin/skills/{id}/approve`
- `POST /api/admin/skills/{id}/reject`
- `PUT /api/admin/skills/{id}`
- `DELETE /api/admin/skills/{id}`
- `GET /api/admin/skills/sync/status`
- `POST /api/admin/skills/sync`

## Agent 典型使用流程

1. 先在 Nexra 搜索 skill。
2. 读取评分、推荐分和 provider 说明。
3. 选择合适的 skill。
4. Agent 自己去调用对应 provider。
5. 再把评分和反馈提交回 Nexra。

## 文档

- [平台使用文档](./docs/usage-guide.md)
- [产品设计文档](./docs/product-spec.md)

## 参与贡献

欢迎贡献。详情见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## License

MIT License. See `LICENSE`.
