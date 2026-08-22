# 阶段 2：项目探索

## 目标

以只读方式建立项目清单和证据地图，避免从目录名直接生成产品事实。

## 扫描策略

先用 `rg --files` 建立候选集合，再用针对性 `rg` 查看入口、路由、菜单、命令、配置、错误类型和测试。默认排除 `.git`、`node_modules`、`vendor`、`dist`、`build`、`coverage`、缓存和生成文档。

按软件类型选择探索角度：

- Web：架构、页面/路由、导航、角色权限、API 客户端、配置。
- CLI：命令树、选项、输入输出、退出码、配置。
- SDK/库：公共导出、类型、示例、兼容性、异常。
- Desktop：窗口、菜单、关键工作流、配置、存储位置。
- Service/API：入口、路由、鉴权、schema、部署、监控。
- Monorepo：先固定目标 workspace，仅跟踪必要依赖，不扫描其他产品。

## 并行规则

如果探索面彼此独立，可把架构、界面、API、配置分配给不同子智能体。主 Agent 先声明范围和输出路径；每个子智能体只写一个唯一 JSON。建议返回：

```json
{
  "status": "completed",
  "output_file": "/abs/path/exploration-ui.json",
  "evidence_count": 12,
  "key_findings": ["..."],
  "gaps": [],
  "warnings": []
}
```

## 证据记录

每个发现至少记录：`claim`、`source_file`、`line`（可得时）、`evidence_type`、`confidence`。运行态证据另记录命令、URL 或测试名称。不要把秘密内容写进探索文件。

## 输出

`exploration/` 至少包含架构清单；其他文件按实际项目生成。主 Agent 汇总成 `evidence-map.json`，供所有章节共享。
