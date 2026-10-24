# Round 64 · 北河转水埠系泊舢板原生轻摇

日期：2026-10-24  
仓库：`XDHRY/yanyu-jiangnan`（整体庭院、园林与村镇；未修改独立客栈仓库）  
基线：main `0545674995be847210e13ac1cb2a32abceabe8ea`（Round 63，含完整村镇）  
实现 head：`e757bff5374377741effcc77031e7e215bfcebef`  
PR：[#71](https://github.com/XDHRY/yanyu-jiangnan/pull/71)

## 实际交付

- 复用北河转水埠既有舢板，不增加船体几何、材质或贴图。
- 新增零几何 EMPTY：`JN_北河转水埠_停泊舢板系泊锚64`，位置与系缆第一控制点同为 `(7.30, 103.78, 0.45)m`。
- 将船壳、2 舷条、2 坐板、3 横肋和船上桨共 9 个既有部件挂到同一锚点。
- Blender 原生 Action：`JN_Action_北河转水埠_系泊舢板轻摇64`；240 帧 / 24 fps。
- X 轴俯仰峰值 ±0.006 rad，Z 轴偏航峰值 ±0.010 rad；1/40/80/120/160/200/240 帧采样，80 帧为静态诊断中性帧。
- GLB 现在保留两条独立原生 clip：Round 63 工作纱灯 + Round 64 系泊舢板。导出前将两个 Action 分别放入具名 NLA 轨道，避免 ACTIVE_ACTIONS 合并为一个匿名 clip。
- 第 16 聚焦机位由庭院湿岸轮换为 `16_moored_sampan`；核心 14 机位及总览 15 保留。

## 闭环与失败记录

1. 第一版父级设置在重载后把船体镜像到锚点另一侧，桥下净空实测 `-0.865 m`，Smoke 拒绝。
2. 仅增加 parent inverse 未解决；改为显式计算 `anchor.matrix_world.inverted() @ world_matrix`，写入 `matrix_basis`，并在生成时要求所有部件世界位置误差 < `1e-5 m`。
3. 净空修复后，横肋静态接触断言因验证脚本停在动态采样帧而失败；将静态构造检查固定在中性帧 80，动态段仍独立检查 40/80/120/200 帧。
4. 场景、Smoke 与 16 图通过后，GLB 初次仍把两个对象 Action 合成一条 `Animation`；改为独立 NLA 轨道导出，最终得到两条具名 clip。没有降低几何、支撑、净空或运行时断言。

## 几何 / 支撑 / 运动验证

- 船体各采样帧均保持在终端水湾包络内。
- 桥下最小纵向净空（帧 40/80/120/200）：`0.2640 / 0.2700 / 0.2652 / 0.2640 m`，均高于 `0.24 m` 门槛。
- 系缆端点与动画锚点严格重合；绳索不参与变形，当前仅验证端点固定和小幅摇摆。
- 9 个船上部件共享同一父级；横肋—船底、坐板—横肋、船桨—坐板的原有接触门禁在帧 80 通过。
- 不是浮力、流体或缆绳动力学模拟；不声称适航或物理精确。

## 性能与资产账

- 4,667 对象；3,145 Mesh 对象；1,427 Curve 对象。
- 99,554 面；167,686 含实例三角面，较 Round 63 三角数不变；170k 预算余量 2,314。
- 58 材质、15 图像、48 灯；RGBA8 趋势估算 44.49 MiB。
- 新增：1 个 EMPTY、1 条 Action；0 Mesh、0 源三角面、0 材质、0 贴图、0 灯、0 建筑。
- 16 张 1024×640 诊断图总耗时 316.59 秒。
- Web：625,355 实例三角；GLB 51,802,336 bytes；2 条原生 rotation clips。
- 离线 HTML 70,605,778 bytes；外部请求 0，页面错误 0。
- 同机位屏幕运动变化 2,045 像素；暂停后时间、灯笼角度、舢板俯仰和偏航均冻结。
- Chromium WebGL SwiftShader 已验收；这不是实体手机 FPS 基准。

## 门禁与证据

- [CI run 40102929506](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/40102929506)
- [Blender Smoke run 40102929577](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/40102929577)
- [Spatial 16 图 run 40102929550](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/40102929550)
- [Web Viewer run 40102929543](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/40102929543)
- [Offline Runtime run 40102929499](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/40102929499)

持久审阅文件：

- [离线动画 HTML](https://chatgpt.com/library?file_id=libfile_8fee8a6f286c8191bb1089ea63dabe93&account_id=personal)
- [完整 Round 64 审阅包](https://chatgpt.com/library?file_id=libfile_62d3b3788d6c8191961f0e68a0d6ac14&account_id=personal)
- [16 图诊断原包](https://chatgpt.com/library?file_id=libfile_a98254aeffc08191912a9c507c8014de&account_id=personal)
- [16 图拼图](https://chatgpt.com/library?file_id=libfile_e7edd1b2d6088191bdb60b8ec118ffa3&account_id=personal)
- [舢板 Blender / Web 双通道图](https://chatgpt.com/library?file_id=libfile_9c9c60538e74819188326cefbc1d9406&account_id=personal)

## 美术检查与限制

- 专用机位确认船壳、坐板、横肋、船桨、系缆、踏桥和码头灯光关系可读；夜景里前景石坪占比偏大，下一次若继续该区域应微调机位而不是增大船体。
- 本轮是动画与结构可信度交付，静态中性帧的几何和材质没有改变；不存在可诚实标注为同机位“Round 63 前图”的旧第 16 机位。不得复制本轮图冒充旧图。
- 网页运行时以导出节点同步复现相同俯仰/偏航；水波、雨雪、昼夜仍为查看器效果。
- 人工 Function / Form / Runtime 审批继续为 pending；实体手机、生产 LOD、碰撞、导航、浮力和缆绳动力学未验收。

## 下一轮

优先推进一个不增加三角面的既有店幌或竹帘原生轻摆，并把第 16 轮换机位用于结构与遮挡检查；若转回静态精修，则优先调整舢板近景前景石坪遮挡和木作材质层次。任何新动画继续要求具名 GLB clip、暂停冻结、独立目标节点和全摆幅空间门禁。
