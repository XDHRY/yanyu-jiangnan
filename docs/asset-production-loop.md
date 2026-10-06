# 烟雨江南：资产生产、贴图与性能预算协议

> 本协议与 `docs/iteration-loop.md` 并行：前者回答“资产怎样做精而不做重”，后者回答“场景怎样低成本观察—修改—再观察”。

## 1. 每轮只做一个主资产/主问题

每一轮必须先从最新诊断图中选出一个 P0/P1：建筑构造、屋面、门窗、石材、木作、家具、植被、水体、灯光、雨雪之一。
禁止一轮同时铺开大量粗资产。优先把一个镜头里真正可见、能改变轮廓或材质层次的对象做到可复用、可验证。

## 2. 几何预算原则

统一以 Blender 三角化后的 triangle count 为主要几何指标，同时记录 faces / verts / objects / material slots。

- **轮廓、承重/连接关系、近景转折**：用真实几何。
- **木纹、石孔、细裂、瓦面磨损、细小雕纹**：优先 Normal / Roughness / AO，不用大量微几何。
- **重复构件**：优先 linked duplicate / Collection Instance / Geometry Nodes instance；不得复制出大量独立网格。
- **不可见几何**：清理内部面、长期遮挡面、重合面；不为看不到的背面细节付渲染成本。
- **Bevel**：只保留能在目标机位形成高光边的必要段数。
- **高模仅作为烘焙源**：若为了法线/细节做高模，高模不得直接成为大量重复场景实例。

建议初始预算（不是永久硬编码；以诊断机位和实际 silhouette loss 为准）：

| 资产级别 | LOD0 目标 | LOD1 | LOD2 |
|---|---:|---:|---:|
| 小型重复件（瓦端、石灯小部件、窗格单元） | 0.2k–2k tris | 40–60% | 10–25% |
| 家具/中型摆件 | 2k–10k tris | 40–60% | 10–25% |
| Hero 石/树干/复杂门窗 | 5k–20k tris | 35–55% | 8–20% |
| 模块化建筑单件 | 2k–15k tris | 35–55% | 8–20% |

任何资产超过建议范围时，必须在 manifest 中写明“为什么镜头需要这些三角面”。远景和大量重复资产默认必须有显著低模版本。

## 3. 贴图必须成为资产的一部分

每个重要资产至少定义：

- BaseColor：不烘入强方向光/投影；可复用、尺度正确。
- Normal：承载小凹凸、木纤维、石孔、磨损等高频细节。
- Roughness：控制湿石、旧木、粉墙、黛瓦之间的反射差异。
- AO：只表达局部遮蔽；可与 Roughness/Metallic 做 ORM 通道打包。
- Alpha：只在叶片、花瓣、细枝卡片等确有收益时使用。

屏幕占比决定分辨率：

- 极远/小重复件：512
- 中景常见资产：1K
- 近景重要资产：2K
- 只有确实占据大画面、能在正式成片中读出差异的 Hero 资产才考虑 4K

能共享时使用 atlas；同类瓦、窗、家具小部件不要无意义地各占一张大图。
所有生成/外部贴图必须进入仓库资产目录，并记录：来源或提示词、用途、分辨率、色彩空间、映射方式、可否平铺、目标资产、许可证/来源说明（如适用）。

## 4. 资产目录与 manifest

逐步把当前单层 `textures/` 扩展为可审查资产库，目标结构：

```
assets/
  architecture/
  furniture/
  rocks/
  vegetation/
  props/
  materials/
textures/
  source/
  baked/
  atlases/
  generation_prompts.json
```

每个可复用主资产应有 manifest，至少记录：

```json
{
  "name": "asset_name",
  "role": "hero|mid|background|repeat",
  "lod0_tris_budget": 0,
  "lod0_tris_actual": 0,
  "lod1_ratio": 0.5,
  "lod2_ratio": 0.2,
  "materials": [],
  "textures": [],
  "texture_resolution": [],
  "instances_in_scene": 0,
  "source": "procedural|modeled|generated|external",
  "validation_views": []
}
```

## 5. 每轮性能账本

每轮提交前后都记录：

- total triangles / faces / verts
- mesh objects / total objects
- materials
- image textures 与估算纹理内存
- repeated asset instances
- driver count
- 诊断渲染总耗时与最慢机位
- .blend / artifact 大小

注意：当前场景的成本不能只看“面数”。对象数量、驱动器数量、材质与透明片 overdraw、贴图大小同样可能成为瓶颈。

## 6. 资产验收

一个资产只有同时满足以下条件才算“进库”：

1. 在指定诊断机位中确实改善画面。
2. silhouette 与关键结构在 LOD0 正确。
3. LOD1/LOD2 不出现明显穿帮。
4. UV、法线、比例、原点和变换正确。
5. PBR 贴图与真实尺度匹配。
6. 无无意义的内部/重叠几何。
7. 重复使用时走实例化。
8. Blender 4.5 headless 可重建。
9. 贴图能自动定位并 pack。
10. manifest、preview/contact sheet 与性能指标齐全。

## 7. 固定闭环

`观察 → 选一个重点 → 设预算 → 精修建模 → 生成/烘焙贴图 → LOD/实例化优化 → 入资产库 → 无头重建 → 10 机位诊断 → 对比质量/成本 → 提交`

如果质量提升不明显而 triangles、对象数、显存或渲染时间明显上升，视为失败迭代；回退或重新设计，不允许靠“继续加细节”掩盖问题。

## 8. GitHub 经验吸收原则

公开项目中值得持续借鉴的机制包括：

- 生成脚本/参数化源文件作为可审查 source of truth，而不是把 .blend 当唯一真相。
- 每资产固定 triangle budget，自动生成 LOD0/1/2。
- 高模细节烘焙到 BaseColor/Normal/ORM，低模用于真实场景。
- atlas / channel packing / screen-coverage texture sizing。
- headless Blender + CI 自动重建、预览、manifest 与验证。
- 高模原件与最终发布资产分离，保留以后重新优化的能力。

引入任何外部脚本/插件前先检查许可证、Blender 4.5 兼容性与最小依赖；优先移植原理和小工具，不直接把未知大型依赖塞进主场景。
