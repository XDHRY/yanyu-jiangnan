# 二次开发与升级指南

本文面向后续维护者（含 AI 代理），说明仓库布局、脚本契约、常见升级路径与验证清单。阅读顺序建议：先 `README.md` 看总览，再 `docs/usage.md` 学操作，最后读本指南动手改。

## 1. 仓库布局与脚本契约

```
yanyu-jiangnan/
├── Jiangnan.blend        # 主场景（Cycles，2745 对象，见 validation/scene_statistics.json）
├── Jiangnan.blend1       # Blender 自动备份快照（上一存盘态，可删）
├── jiangnan.py           # 生成脚本 · 唯一权威副本（约 40KB，单文件全参数化）
├── textures/             # 7 张 image_gen 贴图 + generation_prompts.json
├── renders/              # 正式渲染静帧 + gallery.html 预览页
├── validation/           # scene_statistics.json / validation.json
├── tools/
│   └── verify_render.py  # 验证 + 四机位出图脚本（在 Blender 内运行）
├── progress/             # 构建过程记录（过程图 / 渲染日志）
└── docs/                 # usage.md / art-direction.md / 本文
```

**核心契约：`output_dir` = 仓库根目录。**

- `jiangnan.py` 从 `<output_dir>/textures/` 读取贴图（`art_upgrade()` 映射），向 `<output_dir>` 写出 `Jiangnan.blend`、`scene_statistics.json`，向 `<output_dir>/renders/` 写渲染图。
- 两个脚本的输出目录都默认取「当前打开的 `.blend` 所在目录」，仓库内 `Jiangnan.blend` 位于根目录，因此打开即满足契约；也可用环境变量 `JN_OUT` 显式覆盖。
- `.blend` 文本数据块内嵌的 `jiangnan.py` 是生成时快照；每次重建时 `deliver()` 会把 `output_dir` 下的权威脚本重新嵌入，二者自动同步。

## 2. 场景结构速查

- 命名前缀：所有生成资产带 `JN_` 前缀；集合 `JN_00_总控` 至 `JN_10_验证相机` 共 11 个。
- 总控对象 `JN_总控_天气0雨1雪_风力`：自定义属性 `Weather`（0 雨 / 1 雪，驱动 `hide_render` 互斥切换）与 `Wind`（0–2，驱动梅枝摇摆与雪粒横飘幅度）。
- 动画：原生驱动器（4461 条），无外部缓存；时间轴 1–240 帧 / 24 fps，非严格无缝循环。
- 相机三机位：`JN_正面`、`JN_顶视`（正交）、`JN_三分之四`（默认活动相机）。
- 脚本分阶段：`stage` 1 庭院 → 2 植被 → 3 雨雪 → 4 天空 → 5 灯光氛围（含 `art_upgrade` 贴图精修）。调 bug 时可低 stage 快速重建。

## 3. 常见升级路径

### 3.1 补齐剩余三机位渲染（当前最优先）

交付时仅完成 `renders/01_rain_front.png`（148 秒 / 帧，Cycles CPU 1600×1000@96spp）。补齐方法：在打开 `Jiangnan.blend` 的 Blender 中运行 `tools/verify_render.py`，将依次产出：

| 文件 | 机位 | 天气 |
|---|---|---|
| `renders/01_rain_front.png` | 正面 | 雨 |
| `renders/02_snow_top.png` | 顶视 | 雪 |
| `renders/03_rain_three_quarter.png` | 三分之四 | 雨 |
| `renders/04_snow_front.png` | 正面 | 雪 |

完成后：`renders/gallery.html` 中删除雪月按钮的 `disabled` 属性、把两个「待渲染」占位块换成对应 `<figure>` 即可。`verify_render.py` 同时会重写 `validation/validation.json` 并把场景另存回根目录 `Jiangnan.blend`。

### 3.2 调整场景参数

改 `jiangnan.py` 顶部 `PARAMS`（种子、花量、雨雪密度、风力、分辨率、采样），在 Blender 文本编辑器运行 `jiangnan.py` 即全量重建同名场景。注意：重建只替换 `JN_` 前缀资产，手工改动请放在非 `JN_` 对象上，或重建前另存。

### 3.3 重新生成 / 更换贴图

贴图全部为内置 image_gen 生成的 albedo，提示词存档于 `textures/generation_prompts.json` 与 `docs/art-direction.md`。更换流程：

1. 按提示词风格重新生成 PNG（四方连续、平光、无烘焙阴影）。
2. 以同名放进 `textures/`（`plaster/stone/bark/clay/wood/petal/landscape` 之一）。
3. 重建场景：`art_upgrade()` 中的 `image_material(key, asset, scale, ...)` 按文件名映射到材质；`scale` 控制 UV 平铺尺度。
4. 新增贴图时，在 `art_upgrade()` 追加一行 `image_material` 调用，并在 `generation_prompts.json` 与 `docs/art-direction.md` 补录提示词。

### 3.4 新增构件 / 集合

- 在 `jiangnan.py` 对应 stage 函数中追加几何（`mesh/box/uv/line` 四个基元函数），命名必须带 `JN_` 前缀并挂入正确集合。
- 新集合需在 `start()` 的集合清单注册（保持 `NN_名称` 编号连续）。
- 需要随风摆动的部件，参考 `driven()` 挂驱动器，属性只取 `Wind`/`Weather` 两个总控量。

### 3.5 渲染视频

`PARAMS` 设 `render=True` 只出三机位静帧。出片需自行设置：`S.render.filepath` 指向序列目录、`image_settings.file_format='FFMPEG'`（或先出 PNG 序列再合成）。参考基线：Cycles CPU 单帧约 148 秒，240 帧全片需约 10 小时；可降采样（`resolution_percentage`）或降 `samples` 先试短样。

## 4. 验证清单（改完必跑）

`tools/verify_render.py` 内置断言即验收标准，全部通过才算改动成立：

1. 天气互斥：`Weather=0` 时雪粒/薄雪计数为 0，`Weather=1` 时雨丝/涟漪为 0。
2. 帧间动态：风动枝组、雨丝、雪粒、云团在帧 1 与帧 100 间位置/旋转有变化。
3. 驱动器全部有效（`invalid_object_drivers` 为空）。
4. 贴图资产 ≥7 且全部 packed 进 `.blend`。
5. 太湖石（瘦透漏皱）= 3 尊。
6. 云团、明月、花尖露珠法线朝外（体积符号为正）。
7. 场景唯一（`isolated_scene_count == 1`）。

## 5. 已知限制

- 远山是面向庭院机位的分层轮廓片，绕到背面无完整山体。
- 雨雪为艺术化循环驱动，无碰撞模拟；不模拟积水/积雪增长。
- 题字依赖 Windows 楷体（已 pack 进 `.blend`）；无该字体的系统重建时需改 `fontpath`。
- 渲染验证基于 Cycles CPU；GPU 可用时把 `S.cycles.device` 改为 `'GPU'` 提速。

## 6. 路线图建议

- [ ] 补齐三机位渲染并启用 gallery 雪月切换（见 3.1）
- [ ] GPU 渲染配置与短样片（240 帧）
- [ ] 月洞门内侧借景深化（当前为阶梯与竹影，可加第二进庭院）
- [ ] 雨雪转场中间态（`Weather` 目前仅 0/1 整型互斥，可扩展 0–1 连续混合）
- [ ] Eevee 实时预览分支（供快速构图，Cycles 保留正式出图）
