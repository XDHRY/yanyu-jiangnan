# 2026-10-12 · Round 16 · 第五桥与北河油纸伞住商巷

## 基线与范围

- 基线：`main@ab889f12aa1c7dc926c5b093de6626c51c2b2ba2`，包含 Round 15 西岸修桨作坊及此前全部村镇进度。
- 终版实现 head：`6ea224214754a7ef3854d1acd7efc5049051177e`；合并提交：`3f1eb49d15c922e76df954fa7439d5afa1918a55`；PR：[#22](https://github.com/XDHRY/yanyu-jiangnan/pull/22)。
- 本轮仅修改整体村镇仓库 `XDHRY/yanyu-jiangnan`；独立客栈仓库没有变更，也没有混用来源不明的客栈资产。

## 实际完成

1. 北端双岸、5 m 宽河道及两条纵向青石街向北延伸 11.30 m，并与上一轮端点重叠连接；东岸补一条通往第四桥的短横巷，形成连续步行回路。
2. 在 y=84.45 落地第五座木桥：11 块 linked bridge plank、12 根栏柱、4 道栏杆，两岸各 3 级踏步；构件在水岸和街道之间有真实承接关系。
3. 东岸落地 8.40 × 5.40 m 油纸伞住商铺：6 柱落 6 只柱础、连续额枋、实体厚度曲面屋面、4.70 m 临街开口，以及 1.18 m 可达后宅门洞。
4. 前店配置柜台、伞架、三把共用一个 12 分片 canopy Mesh 的油纸伞；三轮实图后将伞面缩至 0.46 m 半径并移向北侧，避免遮断后宅门洞。
5. 后宅配置明式榻、小案、方凳；为使门洞有明确去向，榻调整到门洞视轴，并用木框纸罩壁灯替代早期近景中读成现代裸灯的球形发光体。
6. 河岸补两根落地系船柱；本轮新增位图 0 B、付费资产 0，继续复用已有 7 张打包贴图。

## 实图闭环

- 第一轮：三把大伞与中央伞架遮住后宅门洞，近景只读成伞面陈列。
- 第二轮：伞面缩小并移到北侧后，近景前景柱落在画面中央，仍切断店内空间。
- 第三轮：机位回到街道中轴，门洞清楚，但后宅显得空且无明确目的地。
- 第四轮：明式榻进入门洞视轴并加低位暖灯，后宅去向成立；随后将椭圆高亮的裸灯轮廓改为木框纸罩壁灯。最终机位保持前 14 个基线机位不变，仅轮换 15/16。
- Function / Form / Runtime 三项人工门禁继续为 `pending`，没有由脚本或 CI 自动推断批准。

## 验证与性能

| 项目 | 结果 |
|---|---:|
| CI | 通过 · run 38160676936 |
| Blender Smoke | 通过 · run 38160676960 |
| Spatial Diagnostic | 通过 · run 38160676952 |
| Web Viewer | 通过 · run 38160676953 |
| 诊断机位 | 16 张，1024 × 640，Eevee Next |
| 诊断总耗时 | 151.59 s |
| 对象 / Mesh / Curve | 4006 / 2565 / 1361 |
| 顶点 / 多边形 | 169377 / 99435 |
| 实例展开三角面 | 167228 / 170000 本轮上限 |
| Mesh 实例复用率 | 48.81% |
| 材质 / 已打包图片 | 36 / 7 |
| 纹理 RGBA8 估算 | 41.99 MiB |
| 本轮新增位图 / 付费生成 | 0 bytes / 0 credits |

## 证据

- 可编辑 Blender 构建：[artifact 11710395643](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38160676960/artifacts/11710395643)
- 16 张原生诊断图、预算与断言：[artifact 11710505745](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38160676952/artifacts/11710505745)
- 浏览器 GLB、16 图与独立查看器：[artifact 11711070264](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38160676953/artifacts/11711070264)
- 持久 16 图拼图：`round16-contact-sheet-final.png`，Library `libfile_67d7848b24e08191b53bb752906e4a8d`。
- 持久首轮/终轮近景对比：`round16-before-after-final.png`，Library `libfile_4d1b33135a2081918c7b237bb2c021de`。
- 持久第五桥/伞铺重点图：`round16-focus-final.png`，Library `libfile_03fa3d2272048191aaf5a5085d9ea05b`。
- 结构、洞口、道具和三项人工门禁状态见 `assets/architecture/north-umbrella-lane/`；机器可读证据见 `docs/reviews/round16-north-umbrella-lane/manifest.json`。

## 已知债务与下一轮

- 碰撞、导航、LOD、UV/法线导出审计仍未完成。
- 雨伞目前强调结构与剪影，纸面色阶和半透明材质仍偏素；后续应优先用克制的粗糙度、透光和局部纹样提升，而不是堆高面数。
- 北端仍是阶段性边界；下一轮应继续向北接纸作/染坊小巷或转入河湾园林节点，并维持第五桥与两岸街道的回路净空。
- 最终纸罩壁灯已经在 16 号真实机位通过检查；下一轮不再回退到第四轮的裸灯版本。
