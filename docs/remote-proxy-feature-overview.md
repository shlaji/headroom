# 远端代理分支功能概览

本文概述 `feat/remote-proxy-integration` 相对 `main` 的主要变化，重点说明各项功能解决的问题及适用边界。它不是完整的安装或命令手册。

## 远端代理模式

以往 `headroom wrap` 默认在本机启动或复用 Headroom 代理。新模式通过 `HEADROOM_REMOTE_PROXY_URL` 让受支持的包装器把客户端流量直接发往已有的远端 Headroom 代理，因此本地命令不再负责启动、监控或关闭代理进程。远端地址可以带基础路径，项目归属前缀会接在该路径之后；OpenAI 兼容客户端仍会使用 `/v1` 路径。

`HEADROOM_REMOTE_PROXY_URL` 只回答“wrap 把客户端请求发到哪里”。它必须是绝对的 HTTP 或 HTTPS URL，不能包含查询参数或片段。该变量不同于 `HEADROOM_FORCE_OPENAI_TARGET`，后者控制代理收到 OpenAI 请求后选择哪个上游，见后文。

启动包装器时会探测远端 `/health`。探测失败只输出警告，不会阻止客户端启动，因此它不能替代部署侧的可用性检查。部分包装流程会写入持久客户端配置，这些配置可能在命令结束后继续指向远端 URL，直到后续配置操作将其覆盖。

## 支持的集成与前置保护

远端模式当前只支持以下 `wrap` 集成：

* Claude
* Codex
* OpenCode
* Aider
* Cursor
* Cline
* Continue
* Goose
* OpenHands

其他集成会在进入具体设置流程前被拒绝，避免先写配置、注册 MCP 或清理工具，再因远端模式不兼容而失败。本地代理模式不受这份允许列表限制。

两条路径即使属于上述集成，也明确不兼容：

* Claude 的 Vertex 和 Foundry 路由模式仍需使用标准本地代理路径。
* OpenCode 的 Copilot 订阅模式需要注入凭据的私有本地代理，不能与 `HEADROOM_REMOTE_PROXY_URL` 同时使用。

## 强制 OpenAI 目标路由

`HEADROOM_FORCE_OPENAI_TARGET` 解决共享或集中代理需要由运维方固定 OpenAI 兼容上游的问题。它默认关闭。关闭时，请求可通过请求级上游信息选择目标，Codex 的 ChatGPT 订阅身份也会触发 ChatGPT 后端路由。

开启后，OpenAI 处理路径统一使用代理配置的目标，也就是 `OPENAI_TARGET_API_URL` 或对应的代理配置值。请求携带的 `x-headroom-base-url` 不再覆盖该目标，Codex 的 ChatGPT 身份提示也不再把 HTTP 或 WebSocket 请求改送到 ChatGPT 后端。该开关只约束代理的 OpenAI 上游选择，不决定 wrap 连接本地代理还是远端代理。

## 可信 Dashboard CIDR 管理端点扩展

`HEADROOM_PROXY_TRUSTED_DASHBOARD_CLIENT_CIDRS` 及可信客户端识别机制在 `main` 上已经存在。本分支没有新增这个配置，而是把既有的可信 Dashboard 客户端访问许可扩展到更多原先只允许 loopback 的管理与观测路由，解决 Dashboard 经可信网关或远端网络访问时无法使用这些功能的问题。

本分支扩展的读取端点包括：

* `GET /health`：可信客户端可查看原本仅 loopback 响应中的配置详情。
* `GET /admin/upstream`。
* `GET /debug/tasks`、`/debug/ws-sessions`、`/debug/warmup`、`/debug/memory`。
* `GET /transformations/feed`。
* `GET /v1/retrieve/stats`、`/v1/feedback`、`/v1/feedback/{tool_name}`。
* `GET /v1/telemetry`、`/v1/telemetry/export`、`/v1/telemetry/tools`、`/v1/telemetry/tools/{signature_hash}`。
* `GET /v1/toin/stats`、`/v1/toin/patterns`、`/v1/toin/pattern/{hash_prefix}`。
* `GET /v1/retrieve/{hash_key}`。

本分支也允许可信 Dashboard 客户端访问以下写入或状态变更端点：`POST /admin/runtime-env`、`/stats/reset`、`/cache/clear`、`/v1/retrieve`、`/v1/telemetry/import` 和 `/v1/retrieve/tool_call`。这些写操作仍执行同源校验；可信 CIDR 不会使跨源请求自动通过。应将允许网段视为管理权限边界，并确保代理获得的客户端地址可信。

## 辅助维护与文档变更

本分支还包含少量不改变代理运行语义的维护工作：

* 新增面向编码代理的跨会话记忆指引，要求先查询既有决策，并保存可长期复用的项目知识。
* 扩充本地状态忽略规则，覆盖代理工具目录和 CodeGraph 产生的临时文件，减少误提交。
* 新增 `wrap.py` 差异最小化规则，强调以环境状态和底层拦截实现远端兼容，避免大范围控制流改写，并要求使用聚焦回归检查。

这些内容用于约束开发和仓库卫生，不应与远端代理、上游固定或 Dashboard 访问控制等运行时功能混为一谈。
