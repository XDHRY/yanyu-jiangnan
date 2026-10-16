# 2026-10-16｜Round30 网页材质错误法线与UV修复

## 基线与范围

整体库 XDHRY/yanyu-jiangnan，main@31f9c4d96e78fee3e02bb9039a2e657cedc20d21；包含全部村镇与Round29相机修复。开始前读取main、开放PR、Actions、美术方向、美术契约、针线户清单与Round29交接；无开放PR、无进行中构建。独立客栈库未改动。按build-3d-game-rooms技能分开记录源码、真实运行证据与人工批准，不运行付费资产生成。

首批源码27a014ed1967742e7d261804bce815a00e328a55，[PR36](https://github.com/XDHRY/yanyu-jiangnan/pull/36)。基于完整父树创建6路径增量，不覆盖非目标资产、纹理和工作流，不重复触发同头。

## 已确认的问题

恢复Round29持久审阅包并解析实际GLB：JN_plaster、JN_tile、JN_edge、JN_wood、JN_stone、JN_ivory、JN_bark、JN_pink共8材质的normalTexture与baseColorTexture引用同一张彩色图片，错误地将底图当作切线空间法线。共有1568个primitive缺少TEXCOORD_0、655个具有该属性（不等于全部1568个都需要纹理）。基线GLB按节点实例及索引计算有626279个导出三角面，包含Curve及修改器，与164746原始网格三角面不是同一口径。

官方导出材质参考：https://github.com/KhronosGroup/glTF-Blender-IO/blob/main/docs/blender_docs/scene_gltf2.rst 。本轮判断主要来自实际GLB，不把“所有复杂节点都丢失”当作已验证结论；基线事实上包含7张底图。

## 修复与边界

- 仅在导出会话复制材质/共享网格，不回存作者场景；移除不受glTF原生表达的Bump输出，改为几何法线，不把它命名为已完成的Normal贴图。
- BOX图像使用JN_WEB_MetreUV：按本地面法线的主轴投影，沿用原Object坐标乘数。共享Mesh仍按源数据块复用；Curve先按现有求值结果转网格后补UV。保留原UV供花瓣/背景使用。
- 这是主面投影近似，不是完整BOX三向混合烘焙，边缘接缝、程序粗糙度与真实切线Normal/AO仍待专项。未增加灯光曝光、未加入方向光底图、未创造新位图/屋面/资产。
- 位图来源、原始提示词和用途沿用textures/generation_prompts.json与docs/art-direction.md；7张既有项目生成图继续嵌入GLB，无外部新增许可、付费资产或新增文件。Object乘数记录在每材质导出报告，非BOX缺UV回退单列，不假称所有UV都满足正式打包与尺度验收。
- 导出后强制检查：彩色底图不能与法线图共用同一image；每个有底图的primitive必须有其指定UV属性；材质报告来源必须和本次viewer提交一致。
- 本地5项Python测试通过（含新增3项：有效UV/独立法线、拒绝底图法线复用、拒绝缺UV）；既有3项Node相机投影测试保留。

## 运行状态

首批CI38916685914与Smoke38916684955通过，Web38916685308在完成16图、导出与相机核对后，被新增材质门禁拒绝：JN_ivory__WEB仍缺底图UV。未合并，未放宽检查。修复缺UV的非BOX图像材质：已有UV保留，无UV时按主面包围范围生成0–1保守UV，并单独计入normalized_fallback_faces；该回退不是已审定的花瓣UV展开。

二次源b561b2867c0524e83873b94776ebf4a6fd605516，CI38917720426、Smoke38917720461及Web38917720422全部机器通过；16图319.67秒，Web artifact12052869098，测试合并树cce333bc1463dd6f8183143149cff627aabab7a6。1518个带底图primitive检查无缺UV，0个错误法线复用，92个面使用归一化回退UV；4张网页实截均位置误差0，最大角误差2.98e-8。实际纹理已可读，但下载后独立几何预算断言拒绝626567三角面（基线626279）：新增288来自三个原本hide_render的屋面原型，它们的Curve临时替代物丢失隐藏属性。未合并，未把机器全部通过当作人工美术通过。

二次还测得UV开销：GLB52897492字节（基线44489352），POSITION去重accessor顶点818438（基线748060），属性/索引缓冲估算29777038字节（基线21649614）。UV接缝拆点与新UV属性确有代价，不宣称零几何内存增长。glTF材质条目45对比基线41，源材质名集合相同，4项增量是同材质不同UV集合索引的导出变体；作者场景仍46材质。这些均非实际GPU驻留显存或手机帧率。

三次源1087d4047a488204752456dae3b6b3301f5ae655，转换前跳过原hide_render对象，报告隐藏名并在GLB验证拒绝这些原型；CI38919284003、Smoke38919284045、Web38919283802全部通过。实际测试合并树c3554cbdbc85a73b7af8cb9d1f173f0df3604763，16张1024×640诊断303.51秒；Web artifact12054645611，Smoke可编辑Blender artifact12054291498。没有额外重复触发Spatial渲染，16图由Web构建中的同一诊断脚本生成。

下载后运行verify_web_cameras.py与verify_web_materials.py独立复核通过；1518个带底图primitive均有其指定UV、错误底图/法线复用0、法线贴图primitive0（明确为几何法线降级）、92面归一化回退。642个Curve对象转网格，2216个导出共享数据块；164362个面有导出投影UV。隐藏原型拒绝检查通过。

独立解析GLB：626279实例展开求值三角面，与Round29精确相等，非目标几何没有新增。7图片/44030496字节RGBA8估算亦精确相等。终版GLB52897192字节，较基线+8407840字节；818438个POSITION accessor顶点、29777038字节属性/索引估算，UV开销仍存在。该缓冲估算不是实际GPU驻留显存。

4张实际Chromium WebGL截图的位置误差均0，最大角误差2.98e-8弧度，页面脚本错误0；两组桌面截图与Round29相同机位、灯光、曝光、前端代码。屋瓦/木作/地坪不再黑面，木纹与墙面纹理可读；网页石瓦仍偏粗亮，BOX三向接缝/真正Normal烘焙/材质精美度未通过人工美术验收。网页导出没有Blender夜景灯光与雨雪，不能将两种渲染器的亮度差异冒充本轮美术升级。

PR36已合并为9d61e399e1240ce35b12071265174fde57a430ba。作者源生成脚本、全部16机位定义及网页灯光代码均未变化，Smoke实测4521对象/3005Mesh/1426Curve/4444驱动/7打包图。原始网格164746三角面与5254余量沿用Round29已验证源预算；本轮没有另行运行asset_budget.py，不将这项沿用值冒充本轮新测。新增验证是完整导出GLB三角面与纹理预算的独立对比。

- [CI38919284003](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38919284003)
- [Smoke38919284045及可编辑Blender](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38919284045/artifacts/12054291498)
- [Web38919283802：16原图、GLB、查看器及实截](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38919283802/artifacts/12054645611)
- [持久审阅图集](https://github.com/XDHRY/yanyu-jiangnan/blob/review/round-38919283802/docs/reviews/round-38919283802/README.md)

Function/Form/Runtime人工批准仍pending。skill要求的证据与批准分开记录，不将机器测试替代人工批准；本轮不部署线上场景。增加失败时16图与材质报告保存，首批不提供无法恢复的运行时截图。

## 下一轮

优先压低网页石瓦的粗亮感、检查主面投影接缝，并选择一组材质进行真实PBR/法线烘焙；不靠加曝光。将导出626279求值三角面、UV缓冲增长作为新性能基线，下一次改动应自动运行完整导出预算回归（本轮离线独立脚本已有实测，尚未接入CI硬门禁）。随后回到针线户织物转折/木作接缝，继续跟踪竖屏主体偏小及旋转中心8米近似。Function/Form/Runtime人工门禁、碰撞导航、正式LOD及全场景导出UV/法线专项仍pending。
