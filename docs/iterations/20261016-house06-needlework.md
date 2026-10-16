# 2026-10-16｜Round28 东岸第6户针线节点

## 基线、范围与提交

整体库 XDHRY/yanyu-jiangnan，基线 main@1f8ebb9e0ce88a0052a696d4b4f000da81fdbd4b，包含全部既有村镇与Round27。读取main、开放PR、Actions、美术契约、资产清单、上轮交接及Round27实际产物后开始；无其他开放PR或进行中同头构建。独立客栈库未改动。

[PR34](https://github.com/XDHRY/yanyu-jiangnan/pull/34)已通过机器验证并合并，合并提交 05b0bc4ac38c63997131567064a770e7ee557f79。最终源码8945f7defdabc9b86d6a6bec80562162e5bbfdda；Actions测试合并树086da629762e7e5826c74288160693cf7481f9fb。每次提交均以完整父树为base，只改5条目标路径并检查expected head，保留全部其他纹理、资产和工作流；等前批构建结束后才更新同一分支，未重复触发同头。

## 实建与预算

现有第6户、案几与长凳不移动。新增0.68米矩形绣框、四撑足、绷布与六瓣针脚，三只闭合低面线轴及绕线，开口针盒/独立盒盖/绣针，落地布架与12顶点搭布，以及木框纸罩案灯和同位光源。10类重复件共享Mesh；新增47对象（44 Mesh、2 Curve、1光），无新屋面、街区边界、材质、位图或付费资产。织物复用Round26程序材质，来源、米制映射及许可见assets/architecture/house06-needlework/asset_manifest.json。

| 实测项 | 终版 |
|---|---:|
| 对象 / Mesh / Curve | 4521 / 3005 / 1426 |
| 实例展开网格三角面 / 面 / 顶点 | 164746 / 98014 / 169144 |
| 新增三角面 / 总预算余量 | 912 / 5254 |
| 唯一网格三角面 | 125204 |
| 材质 / 打包图片 | 46 / 7 |
| 纹理RGBA8估算 | 41.99 MiB |
| Mesh复用率 | 48.52% |
| 16图渲染耗时 | 299.05秒 |
| 预算 / 空间警告 / 无效驱动 | 0 / 0 / 0 |

Smoke和Spatial独立构建场景统计一致。面数口径不含全部修改器求值和Curve转网格；纹理估算不是实际GPU驻留显存。

## 真渲与失败记录

1. bceab72e085b658a9a04b16b1ef4cb682c542e19：四项通过，首批实图Spatial38856438792，296.99秒；16号被门扇占画，物件偏小。
2. 7c8914cd49e076e52818eda489a3062d61dbba34：CI38857383077通过；Smoke38857382999、Spatial38857383101、Web38857383002在新增接触断言处失败，搭布顶面1.615米、横枋顶面1.610米，不计为有效出图。修正几何为1.610米，不放宽断言。
3. bfcb73993fd4e9d8aeeaf29a4b3f02296ac997a4：四项通过，Spatial38857669582实图311.96秒；门扇遮挡消除，但16号仍裁布架左侧及案几下沿，未将机器成功当成完整取景。
4. 4d153ec0dfa797a2db341bcf3a87ecdc463f2099：CI/Smoke通过，Spatial38858550238与Web38858550164在取景预检拒绝9.61mm超广结果；无有效新图。
5. 8945f7defdabc9b86d6a6bec80562162e5bbfdda：近景按实际求值顶点（含Curve、薄布Solidify）拟合而非保守包围盒，四项通过，终版16张实际图已审阅。只轮换15/16，前14机位AST保持不变，未隐藏门扇、墙体、植物；未恢复36机位高成本渲染。

15号完整检查本户26个对象的屋面、门窗、台基及沿河联系，三条门口观察射线无遮挡；邻居/桥是边缘延续，不宣称它们在该图完整入画。16号在真实室内通道内，38个家具/针线对象求值顶点投影边界[0.142469,0.829739,0.059406,0.758047]，四边均超过4.5%边距，实际焦距25.271896mm。案几、长凳、布架和落地足完整可见；绣框、三线轴、开口针盒分离可辨。该投影检查不替代BVH遮挡、导航或人工造型批准。

清单分列requested_target/fitted_target及requested_lens/实际lens，避免上一轮元数据歧义。Round27的起居户机位与图包仍保留于其交接和review分支，不以新图覆盖旧证据。对比图左为本轮首批Run38856438792，右为终版Run38859048568：机位和搭布折面均改变，不宣称是同角度材质对比。

## 验证与产物

- [CI38859048580](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38859048580)
- [Smoke38859048519](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38859048519)；[可编辑Blender12028391579](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38859048519/artifacts/12028391579)
- [Spatial38859048568](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38859048568)；[16张PNG、断言与预算12028038190](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38859048568/artifacts/12028038190)
- [Web38859048607](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38859048607)；[GLB与Viewer12028956267](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38859048607/artifacts/12028956267)
- [持久审阅图集](https://github.com/XDHRY/yanyu-jiangnan/blob/review/round-38859048568/docs/reviews/round-38859048568/README.md)

## 尚未完成与下一轮

Function/Form/Runtime人工门禁保持pending。住宅入口沿用约1.122米，不按公共大厅2.4米默认值；2.2×1.0米室内避让条带不等于导航验收。完整BVH碰撞、运行时体验、正式LOD、导出UV/法线与全部求值几何预算仍待专项验证。布料仍硬，针脚和木作细部仍简，不宣称达到最终精美度。

新发现P2管线债务：tools/export_web.py仍独立硬编码旧织造后园15/16巡游机位，本轮Web成功只证明既有导出/展示构建，不能冒充本轮聚焦机位运行时验收。下一轮优先让Web预设消费同一份实际诊断相机参数（保留14核心与历史轮换记录），再补一处低成本家具木作/织物转折；不先扩建大屋面。未来轮换机位时须同步调整house06专用预检，不强行适配回旧区域。
