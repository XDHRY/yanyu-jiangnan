# Changelog

## 2026-09-22

- 修复 GitHub Actions 无头 Eevee 的 EGL/Mesa/Xvfb 运行环境，10 个 640×400 诊断机位现可在 Ubuntu runner 稳定生成并上传 artifact。
- 空间断言从对象数量升级为几何语义：月门路径连续性、端点距门洞、听雨轩踏步与台基接触、临水踏步跨越池岸，并验证月门路面净宽。
- 月洞门中心标高调整到 z=2.0；月门引路石改为承接曲水汀步 S 曲线的近铺地路径，曲水末石至首块引路石中心距收敛到 0.741m。
- 修正 03/06/07/09/10 诊断机位；06 不再被远竹/梅枝主遮挡，09 可同时观察屋顶、柱梁、台基和踏步。
- 修复诊断 manifest 的伪坐标问题：程序化 Mesh 现使用世界包围盒中心记录真实空间坐标，CI 会拒绝全零占位数据。
- gallery 新增当前空间诊断基线与关键指标，完整 10 图继续通过短期 Actions artifact 保存，避免仓库被每轮诊断图持续膨胀。

## 2026-09-20

- 停止以补齐大量正式机位为目标；`verify_render.py` 的正式静帧改为 `JN_FORMAL_RENDER=1` 显式启用。
- 新增 `tools/diagnostic_review.py` 与 **Jiangnan Spatial Diagnostic** 工作流：每轮输出 10 张低成本空间诊断图和机位 manifest。
- 第一轮空间修正新增 7 块月门引路石、3 级听雨轩入轩踏步、3 级临水踏步，并纳入 Blender 断言。
- `renders/gallery.html` 改为直接展示仓库已有正式图和构建过程图，不再用“待渲染”占位推动高成本渲染。
- 新增 `docs/iteration-loop.md`，把“观察 → 修改 → 再观察”的循环固化为项目协议。


## [1.0.0] - 2026-09-18

初始入库。场景与脚本由 Codex（OpenAI）于 2026-09-17/18 经 Blender MCP 工作流生成，本次提交完成归档整理：

### 场景本体
- 「烟雨江南 · 雪月江南」可编辑庭院：2745 对象 / 13.3 万顶点 / 23 材质 / 11 集合 / 3 机位 / 11 灯光 / 4461 条原生驱动器。
- 双天气互斥系统（烟雨 / 雪夜）+ 风力 0–2 总控，240 帧 / 24 fps 驱动动画。
- 7 张 image_gen albedo 贴图全部 pack 进 `.blend`，提示词存档于 `textures/generation_prompts.json` 与 `docs/art-direction.md`。

### 归档整理（相对 Codex 交付物的改动）
- 目录结构化：`textures/ renders/ validation/ tools/ progress/ docs/` 分区；中文文件名文档改为英文文件名（内容不变）。
- `jiangnan.py`：`output_dir` 由硬编码绝对路径改为「环境变量 `JN_OUT` → `.blend` 所在目录」可移植默认值；`render=True` 出图归入 `renders/` 子目录。
- `tools/verify_render.py`：输出路径同步可移植化；渲染图写入 `renders/`、验证记录写入 `validation/`。
- `renders/gallery.html`：链接适配新结构；三张待渲染机位以占位块明示，雪月切换待 `04_snow_front.png` 完成后启用。
- `.blend` 文本数据块内嵌的 `jiangnan.py` 仍为 Codex 交付时快照；下次重建时会被权威副本自动覆盖同步。

### 已知待办
- 其余三机位渲染（02_snow_top / 03_rain_three_quarter / 04_snow_front）。
- GPU 渲染配置与 240 帧样片。
