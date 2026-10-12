# 2026-10-12 · Round 18 东岸装订纸铺与预算回收

## 基线与结果

- 源基线：`main@f4240c1300dab3102d7c4b5729d759fac6d59232`（Round 17 北河楮皮纸坊与晒纸院）
- 最终实现 head：`c52cda29a20565c4706cd8acb537000a736d3f49`
- PR：[Round 18 #24](https://github.com/XDHRY/yanyu-jiangnan/pull/24)
- 实建合并提交：`3cf9eb9e3a40cced68b31e8f5c273e0bb285aa5c`

本轮没有继续向北拉长边界，而是复用 Round 17 已建的东岸纸业地块，补成与西岸楮皮纸坊隔河相望的装订纸铺。先回收共享微小构件预算，再用实体结构完成纸业“生产—交易—装订”链条。

## 实际建成

- 5.80 × 6.50 m 东岸纸铺，六柱六础，柱—梁—台基接触完整。
- 连续纵梁、三道横梁、实体厚度低模双坡屋面、正脊和檐口。
- 两级青石临街门槛；南、北两段开敞店面净宽均为 2.40 m。
- 临街柜台、东墙三层纸架。
- 四足装订压书台、双立柱、横梁、铜螺杆与压板。
- 6 份共享 Mesh 纸令、5 册共享 Mesh 线装书及可见书脊线。
- 一盏有实体吊线的柜台任务灯。
- 新位图 0 B，付费生成资产 0。

## 预算回收

共享露珠原型由 6×4 UV 分段降为 6×3；257 颗 2–4 cm 露珠保持数量与材质不变，理论回收 3,084 个展开三角面。与 Round 17 相比，纸铺新增 70 个对象后，场景展开三角面仍由 167,964 降至 165,562，净减少 2,402，恢复 4,438 个三角面的余量。

## 三轮真实渲染闭环

1. 首轮：纸铺本身可读，但 15 号近檐吞掉西岸纸坊，16 号中柱压在画面中央。
2. 第二轮：河轴俯拍把两岸建筑裁到画面边缘，近景仍穿柱，判定失败。
3. 终轮：15 号改为西南远距斜看，双岸纸业、第五桥与水巷同框；16 号正对南侧 2.40 m 净开间，纸架、纸令、线装书和压书台可读。

前 14 个庭院与村落基线机位保持不变，只轮换 15/16；仍为 16 张 1024×640 Eevee Next 诊断图，没有恢复 36 机位高成本渲染。

## 验证与性能

- CI：[run 38244428573](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38244428573) — success
- Blender 4.5 Smoke：[run 38244428521](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38244428521) — success
- Spatial Diagnostic：[run 38244428591](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38244428591) — success
- Web Viewer：[run 38244428627](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38244428627) — success
- 对象 / Mesh / Curve：4,139 / 2,670 / 1,386
- 展开三角面：165,562 / 170,000
- 材质 / 打包图像：36 / 7
- 纹理显存估算：41.99 MiB
- Mesh 实例复用率：47.68%
- 16 图总渲染耗时：159.56 s

## 产物与审阅证据

- [16 张原图、断言与预算](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38244428591/artifacts/11744890335)
- [可编辑 Blender 构建](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38244428521/artifacts/11744750026)
- [GLB 与 Web Viewer](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38244428627/artifacts/11744354857)
- 16 机位拼图：Library `libfile_bb41b31cd2ec8191a94b8ab659951fb7`
- 纸业双岸重点图：Library `libfile_03191feca5ec8191aac78ee2d8283b0f`
- 首轮失败—终轮修正对比：Library `libfile_06a127df42d48191a55d03b59831da83`

## 未完成与下一轮

Function、Form、Runtime 三项人工门禁继续保持 `pending_human_review`。碰撞、导航、LOD、专项 UV/法线导出审计仍未完成。装订铺目前结构可信、工艺链可读，但纸张/书册仍偏素，压书台细部与商号识别可以继续提升。

下一轮优先：
1. 在不突破 170k 的前提下加强纸页层次、书脊线与压书台构造可读性；
2. 评估进一步批处理庭院高频小件，为后续染纸门面或纸商小院回收 3–5k 三角面；
3. 保持北河双岸路线连续，新增区域必须从现有东岸石街或第五桥产生清楚动线。
