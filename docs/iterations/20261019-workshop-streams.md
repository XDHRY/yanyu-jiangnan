# Round45｜修桨作坊局部无损属性共享

基线完整 main `95f9977784ff15680239400285e447760f09c6df`，含Round44和全部旧村镇。开始时无开放PR或活动构建。独立客栈库未改。无新建筑、对象、面、材质、贴图、灯、外部资产或付费生成。

先核第44轮真实Web artifact12163882968大小/SHA/CRC与GLB SHA c8552ff3a200b29647d34ae95a2f88e43bdb96c383c1f72a2ac492e03d727432。实际八腿POSITION/NORMAL重复，但UV并非全部逐字节一致，拒绝强行合并2完整Mesh。改为只对这8个命名目标的属性做元数据+bufferView逐字节匹配；差异UV保留，不舍入、不改变节点、材质绑定、Mesh项、索引或三角面。只删除不再使用的目标accessor/view；所有非目标未使用数据也保留。未知accessor消费者、压缩、动画、蒙皮、稀疏、morph扩展拒绝，不能静默损坏。

真实旧GLB隔离测试：删除14重复accessor/view，文件53057484→53019336 bytes，差38148；节点/材质/相机不改，7573保留buffer payload逐字节相同，幂等通过。这是隔离旧产物测试，尚不是本轮Actions产物；预计全场属性/索引回收35424 bytes，须实际构建确认。8Mesh项仍8，不宣称减少draw calls或FPS提升。

保留10庭院+4村镇核心+15舢板+16作坊，16×1024低成本，无36机位。源码生成模型不变，仍复跑原结构/支撑/Smoke与双预算。完整PBR/UV确定性、LOD/碰撞、实体手机、夜景暗部、挂桨动态/载荷与人工Function/Form/Runtime仍pending。通用Form标准文件/schema旧债未修复，沿用用户已授权既有诊断闭环，不作生产发布。

本轮真实Actions、前后对照、审计和持久包待完成，未验证代码不算最终交付。下轮先核最新主线/PR/Actions，转其他连通生活节点，不能只围绕作坊继续堆摆件或放宽预算。

## 最终已验证交接｜2026-10-19

前文为过程记录；当前以本节为准。

### 交付、完整性与真实闭环

- [PR51](https://github.com/XDHRY/yanyu-jiangnan/pull/51) 已合并。完整基线95f9977784ff15680239400285e447760f09c6df；源ebf8e713b73f3b7485c9c7e1a4dbacc47c91adf9；实际测试合并f281b17cac8c43a82e0ff050ac567efd6abe1d07；实际合并b5b4c1fbd2e778d6f90d1f86381d792ba22652c8。测试/实际树同为0d4d2a4da475726c0de974796d7d3b0238cd8f55，已逐一核4修改文件blob及完整父树，其他资产/工作流保留。独立客栈库未改。
- 只改导出属性存储，不新建区域/建筑/构件/对象/面/材质/贴图/灯。来源tools/web_shared_streams45.py，在原材质因子与精确退化面清理后执行；原jiangnan.py、映射、物理尺度、贴图来源/许可不变。无外部付费生成或手工场景绕过源码。
- 查看第44轮实际GLB后确认位置/法线重复、UV不同，拒绝原拟8→2完整Mesh合并。改为仅八个命名腿目标的相同属性流逐字节共享；元数据、stride、offset、normalized等全部参与匹配，UV差异不舍入。删除14不再使用的目标accessor/view；保留7573个view原字节及所有非目标未使用数据。8腿GLB mesh项仍8，draw calls未下降。
- 53 Python+3 Node通过；CI39211237989、Smoke39211237945、Spatial39211238005、Web39211237965全部success。既有31作坊接触/4罐底反向检查、4桨16底角承托射线、4枋柱搭接、8闭合源Mesh朝外法线均复跑通过。无重复dispatch，没有未完批次上叠改head。
- 已看本轮空间16图、Web构建内16图及实际桌面/竖屏4捕获；旧第44轮明确标旧，当前不使用概念图。相机与framing/exclusions逐字段保持：10庭院+4村镇核心+15舢板+16作坊，16×1024×640低成本；无36机位。
- 实际GLB独立审计：3113几何节点变换/全部Mesh条目/材质绑定、全部旧材质、9图SHA、全部索引、16相机保留，比较6735属性流。旧真实GLB隔离处理UV逐字节相同；本轮重建与上轮比较735条UV流浮点漂移最大6.103515625e-5，仍pending，不宣称完整二进制确定性。处理器本轮的保留payload为精确原字节，漂移在重新导出前已存在。

### 实测预算与性能

| 指标 | Round44 → Round45 |
|---|---:|
| 对象 / Mesh / Curve | 4620 / 3102 / 1427，保持 |
| 源顶点 / 面 / 实例三角面 | 171102 / 99678 / 168262，保持；上限170000余1738 |
| 源唯一Mesh / 唯一三角面 | 1691 / 127360，保持 |
| GLB实例三角面 | 625055，保持；上限629155余4100 |
| GLB bytes | 53057484 → 53019336，减少38148 |
| 属性+索引 bytes | 29873670 → 29838246，减少35424 |
| 属性+索引余量 | 126330 → 161754；上限30000000不变 |
| 材质 / 图 / 灯 / 驱动 | 54 / 9 / 46 / 4444，保持 |
| 源共享用户 / 复用率 | 1531 / 49.36%，保持 |
| 估算draw calls | 3105，保持；不冒充GPU实例优化完成 |
| 图像RGBA8估算 | 44554784 bytes = 42.49MiB，非实测VRAM |
| 本轮Spatial16图 / Web内16图 | 376.25 / 262.69秒，不同runner不宣称加速 |

二进制chunk节省35425含1字节末尾padding差异；属性逻辑流真实节省35424，文件另含JSON元数据回收。4实际Chromium/SwiftShader捕获ready、无page_errors、pose/rotation误差0、加载遮罩0；非实体手机、不代表FPS实测。

### 实际产物与持久审阅

- [Spatial39211238005](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/39211238005)：artifact12168595285，16140657bytes，SHA207611e67f16ea23b1fdef4f7f5ef10f9f5863f3ddec7432637821fc55b8e322。
- [Web39211237965](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/39211237965)：artifact12167554645，119821393bytes，SHA461cf4f20fcc4344eed324a9f29c43c309ff5bb0e84dfb1317a0a207111b42c1。
- Smoke39211237945：artifact12167592146，23686242bytes，SHA90f797d73dc434d9a2008049a74c808835bf593acfa70c7d511d156bf82c949c。3原artifact大小/SHA/CRC及Web内包CRC已核。
- 实际GLB SHA3deb283d063e1079510375673d1126e76f0422815de3581f7554305551ec4fc5；本轮未共享前SHA c802faca3d8e51ce6e52deff05e002bd07e5e616ecd9b88f8c78222c3715166c，不混同上轮c8552ff3开头的GLB。
- [持久图集](https://github.com/XDHRY/yanyu-jiangnan/blob/review/round-39211238005/docs/reviews/round-39211238005/README.md)：完整实际合并父树的独立review分支，含3拼图、独立审计脚本/结果、来源、通用Form日志和打包脚本。
- 独立审阅ZIP yanyu_round45_workshop_streams_review.zip 已成功保存，46文件、105987780bytes，SHA541e56b918b2d24469949b8eb618c3fcec32cc22aa7f43c8a23f5236d2a3f2b7。含可编辑blend、实际GLB、独立HTML、16原图、4网页捕获、明确标旧Round44对照与逐文件校验；无需重复保存Git源码。

### 美术检查、未完成与下一轮

本轮使用3D审阅技能的实际运行相机、原字节证据与不推断人工批准规则，保持结构与外观，不把缓冲优化宣称新增建模。屋檐—柱梁—台基、案腿/承托与通行保持；夜景作坊/舢板暗部依旧偏重，Web省略Blender灯/天气，较亮网页不能当夜景改善。

通用Form实际运行缺plan-metadata.json/final-report.json，3旧schema不匹配，5项失败保留；人工Function/Form/Runtime仍pending。沿用用户已明确授权的现有低成本诊断，不生产发布，不付费生成。全镇完整UV/PBR/Normal/AO、UV跨构建确定性、LOD/碰撞导航、实体手机、挂桨动态扣件/载荷与灶房热工未验收。尚未达到全镇最终目标，不停用持续任务。

下一轮：先读最新main/PR/Actions及本交接；转候船亭—候船横巷等不同连通公共生活节点，优先结构/通行/遮挡精修；利用回收的有限缓冲，不能盲目填满余量、继续给作坊堆陈设或放宽任何上限。若只改新共享helper，须同时确认Web/Spatial触发路径（当前由export_web.py改动触发），不要漏跑实际产物。

待批准经验（pending，未改共享approved规则）：源Mesh共享和法线/位置相同不保证完整GLB Mesh可无损共享；UV微差必须保留，可先做局部独立属性流精确共享。体积/面数预算通过仍须独立核属性缓冲。

合并后CI39212466311与Smoke39212466312均已完成success，无重复触发。持久审阅最终提交239af397fa8f95b03e3669f95f2b0eca3f833f20，基于完整实际合并父树，仅增加审阅内容；3拼图已在README显示。独立ZIP保存返回成功且本地版本标记已写回。
