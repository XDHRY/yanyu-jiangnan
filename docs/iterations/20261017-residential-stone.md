# 2026-10-17｜Round32 民居细磨青石与导出预算

## 基线与实际范围

整体库XDHRY/yanyu-jiangnan，基线main@03fbf7685add717f29d6150a8534b638ae1fc6a8，含Round31搭布、全部村镇与Round30材质导出修复。开始读取main、开放PR、Actions、最新交接、美术方向、美术契约和资产清单；无开放PR/进行中构建。恢复Round31 Web实际产物12063652099并查看desktop16，确认地坪与园林粗石共用材质，颗粒偏大、室内偏亮。独立客栈库未改。

首批源码d2d07a52cd15a1a8f2b02c48811382ea5f1f5e0c，[PR38](https://github.com/XDHRY/yanyu-jiangnan/pull/38)。从完整父树增量修改10路径，不删除非目标目录/工作流；无手动重复触发。使用build-3d-game-rooms技能检查尺度、用途、实际运行时与预算；不调用付费生成，不把诊断产物当人工批准。

## 资产与材质

新增1种细磨青石材质，仅分配给8栋原村民居室内地坪（仍1个共享Mesh）。不移动房屋、地坪、门洞、家具和灯具，不改机位/灯光，不新增几何。

复用textures/stone.png，来源/提示词/用途沿用textures/generation_prompts.json、docs/art-direction.md；现有项目生成素材，无新位图、外部许可或付费素材。Object-space BOX从原0.7次/局部米改为1.8次/局部米，名义平铺0.556米；线性RGB乘数(.45,.52,.54)，粗糙度.82，Specular IOR Level .25，源Bump距离从粗石.07米改为.004米/强度.16。没有把光影烘入BaseColor。

园林太湖石、室外青石街和屋瓦不改。本轮不是全场景PBR完成：源Bump仍是灰度近似，导出仍几何法线降级，BOX三向混合/接缝和真正切线Normal/AO烘焙仍待专项。8栋门洞与通行净宽不变，碰撞导航和正式LOD仍pending。

## 实际GLB预算硬门禁

新增tools/verify_web_budget.py及validation/web_budget_contract.json，并接入Web打包步骤与产物。解析活动glTF场景树，每个Mesh节点实例计一次；不把共享Mesh唯一面数当全场景成本。校验GLB完整长度/三角形拓扑/内嵌图片，统计实例求值三角面、实际文件字节、唯一accessor属性/索引缓冲估算、图片数和RGBA8估算。

本轮几何锁定Round31的627155求值三角面；GLB≤54000000字节、缓冲估算≤30000000字节、图片≤7、RGBA8≤44030496字节。以后几何扩建必须明确审阅并更新契约，不静默放宽。新增4项回归涵盖重复实例/排除非活动节点、几何增加或丢失、纹理/缓冲超限、截断GLB。9项Python、3项Node本地通过，上轮实际GLB通过新门禁。

## 运行证据

首批d2d07a5的CI38963983364通过，Smoke38963983447、Spatial38963983365、Web38963983353均被新增地坪材质使用范围断言拒绝，未出可审阅新图、未合并。原因：后续住宅区也复用了原村地坪Mesh，直接修改材质槽会影响本轮8户以外的实例（jiangnan.py原型复用见phase4）。没有放宽断言。

二次源80376f23c1da59989916167d71750af687ac0a8f，复制一个原地坪共享数据块，只让选定8户使用新材质；其他住宅保留原Mesh/原石材。唯一Mesh数据块增加1，实例总三角面应不变，不能宣称零缓冲代价。二次CI38964522715通过；其余实际结果如下。

二次Smoke38964522233和Spatial38964522394通过，Spatial artifact12074512687保存完整16图。已查看第16机位，地坪颗粒与凹凸感减弱；不是未经审图的修改。但Web38964522413被乘色门禁拒绝：glTF省略baseColorFactor，不接受以默认1替代源(.45,.52,.54)。该运行没有网页实截，不将失败产物12073604421（仅3个JSON）冒充查看器，16图保存在失败证据12074790285。

三次源c22b6db66afad6d88e02606d8639fc1c757dabdf：源材质明确声明JN_web_base_color_factor，报告传递该声明；新增web_material_factors.py只将该常量写到对应glTF材质，原二进制chunk逐字节保留。独立乘色/粗糙度检查不变，没有降低门槛。新增2项测试证明非目标材质与二进制保留、缺少声明材质被拒绝；现共11项Python和3项Node本地通过。三次构建全部通过，见终版结果。

## 终版验证与美术检查

三次CI38965576331、Smoke38965576419、Spatial38965576342、Web38965576491全部通过。下载后独立运行verify_web_cameras.py、verify_web_materials.py、verify_web_budget.py及审阅分析脚本均通过。实际测试合并a9df0a6946f15d0641e8aad34fdb595b7f51daf6；PR38已合并为a2219084ad11210fb712dfce6a1c830afe71e69c，二者Git tree相同。最终14条目标路径增量保留完整父树。

新测4521对象、3005Mesh、1426Curve、165134实例源网格三角面、98208多边形、169363顶点。唯一Mesh数据块1643（+1），唯一Mesh三角面125604（+12，仅复制既有数据块），对象实例三角面未增加；复用对象1458/48.52%，材质47（+1）。源网格全局170000余4866。7打包图片、RGBA8估算44030496字节/41.99MiB不变；预算warnings为空。

实际GLB627155求值三角面，与Round31完全一致；图片数7、7张内嵌图SHA256逐一与基线相同，确认没有把乘色烘成新图。GLB52799744字节（-111840），属性/索引估算29792134字节（+768，隔离Mesh的数据代价）。文件下降主要来自JSON紧凑UTF8编码，不是几何减少或实际GPU性能提升。新门禁已在本轮Web构建真实运行，不再只是离线待接入脚本。

Spatial16张1024×640共316.06秒，Web另一组同16机位诊断230.37秒；硬件/负载差异不能解释为材质优化提速。全部16机位位置、四元数、适配焦距、传感器和正交尺度与Round31相同。检查完整拼图、15/16原图及桌面/竖屏实截：屋檐—柱梁—台基、家具/布架支撑与动线不变；新地坪颗粒较细，粗亮感减弱，仍保有与木作区分。原石材斑驳仍偏明显，未标为极致材质完成。对比左图明确为旧Round31/Web38941563982，右为本轮终版；未换灯光/曝光或后期修图。

Web实际1519个带底图primitive有指定UV，错用底图作法线0；地坪baseColorFactor与roughnessFactor均通过独立检查。法线贴图primitive仍为0（几何法线降级）。4张Chromium/SwiftShader实截位置误差0，最大角误差2.98e-8弧度，页面脚本错误0；不是实体手机实测，竖屏主体仍偏小。

- [CI38965576331](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38965576331)
- [Smoke38965576419：可编辑Blender artifact12074308700](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38965576419/artifacts/12074308700)
- [Spatial38965576342：16原图与预算 artifact12075220576](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38965576342/artifacts/12075220576)
- [Web38965576491：GLB/独立HTML/实截/预算 artifact12074941846](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38965576491/artifacts/12074941846)
- [持久审阅图集](https://github.com/XDHRY/yanyu-jiangnan/blob/review/round-38965576342/docs/reviews/round-38965576342/README.md)

独立文件yanyu_round32_stone_review.zip包含可编辑打包Blender、16张1024原图、单文件HTML（含GLB及640预览）、4网页实截、Round31对照图、拼图、预算与来源JSON。以保存成功后的文件身份记录为准；不把缩略图当原始1024图。

审阅包已持久保存：77566710字节/37项文件，ZIP CRC通过，SHA256为08843c765863f469956476564304f737ad3b239913f6c3e387a1353688d59cc4，文件身份libfile_92c49f7ef2088191b917dfa64bb1d53e。可按精确文件名恢复；未重复保存整个Git源码树。

待审经验（pending）：修改共享Mesh的材质槽前，先枚举全部使用者；局部美术修订需要按用途分组隔离数据块并继续组内复用。新增范围断言确实阻止了一次非目标材质改写；不将该经验自行升为人工批准。

Function/Form/Runtime人工批准始终pending。本轮不部署线上场景，不将Chromium软件渲染代替实体手机体验。

## 下一轮

先解决本轮实图发现的问题，再选择单一屋瓦材质做PBR/法线烘焙小样，保留低成本16机位。竖屏主体偏小与旋转中心近似仍待处理；不要以增加曝光或几何细分掩盖材质问题。
