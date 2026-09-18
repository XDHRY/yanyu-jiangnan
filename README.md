# 烟雨江南 · 雪月江南

> 致虚极，守静笃 —— 一庭月色，半池灯影。听雨轩前，梅枝随风。

*A fully procedural, editable Jiangnan night courtyard in Blender — moon gate, leaning plum trees, still water and a rain-listening pavilion. One script builds everything; no external game assets.*

![正面 · 烟雨](renders/01_rain_front.png)

## 这是什么

一座可步入、可停留、可整体重建的江南夜庭院，由单个 Blender Python 脚本（`jiangnan.py`，约 40KB）全参数化生成：

- **场景**：粉墙月洞门（真实贯通几何）、斜梅两株、静水池与汀步、听雨轩、石灯茶案、太湖石三尊、云月与远山。
- **双天气一键切换**：烟雨（细雨/涟漪/湿石）与雪夜（飘雪/瓦上薄雪/残雪）互斥切换，风力 0–2 可调。
- **原生驱动动画**：4444 条对象驱动器，240 帧 / 24 fps，花枝摇摆、露珠随枝、雨雪下落、云移水动，无外部缓存。
- **AI 贴图**：7 张 albedo 贴图（粉墙/苔石/梅皮/黛瓦/老木/花瓣/远山夜景）由 image_gen 按存档提示词生成；Blender 4.5 CI 从源码重建时会全部 pack 进新生成的 `.blend`。
- **可验证交付**：`tools/verify_render.py` 内置 7 项断言（天气互斥、帧间动态、驱动器有效性、贴图打包、法线朝向等）。

Blender 4.5.14 CI 重建基线：2924 对象（1464 网格 + 1404 曲线）/ 183539 顶点 / 137577 面 / 22 材质 / 11 集合 / 3 机位 / 11 灯光 / 4444 对象驱动器（详见 `validation/scene_statistics.json`）。

## 快速开始

1. 推荐从 GitHub Actions 的 **Blender 4.5 Scene Smoke** 下载与当前 commit 绑定的 `Jiangnan-Blender-4.5-*` artifact；其中的 `Jiangnan.blend` 是由当前源码和 `textures/` 从零重建并通过断言的可验证产物。
2. 也可以用 **Blender 4.5 LTS** 直接运行 `jiangnan.py` 全量重建。根目录现有 `Jiangnan.blend` 保留为历史预览快照，不再视为权威构建产物。
3. 若提示禁用驱动表达式，选择信任并启用脚本自动运行；播放时间轴（1–240 帧）查看动态，并在 `JN_总控_天气0雨1雪_风力` 上切换 `Weather`（0 雨 / 1 雪）与 `Wind`（0–2）。
4. 浏览器打开 `renders/gallery.html` 查看静帧预览页。

更多操作细节见 [docs/usage.md](docs/usage.md)。

## 重建与二次开发

```python
# 在 Blender 文本编辑器中打开 jiangnan.py 直接运行即可全量重建。
# 顶部 PARAMS 集中管理：seed / weather / wind / blossom_density /
# rain_count / snow_count / resolution / samples / stage / render / output_dir
```

- `stage` 1–5 分阶段构建（庭院→植被→雨雪→天空→灯光），调试用低 stage 更快。
- `render=True` 时构建完成后自动渲染正面、顶视、三分之四三个机位到 `renders/`。
- 输出目录默认取当前 `.blend` 所在目录（仓库内即根目录），需有 `textures/` 子目录；可用环境变量 `JN_OUT` 覆盖。

升级路线、脚本契约与验证清单见 [docs/development.md](docs/development.md)；贴图与美术标准见 [docs/art-direction.md](docs/art-direction.md)。

## 目录结构

```
├── Jiangnan.blend     # 历史预览快照；权威可验证产物由 CI 从源码重建
├── jiangnan.py        # 生成脚本 · 权威副本
├── textures/          # 7 张贴图 + 生成提示词存档
├── renders/           # 正式静帧 + gallery.html 预览页
├── validation/        # 场景统计与验证记录
├── tools/             # verify_render.py（验证 + 四机位出图）
├── progress/          # 构建过程图与渲染日志
└── docs/              # usage / art-direction / development
```

## 当前状态与路线

- [x] Blender 4.5.14 CI 从源码全量重建，并通过天气/动态/驱动/贴图打包/法线等场景断言（2026-09-18）
- [x] 正面烟雨静帧 `01_rain_front.png`
- [ ] 其余三机位（顶视雪 / 三分之四雨 / 正面雪）—— 运行 `tools/verify_render.py` 补齐，详见 development 指南 §3.1
- [ ] GPU 渲染配置与 240 帧样片

完整变更记录见 [CHANGELOG.md](CHANGELOG.md)。

## 致谢与许可

- 场景与脚本由 **OpenAI Codex** 经 Blender MCP 工作流生成（2026-09-17/18），灵感方向参考《燕云十六声》与《黑神话：悟空》的美术气质；工作流参考 [newo-ether/blender-mcp](https://github.com/newo-ether/blender-mcp)、[hassledzebra/codex_blender_mcp](https://github.com/hassledzebra/codex_blender_mcp)、[PatrykIti/blender-ai-mcp](https://github.com/PatrykIti/blender-ai-mcp)。
- 本仓库为私人项目存档，未附带开源许可；如需引用请先联系所有者。
