# Round36｜第7户局部法线、青白釉与烟道灰面

## 基线与范围

基线main013d2883b4d5015cedee9b02315349eba7d1f4ac，保留Round35及此前完整村镇、庭院园林、河街工坊和生活户。整体库XDHRY/yanyu-jiangnan；独立客栈库XDHRY/yanyu-jiangnan-ming-inn未改。先核对main、开放PR、Actions、LATEST、上轮交接、美术与资产预算，并复用Round35已验证原图和导出作对照。不回退旧main，不把文档数量当资产。

PR42实现源150d39eed91542960a741f909451de147ae1df9a，测试合并173ada9e3be0f8ebbd26d46083877ac22e8b5418。一个实现源commit，6个增量路径，保留完整父树；无重复dispatch或重叠改分支，未恢复36机位。14固定+2聚焦相机仍1024×640。

## 实际修改与边界

旧box()为向内面序，本轮不改全镇helper。仅对第7户11个私有闭合方盒Mesh审计签名体积，10个负体积才反转面序；已正向的灶背壁保持。逐块断言顶点坐标、顶点/面数及无向边集不变，所有共享用户限于本户；包括底座、侧壁、灶口边墩/过梁、台面长/端边、石踏、砧板与刀柄/刃。锅、碗、烟道布尔构造不改，不新增几何或实例，不靠手工场景绕过源码。

新增2种局部PBR、0新图像/对象/三角面：两只共享Mesh碗用JN_备膳青白釉，线性BaseColor(.48,.57,.50)、roughness .27、Coat .30/Coat Roughness .18，无石/瓦底图；5个烟道壁面用独立JN_备膳烟道灰面，隔离复制原石节点后复用plaster.png，线性乘色(.56,.57,.53)、roughness .88、Object BOX .60次/局部米、Bump .002m/Strength .08。原8个地面石材用户保留。来源、用途、尺度与许可见assets/architecture/house07-finish36/manifest.json、contract.md及textures/generation_prompts.json；无外部付费资产、无底色烘方向光。Web仍dominant-face UV近似，全镇UV/Normal/AO与正式LOD尚未完成。

本地19Python+3Node回归、编译与差异检查通过；机器检查不等于人工美术审批。build-3d-game-rooms通用Form实际退出1：完整工程图与人工记录未齐，通用Meshy付费/门窗型契约也不兼容零付费utility_flue；保留原失败日志，不修改验证器、不假造批准或付费资产。用户授权程序建模与诊断，未授权生产发布。

## 运行与实测（保留构建期间追踪，终版见后文）

CI39104593989、Smoke39104593990已通过；Smoke artifact12127747867下载CRC通过。4563对象、3046Mesh、1427Curve、170182顶点、98888面、52材质。源实例Mesh三角面166626/170000，余3374，较Round35不变。旧备膳/烟道通路、入口/支撑及11块体积检查通过。

Web39104594062通过，artifact12128176596与内部ZIP CRC通过，独立重跑16相机、材质/UV/PBR、实际预算通过：628555求值实例三角面、52992872字节GLB、29836942字节属性索引、9图RGBA8估算44554784字节/42.49MiB。源Mesh与求值导出口径不同；不是GPU实际驻留或FPS。未放宽任何预算。

Spatial39104594088仍在构建，本段不是最终合并/实图验收声明。待完整16图、导出全部几何与9图哈希独立比较后追加最终记录。

## 美术债务与下一轮

已查看本轮desktop16/mobile16真实网页截图：浅青釉面可辨，灰面烟道与白墙有了克制区分。灶体与地面粗石纹仍偏粗，屋脊旧图形细线仍可见；不宣称这些已修复。保持无火无烟，热工/抽力/消防、人工Function/Form/Runtime、实体手机、碰撞导航、全镇UV/Normal/AO与正式LOD仍pending。

本轮是既有第7户第三批精修，无新民居/新街区。完成本批后转向不同区域的生活功能或公共空间，不再连续堆同一户；先以最新全景/manifest定位可连通的小批次，守3374源三角面余量与9图预算。构造问题优先，付费生成和生产发布继续不启动。

## 终版独立复核与合并

最终四项全部通过：[CI39104593989](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/39104593989)、[Smoke39104593990/artifact12127747867](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/39104593990/artifacts/12127747867)、[Spatial39104594088/artifact12127134419](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/39104594088/artifacts/12127134419)、[Web39104594062/artifact12128176596](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/39104594062/artifacts/12128176596)。完整ZIP与Web内包CRC通过。

独立GLB逐Mesh节点比较全部局部坐标集合和三角面数，与Round35完全一致（允许UV/法线拆点差异）；15个可见目标闭合构件体积全正，旧轮其中14个为负。9嵌入原图SHA全部保留，16诊断相机和4网页相机参数逐项与Round35一致。1541带底图primitive具UV、1个独立切线法线图；新增釉面/灰面PBR实际导出值检查通过。4张Chromium/SwiftShader实截无页面错误、加载遮罩透明度0，不是实体手机测试。

最终预算即上文实测：源166626/170000余3374，4563对象、52材质，GLB628555三角面/52992872字节，属性索引29836942字节，9图42.49MiB RGBA8估算。与Round35三角面和图片不变，GLB少316字节、属性索引少2880字节；不把字节小变动当性能提升。Spatial16图314.46秒，Web另16图200.32秒；不同runner耗时不作优化因果结论。

已审完整16实图拼图、同相机前后、移动尺寸近景。浅青釉和烟道灰度变化真实可见，非目标村镇资产保留；灶体/地面粗石纹和屋脊细线仍列债务，未宣布精美完成。

合并前再核对main013d2883、PR42预期head150d39e和四项成功，正式合并ea58984f65e8646af76b77baa48b8dc03ce64233；测试合并与正式合并完整Git树相同c20376043a361b22b8466084c0ce56f3567e6d75。独立审阅含16原图、可编辑打包Blender、独立HTML内嵌GLB、4网页实截、旧Round35对照和来源/预算/法线/门禁日志；持久图集在[review/round-39104594088](https://github.com/XDHRY/yanyu-jiangnan/blob/review/round-39104594088/docs/reviews/round-39104594088/README.md)。分析脚本与打包脚本随分支保存，可重复运行。

审阅ZIP yanyu_round36_finish_review.zip：78024782字节、42项文件，SHA256=37b1a6aeb98c729eeded76eeee553e44c235ec49d618c8bbfce7a4bbdccb2bc4；已持久保存，文件身份libfile_5f63067986f88191bfd07b07d73c4029。源码已在Git，不重复备份仓库。合并后CI另行追踪，不把PR检查冒充push检查。

合并后main CI39105073970与Smoke39105073967均已通过；首个交接提交e010f229ac4ef69d85ff986c06129ccebcc2c4ec的CI39105189959通过。审阅分支提交c4738ec83fdb6474657a539fc31e054d34b5ab2c在完整交接父树上仅新增10个docs/reviews/round-39104594088文件；Git compare核实无其他变更，全部blob与本地git hash-object相同。脚本复现需将脚本置于含round35/round36原产物与yanyu-round36源码的审计工作目录，按source.json下载对应artifact，不能直接把缺输入的审阅目录当一键完整构建。
