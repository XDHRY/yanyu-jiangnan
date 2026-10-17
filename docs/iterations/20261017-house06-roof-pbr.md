# Round33｜第6户黛瓦PBR小样

## 最新基线与范围

整体库XDHRY/yanyu-jiangnan，基线main@0889e5b4c4730b15a1600bcb00d072e77a8fcb9c，包含全部既有村镇、Round31搭布和Round32室内石材。独立客栈库XDHRY/yanyu-jiangnan-ming-inn未改，不是别名。模型与渲染完成于2026-10-17；2026-10-18补齐中断前未写回的交接与持久图集，不把恢复的同轮实图冒充10月18日新渲染。

实现源7b0fed6c5f7a65984005eb196ae9c5deffb3cf21，[PR39](https://github.com/XDHRY/yanyu-jiangnan/pull/39)已合并为27e2043582f51d406e16c565d8b122cc894d8e21。测试合并bdc3cff156ef1d4a833072a087e96066fb1436ec与正式合并完整Git tree相同：8b97dcc6a4232fd51e32821fddb8812f09f0e143。提交始终基于完整父树增量创建、检查预期head，无目录树替换或并行覆盖。

## 实际资产与源码

仅第6户既有屋面隔离一个Mesh副本、新增一种JN_绣户黛瓦PBR材质。15顶点/8四边面、7厘米Solidify、屋脊、檐口、柱梁、台基、门窗和室内用途不改；未新增房屋或实例几何。其余3个标准屋面仍共用Mesh，高脊屋面组继续共享。源码断言逐顶点坐标和逐面索引确认小样与原标准屋面几何完全相同。

复用clay.png，线性BaseColor乘数(.48,.58,.68)，无方向光烘入。新增两张256×256、Non-Color的程序PNG，由jiangnan.py::roof_microtexel33/refine_house06_roof_pbr可重复生成、保存并打包入Blender：

- roof06_normal.png：周期高度场解析导数构建OpenGL切线法线，非彩色底图、非高低模烘焙。高度场三组谐波幅度100/35/20微米。
- roof06_orm.png：R=1中性AO，G=粗糙度约.54–.82，B=0非金属。没有声称已烘焙AO。

UV为JN_ROOF_MetreUV，以0.6米周期按对象实际X尺度与坡面弧长近似生成；上翘转角插值和完整UV打包仍待专项。源图、用途、公式、映射、许可、LOD边界见assets/architecture/house06-roof-pbr/。没有付费或外部新资产。沿用build-3d-game-rooms的用途/尺度/证据分离原则，不将机器检查当人工批准。

## 查看→修正→验证

首批75248f3通过CI，但其他构建被旧“标准屋面必须共用一个数据块”断言拒绝；没有合并失败构建。修订0bd6178明确隔离例外，保留其他共享及结构检查，增加与原Mesh坐标/拓扑严格相等检查，四项构建通过。

随后实图发现Web首张截图截到加载遮罩的0.5秒CSS淡出，整幅画面偏暗，不能当作材质改善。终版7b0fed6仅追加截图等待条件：模型ready后等待#loading.done的计算透明度小于0.001，逐张记录并检查loadingOverlayOpacity；不改曝光、灯光、模型或相机。所有中间构建结束后才更新分支，未重复触发同一head。

终版15项Python回归、3项Node相机回归通过；源材质单屋面范围、UV/贴图尺寸/Non-Color/打包/法线方向/粗糙度通过。导出与下载后独立检查实际normalTexture、独立metallicRoughnessTexture、BaseColorFactor、16个相机、真实GLB预算均通过。1519个带底图primitive有UV，1个primitive有独立切线法线图，底图法线混用0、缺UV 0。4张Chromium/SwiftShader实截遮罩透明度均0，位置误差0，最大角误差2.98e-8弧度，页面错误0；不是实体手机测试。

## 性能实测

4521对象、3005Mesh、1426Curve、169363顶点、98208源多边形、165134实例源网格三角面保持不变；源材质48（+1）。唯一Mesh1644（+1），唯一源三角面125620（+16，仅复制既有数据块），不是新增实例几何。源网格170000预算尚余4866。

实际GLB627155求值实例三角面不变；52922328字节（+122584）；属性/索引估算29792134字节不变。图片7→9，RGBA8估算44554784字节/42.49MiB（+524288字节/0.5MiB）；原七张内嵌图哈希全部保留。显式更新贴图预算，627155三角面、54MB文件/30MB缓冲门限没有放宽。这些估算不是实际GPU驻留显存或帧率测量。

Spatial16张1024×640合计310.77秒，Web另一组同16机位152.08秒；硬件负载差异不当作优化提速。10庭院+4村落核心+2聚焦机位全部保留，16相机位置/四元数/焦距/传感器/正交尺度与Round32相同，没有恢复36机位。

## 证据与美术检查

下列终版均通过：

- [CI38983726889](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38983726889)
- [Smoke38983726999 / Blender artifact12082028312](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38983726999/artifacts/12082028312)
- [Spatial38983727101 / 16张原图 artifact12082153678](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38983727101/artifacts/12082153678)
- [Web38983726795 / 查看器与实截 artifact12081723728](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/38983726795/artifacts/12081723728)
- 合并后main CI38984388869与Smoke38984388831均通过；2026-10-18核对无开放PR或进行中构建。
- [持久图集及来源JSON](https://github.com/XDHRY/yanyu-jiangnan/blob/review/round-38983727101/docs/reviews/round-38983727101/README.md)

已审完整拼图、15/16机位和桌面/竖屏实截：第6户亮白镜面高光减弱，黛灰哑面更均匀；邻屋、屋脊、檐口、柱梁、门洞和动线保留。前后图左为旧Round32/Web38965576491，右为Round33；上排Web实截，下排Blender，同机位/照明，没有后期提亮或概念图。

独立持久审阅包yanyu_round33_roof_pbr_review.zip，77407116字节、39项文件，含可编辑打包Blender、16张1024原图、独立HTML（含GLB）、4网页实截、2原始程序图、旧Round32对照、拼图、验证及来源JSON。SHA256=b583ea17ed45c1209c765d735f9d6328c964101e8206f0ef0218c2fc8f9acbeb；文件身份libfile_abf59064a2608191a4eb48c5f747a103。恢复后ZIP CRC和全部逐文件来源哈希再验证通过，没有重复制品或重复渲染。

## 区域状态、债务与下一轮

庭院/园林和既有河街工坊保留；8户原村真开口/地坪支撑持续通过断言。03书房、05起居和06针线房已在父树实现；本轮仅1户屋面PBR小样，不以文档数或Mesh副本数冒充新增建筑。

P2：夜景屋面偏暗、近景瓦列层次不足，微法线不能代替瓦片轮廓；完整UV、全镇Normal/AO、正式LOD、碰撞导航、竖屏主体偏小与旋转中心近似仍未完成。Function/Form/Runtime人工批准始终pending，不把单屋面样本当全镇美术完成或部署授权。

下一轮先比较本小样与相邻屋面的整体色阶，决定是否推广；避免连续只改同一户。随后在现有临街民居内选择灶作生活节点，保留通行与支撑，按4866源三角面剩余预算审阅扩建；若增加实例求值几何，先明确修改GLB预算契约，不能静默放宽。

待审经验pending：模型ready不代表加载遮罩已经淡出，截图应等待并记录计算透明度。经验只记录，不自动升级人工批准。
