# Round 21｜北端公共转水埠

## 基线与提交

- 源基线：`main@612d2a84997dfeb557c58dcbfaccac9c4757fe35`，包含 Round 20 西岸染料行收货廊及此前全部村落资产。
- 实建分支：`codex/round21-north-turning-quay`
- 最终实建 head：`b3771c4c1c11b8aa1cce63e8977a815e05cbbb80`
- PR：[#27](https://github.com/XDHRY/yanyu-jiangnan/pull/27)
- 合并提交：[`771d6703eb7a123fa40d8ebb5e62ffadda0de775`](https://github.com/XDHRY/yanyu-jiangnan/commit/771d6703eb7a123fa40d8ebb5e62ffadda0de775)

## 本轮真实完成

- 将西岸、东岸、五米水面及两条 1.82 米青石街统一向北延伸 5.50 米；五类承载面均与上一轮保持 0.10 米实体重叠。
- 建成两处 4.72 × 2.05 米公共转身石坪，以低矮、无屋顶的公共节点收束纸业街区北端，继续保留水面与天空负空间。
- 建成 1.24 米净宽的九板青石踏桥；三座水下石墩从河床顶至桥板底，双岸各有高低桥槛，形成完整落地支撑与步行连续性。
- 东岸设置三级亲水踏步，顶标高依次为 0.16、0.11、0.06 米，并以重叠踏面接入终端水湾。
- 增加两张共享石凳、四条落地凳足、两根共享八边平顶系舟石、两盏共享纸灯与实体灯柱；所有家具均退出主通行轴。
- 将 480 粒雪的共享原型从 4×3 降至 4×2 分段/环数，保留粒子数量与四边轮廓，为公共节点回收重复几何预算。
- 未新增位图，未使用付费或外部生成资产；程序化 Blender 源仍为权威来源。

## 三轮真实渲染闭环

1. 首轮实渲确认整体空间连通，但两根系舟石使用球形原型，出现尖锥和悬浮误读；总览远山与前景屋顶占比过高。
2. 第二轮把系舟石改为封闭、平顶、八边收分网格并落在东岸石坪，同时收紧第 15 机位；桥、转身坪和亲水阶开始清晰。
3. 独立 Smoke 与 Spatial 构建暴露同源场景三角面漂移。追查到既有太湖石的程序噪声与 `EXACT` 布尔，最终显式设置噪声种子 36 并改用 `MANIFOLD`；终轮两个独立构建均得到 161,886 三角面。

终版重点机位为 `15_north_turning_quay_overview` 与 `16_north_turning_quay_eye`；原有 14 个庭院/村落基线机位未改动，未恢复 36 机位高成本渲染。

## 自动验证与性能

| 项目 | 终版结果 |
|---|---:|
| CI | [38444172280](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38444172280)，通过 |
| Blender 4.5 Smoke | [38444171678](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38444171678)，通过 |
| 16-view Spatial Diagnostic | [38444171694](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38444171694)，通过 |
| Web Viewer | [38444171749](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38444171749)，通过 |
| 对象 / Mesh / Curve | 4,330 / 2,839 / 1,404 |
| 展开实例三角面 | 161,886 / 170,000 |
| 剩余三角面预算 | 8,114 |
| 材质 / 打包图像 | 40 / 7 |
| 纹理显存估算 | 41.99 MiB |
| Mesh 复用对象 / 复用率 | 1,331 / 46.88% |
| 16 图分辨率 | 1024 × 640 |
| 16 图渲染总耗时 | 209.69 秒 |
| 新位图 / 付费资产 | 0 B / 0 |

可重复性复核：Smoke 的 `validation.json` 与 Spatial 的 `asset_budget.json` 均记录 `161886`；对象、Mesh、Curve、顶点和面数也完全一致。太湖石元数据为 `noise_seed=36`、`boolean_solver=MANIFOLD`。

## 构建与审阅产物

- [可编辑 Blender 构建](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38444171678/artifacts/11836339623)
- [16 张原图、断言与预算](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38444171694/artifacts/11837648325)
- [GLB、图集与 Web Viewer](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38444171749/artifacts/11838065553)

## 美术检查

- 通过：五类承载面连续；桥板覆盖两岸；三座桥墩真实接触桥底；东岸亲水阶按 5 厘米节奏下降。
- 通过：平顶系舟石已落地，不再出现首轮尖锥/漂浮误读；石凳四足与座面接合，灯柱与公共动线分离。
- 通过：低平青石桥与两侧转身坪形成“公共收口”，未用新屋顶继续抬高北端体量，水面负空间仍占主导。
- 后续债务：桥面仍偏整洁，需要克制补充湿痕、缝隙与使用磨损；终端水湾缺少小型停泊船具和人与货的尺度参照。

## 人工门禁与下一轮

Function、Form、Runtime 三项人工门禁继续保持 `pending`，自动工作流成功不等同于人工批准。碰撞、导航、正式 LOD、导出后 UV/法线专项审计仍未完成。

下一轮优先沿转水埠两侧形成小规模公共生活层：补充低成本停泊船具、桥面湿痕与夜间尺度参照，并在不破坏北端留白的前提下选择一侧接入小型茶棚或船具摊；继续把 16 机位和 170k 三角面作为硬门槛。
