# 2026-10-24 · Round 63：北河修桨作坊工作纱灯原生轻摆

## 基线与仓库边界

- 整体仓库：`XDHRY/yanyu-jiangnan`
- 源基线：`main@c56dd8446593e880f29472cc47ea0d4a2bc6f62c`（已含 Round 62 及全部村镇进度）
- 本轮已验证模型源：`c3db4aa8745fe99040d0b63fc29a7dc52de52a06`
- PR：[ #70 ](https://github.com/XDHRY/yanyu-jiangnan/pull/70)
- 客栈精修仓库 `XDHRY/yanyu-jiangnan-ming-inn` 本轮未改动；两库仍是独立来源。

## 实际完成

- 复用既有 `JN_北河修桨作坊_工作纱灯`，新增一个零几何 EMPTY 摆动锚。
- 新增 Blender 原生 Action `JN_Action_北河修桨作坊_工作纱灯轻摆63`。
- X 轴摆幅 ±0.045 rad；1–240 帧、24 fps；帧 80 为中性姿态，锁定诊断图可与 Round 62 静态基线直接对比。
- GLB 导出改为携带 ACTIVE_ACTIONS；最终成品必须恰好包含 1 个 rotation clip，目标名称必须含 `工作纱灯摆动锚63`。
- 两级 GLB 无损共享流优化器现保留 animation sampler/channel/accessor，并用动画 payload 指纹检查无损性。
- 离线 HTML 在已导出的目标节点上同步播放同一周期/幅度，暂停按钮同时冻结水面时钟与灯笼角度。
- 资产合同：`assets/architecture/west-oar-workshop/animation63.json`。

## 自动验证（全部通过）

| 门禁 | Run | 结果 |
|---|---:|---|
| CI | [40075040885](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/40075040885) | success |
| Blender 4.5 Smoke | [40075040850](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/40075040850) | success |
| Spatial Diagnostic（16 图） | [40075040846](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/40075040846) | success |
| Web 3D Viewer | [40075040862](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/40075040862) | success |
| Offline Animated Preview | [40075040828](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/40075040828) | success |

### 产物

- [16 图空间诊断 artifact 12553480126](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/40075040846/artifacts/12553480126)
- [Web Viewer / GLB artifact 12553226697](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/40075040862/artifacts/12553226697)
- [离线动效 HTML artifact 12553396435](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/40075040828/artifacts/12553396435)
- [可编辑 .blend artifact 12552564067](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/40075040850/artifacts/12552564067)

## 实测账本

- 场景对象 4,666；Mesh 3,145；Curve 1,427；材质 58；图片 15。
- 源场景实例展开三角面 167,686；本轮增量 0；相对 170,000 预算余量 2,314。
- 纹理 RGBA8 趋势估算 44.49 MiB；本轮图片/纹理显存增量 0。
- 复用 Mesh 对象 1,571；实例复用比 0.4995。
- 16 张诊断图均为 1024×640；总渲染 177.29 s，最慢单图 36.03 s。
- GLB 原生动画 clip：1；rotation target：`JN_北河修桨作坊_工作纱灯摆动锚63`。
- 离线浏览器初始灯笼角度 0.011873 rad；暂停证据角度 0.044728 rad；暂停后 600 ms 保持完全不变；恢复后最终角度 -0.031821 rad。
- 同机位实际屏幕变化：2,040 / 655,360 像素（阈值 >2）；仅作“动起来”证据，不是 FPS 基准。
- 离线 HTML 70,575,725 bytes，SHA-256 `091ddfc5e4f774ff327fbd2833fefc594b484e6c51e5a3d664d1a0ec63aa16b1`。
- GLB SHA-256 `b763f74cc52ffd71e44b165d82b858e542a54e9b34076b9258a80d815e2f1ce1`。

## 美术检查

- 帧 80 为中性，16 个既有低成本机位未见新增穿插、悬空、遮挡或材质回归。
- 本轮只改善修桨作坊的生活气息，不改变建筑轮廓、柱梁—台基、桥岸或街巷动线。
- 静态图与 Round 62 近似是设计结果，不是漏做：差异应在时间轴/离线播放器中审阅。
- 自动门禁不替代人工 Function / Form / Runtime 审批；三项仍为 **pending**。
- 离线水波、雨雪、昼夜仍是 viewer-side 审阅效果；GLB 原生 clip 仅为灯笼轻摆，没有人物或船只动画。实体手机尚未测试。

## 下一轮优先级

1. 在不破坏系泊/桥下净空的前提下，为既有小船设计原生缓慢升沉/偏航动作，并先补专用近景机位。
2. 继续守住 170k 源三角面和 16 个 1024×640 低成本机位，不恢复 36 机位正式渲染。
3. 若船体动画的空间或支撑门禁不过，退回零几何的店幌/竹帘轻摆批次，不绕过失败门禁。
