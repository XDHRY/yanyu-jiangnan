# Round38｜导出退化三角面清理

基线main `2c4e2c92e1291f12fb4fed44f0f3af2dac348fd7`，完整保留Round37及之前所有庭院/村镇。开始时无开放PR、无运行中构建；先读最新交接、两份美术契约、补履资产manifest及Round37真实Web artifact12131796636。独立客栈库未改。

## 实际修改与边界

上轮GLB628919/629155只余236三角面。新增可复现`tools/web_topology.py`导出后处理，只删除至少两个POSITION完全重合的三角形，**没有epsilon、距离阈值、曲面简化、Decimate或近似共线剔除**。共享index accessor面对不同POSITION时，要求所有消费者都退化才删除，防止伤及另一几何。正面积微小三角形、全部源Blender顶点/面、所有材质/图片/UV/法线/变换及相机均不修改；只压缩专用索引bufferView并重排字节偏移。拒绝把整个primitive删除为空。源资产、工作流原内容、天气和驱动均保留。

Web导出调用后处理，并打包topology-audit.json。Spatial路径触发增加两个导出工具，以便此类无源几何更改仍有同commit16机位实渲，不手动重复dispatch、不恢复36机位。既有14固定及2聚焦机位全不改。

## 已运行的本地证据

- 25个Python回归及3个Node相机回归通过；覆盖零面积剔除、正面积1e-40级微型三角形保留、共享索引不同几何保留、幂等、截断拒绝、无近似共线剔除。
- 对Round37实际下载GLB运行：实例三角面删除4716，unique primitive面删除3136，材质/节点/图片描述不变，7528个非目标bufferView逐字节保留；文件53019040→53015892字节。该数字来自旧Round37产物的实测，不冒充本轮CI。
- 此步骤不降低源Mesh167094，也不减少对象/材质/图片数量；不会伪称新增建筑或渲染加速，实际运行帧率仍未测。

## 构建与验收

本轮新commit的CI/Smoke/Spatial/Web及16图尚待运行、下载和复看；通过前不合并、不把旧图当本轮效果。目标为GLB三角面624203（以实际构建值为准），同样629155上限绝不放宽。

沿用build-3d-game-rooms构造/证据门禁：此为既有用户授权的低成本诊断导出修复，不是生产发布。没有付费生成、无新素材；Function/Form/Runtime人工批准仍pending，通用Form不能由测试成功冒充。原粗石、完整UV/AO/LOD、碰撞导航、实体手机、屋脊细线与灶房热工等债务保持未验收。纹理来源沿用原manifest与提示词档案，不新增许可承诺。

下一步：确认非退化索引顺序完全保留、非索引buffer哈希/9图及全部16相机不变；查看本轮16实图和4个网页捕获，再记录实际commit/run/artifact、耗时、预算及前后对比。如验证通过，下一轮在余量内选公共节点材质精修，不立刻填满预算。

## 终版验证、真实图审及合并

上述待验证为历史状态；本节为2026-10-18实际终版。

- 源8bfa97e81031374d52c61b36f0a0c427bef08917；测试合并fe3b96da3e0056e125866de16ece78478def0343；[PR44](https://github.com/XDHRY/yanyu-jiangnan/pull/44)已合并为c920a3a822e8b8ed810ff782f0fe9ba043c36c09。测试与实际合并树同为22ab115c5b72335162cb63be58f4851170a6a16c。
- [CI39136620309](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/39136620309)、[Smoke39136620334](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/39136620334)、[Spatial39136620307](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/39136620307)、[Web39136620220](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/39136620220)全success。Smoke artifact12140341348、Spatial12139727624、Web12139354654下载及内包CRC通过；无重复dispatch，无并发分支更新。合并后CI39137303763及Smoke39137303761均已success。
- 4595对象、3077Mesh、1427Curve、170478顶点、99110源面、52材质、46灯、4444驱动不变。源实例Mesh167094/170000，余2906；实际GLB624203/629155，余4952（释放4716，约0.75%），53015892字节，attribute/index29846158字节。9图/44554784字节RGBA8估算42.49MiB不变，不是实测显存或FPS。drawcall/共享Mesh规模未改变，不宣称整体渲染加速。
- 180个primitive受影响，共删除3136个独立primitive三角面；复用实例后为4716。全部原非退化三角形按原顺序保留，2266个POSITION流与法线等非UV属性完全相同，节点、材质、相机、9张内嵌原图SHA均保持。
- 跨Round37/38重建有736个UV accessor浮点漂移，最大3.0517578125e-5，**略超上轮记录的3e-5审阅阈值，未放宽阈值或将该比较标为通过**。进一步用本次非索引属性和原索引还原清理前GLB，匹配实际source_sha256 fc6ca2d36373300eef2f8009273fdd1277de1d0e1d947ddb712c132f1f67e4b9；再清理逐字节得到本次最终GLB 822232362070a80f085a2bf9a91daa8da3d381b55c436af76e88a4c2f2edef4f。因而本次清理器不改UV，跨轮浮点漂移根因尚未归属，作为可重复构建债务保留；不能声称跨轮全BIN相同。
- 保留全部16机位（14固定+2聚焦），空间图204.26秒、Web构建内16图221.70秒；16张实图及4个真实浏览器捕获均已复看。网页4视口像素平均绝对RGB差最大0.000281/255，非完全同像素；浏览器错误0，姿态/旋转误差<1e-5，遮罩透明；不是实体手机验收。独立camera/material/budget工具复跑通过（1552贴图primitive有UV、1Normal贴图）。

美术复看：本轮目标是保持外观，未见灯罩、月门、木楦或建筑轮廓因清理而出现可见缺面；不把几乎不变的实图描述为美术升级。夜景暗部、粗石与瓦面尺度、Web平色降级等旧债务仍存在。没有新增建筑、陈设、材质、贴图或付费产物。

通用Form在现有补履证据包上实际运行exit1：工程投影/分层/覆盖、完整功能文件和人工批准等缺失，日志保留于审阅包；不得用成功CI冒充Function/Form/Runtime批准。不生产发布，正式LOD、碰撞导航、实体手机、屋脊细线和灶房热工仍pending。此轮应用3D技能的证据审阅与几何保守原则，不增加付费或审批声称。

独立审阅包yanyu_round38_topology_review.zip已打包CRC通过：45文件、76178490字节，SHA256 `82cb0b5066749080431a676f02b1a4f301e196c01d09c8986cbcb76ebddbdc55`。含16张本轮Spatial原图、Blend、单文件Web、4浏览器截图、旧Round37对照、逐文件哈希与独立审计。持久索引：[review/round-39136620307](https://github.com/XDHRY/yanyu-jiangnan/blob/review/round-39136620307/docs/reviews/round-39136620307/README.md)。本指针是证据，不代表额外资产。

独立ZIP已持久保存成功：libfile_6d03fc4641688191b08c5f0a33ffde3a（file_00000000479881f5ad3d7d1db00d8ec0），本地元数据关联成功。仓库代码无需重复保存；ZIP包含可审阅产物和证据。包在合并后Smoke完成前封装，后续状态以本交接为准，不为相同图像重复创建文件。

下一轮：优先公共生活节点材质尺度/粗石精修，保持源2906与GLB4952双预算，不立即填满几何；为UV导出浮点漂移增加确定性定位，不把清理器无修改与全流程确定性混为一谈。持续补正式UV/AO、LOD/碰撞与人工验收证据，保留所有旧区域，不退回旧main、不恢复36机位。
