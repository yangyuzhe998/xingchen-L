---
name: weather
description: 使用 curl 和 wttr.in 获取指定地点的当前天气信息。
---

# 天气技能

使用此技能查询任何地点的天气。

## 用法

要获取某个城市的天气，请在终端执行以下命令：

```bash
curl -s "wttr.in/{City}?format=3"
```

### 参数
- `{City}`: 城市名称 (例如: Beijing, London, New_York)。空格请使用 `+` 或 `_` 代替。

### 示例

查询北京的天气:
```bash
curl -s "wttr.in/Beijing?format=3"
```

查询纽约的天气:
```bash
curl -s "wttr.in/New_York?format=3"
```
