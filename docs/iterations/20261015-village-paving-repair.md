# 2026-10-15｜Round 24 原村巷铺地连续性修复

## 基线、范围与源码

- 整体库 `XDHRY/yanyu-jiangnan`，基线 `main@e5ae0b75f3b78c4b3ec9941f2deb03caa1169ece`，完整包含 Round 23 及全部既有村落。
- 独立客栈库 `XDHRY/yanyu-jiangnan-ming-inn` 本轮未改动。
- PR [#30](https://github.com/XDHRY/yanyu-jiangnan/pull/30)。首轮源码头 `4a70aff075ccd7f32ff9d4ac3e902ab599b298c8`；第二轮源码头 `f79f31bf2a72c65d66787f1716bdfdcf1ede2ee1`。
- 四项机器门禁及终版实渲审阅后合并，合并提交 `b7112269d0123f324471f93442fdf4738837376d`。
- 修改以完整父树为基础，只有两个生成/验证脚本、诊断机位以及本批契约和 manifest；保留全部非目标资产和工作流。

## 实际修复

上一轮 Run `38584012917` 的 12 号村巷实图暴露条状高差与深缝。源码核对确认：24块旧窄汀步顶高0.18m，后来完整街面顶高0.12m，两套不同节距的铺地叠在一起，产生60mm高差；街板12mm宽接缝直接露出0m地基。

- 24块旧汀步保持可编辑、数量不变，降为顶高0.105m的埋入式基层。
- 西水街、东水街、月门北巷各增加一块闭合连续砂浆床，从0m地基接到0.112m；街面保留8mm凹缝。
- 三条砂浆床与一条连接铺地总计新增48个源码三角面；沿用既有stone/darkstone，无新位图、材质或付费生成。
- 不扩张城镇边界、不填河、不改变房屋、桥、院落与北端茶担。
- 新增断言检查旧石顶高、三条床底/顶、全宽与长度，以及每道板缝均有床承托。
- 前14机位逐项AST比较完全一致，仅15/16轮换为低位铺地及首桥/村巷衔接。

## 验证与真实渲染

第一轮 Run `38707262944` 四项构建全部通过，16图308.79秒。但图像审阅发现月门北巷与西水街之间0.43m裸露地基带仍读成断槽。这是独立于旧窄汀步高差的第二个问题，不能由第一轮断言通过掩盖。

第二轮补建x=2.16..2.59、y=6.5..36.9、顶高0.112m的连接铺地。与既有入户横径保持8mm顶面差，避免共面重叠。断言新增连接带完整边界和标高检查。终版实图确认条槽消失，铺地连续且保留接缝与桥头踏步。

最终源码头 `f79f31bf2a72c65d66787f1716bdfdcf1ede2ee1`；Actions测试合并树 `50f622f4a74e60add9226f4aceb3ac69c5f1b607`（manifest中的source_commit）。

| 实测项 | 终版 |
|---|---:|
| CI | [38708410140](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38708410140) 通过 |
| Blender Smoke | [38708410133](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38708410133) 通过 |
| 16机位空间诊断 | [38708410153](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38708410153) 通过 |
| Web Viewer | [38708410144](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38708410144) 通过 |
| 对象 / Mesh / Curve | 4382 / 2883 / 1411 |
| 实例展开网格三角面 | 162642 / 170000 |
| 预算余量 | 7358 |
| 材质 / 打包图像 | 44 / 7 |
| 纹理RGBA8估算 | 41.99 MiB |
| 共享Mesh复用率 | 47.21% |
| 16图耗时 | 210.80秒 |
| 预算警告 | 0 |

Smoke和Spatial两个独立构建的对象、顶点、面、材质及驱动等场景统计完全一致。三角面口径沿用现有工具的实例展开网格统计，不声称已完成所有修改器求值后的运行时性能审计。

- [持久审阅包](https://github.com/XDHRY/yanyu-jiangnan/blob/review/round-38708410153/docs/reviews/round-38708410153/README.md)
- [可编辑Blender产物](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38708410133/artifacts/11958973148)
- [16张原图、断言及预算](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38708410153/artifacts/11959427857)
- [GLB与独立Web Viewer](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38708410144/artifacts/11959657392)

## 人工门禁与未完成项

Function / Form / Runtime 均为 `pending`。本轮几何测量不等于运行时碰撞/导航验收；正式LOD和导出后UV/法线专项审计仍待完成。

## 美术复盘与下一轮

本轮沿用结构/接触检查指导，把连续通行面优先于新增道具。条缝应读作石材接缝而不是沟槽，旧原型不能在后续铺地建成后继续制造无意高差。此观察仍是项目复盘，不自动提升为已批准技能教义。

下一轮从修复后的原村巷继续审阅入户门洞、门扇和室内去向，选择一栋民居做克制木作/室内目的地精修；保持14个基线机位，并继续追踪碰撞/导航债务。不再增加北端道具簇。
