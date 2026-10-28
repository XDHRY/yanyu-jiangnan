# 江南建模封顶候选 · 2026-10-28

仓库：`XDHRY/yanyu-jiangnan`。从 Round 64 主线继续，收尾 Round 65 / [PR #72](https://github.com/XDHRY/yanyu-jiangnan/pull/72)，已合并。

- 模型源：`e9d69e60263f6e1b611bdf13fcce730210f46064`
- 实际 PR 测试 ref：`bdf0317126edeac7f160eacce9a30db3d4ed1c8a`
- 主线合并：`54debe3e2694e44463d563d2c515ffcc9cd93e92`

## 最终交付

现有庭院、水巷民居、桥梁、茶集、工坊、仓院与码头组成一个可编辑、可复建场景。本轮冻结建模范围；没有新建区域，没有修改独立客栈库。

- [离线交互预览](https://chatgpt.com/library?file_id=libfile_e0af2c97d93481918c63031962dcbbad&account_id=personal)
- [完整模型与审阅包](https://chatgpt.com/library?file_id=libfile_ad4f174bf1e881918181bac4c5d6611e&account_id=personal)
- [16 图总览](https://chatgpt.com/library?file_id=libfile_0dd08c6ac85c8191ad82d84c9fc695cf&account_id=personal)

模型包包含 `.blend`、`.glb`、16 张原始 Blender 图和验证 JSON。15 张图像已打包入 Blender 文件；完整可复建源码仍由此仓库维护。离线 HTML 为 70,603,624 bytes，模型、纹理和查看器已内嵌；手机请用支持 WebGL 的浏览器打开，初次解析需要等待。

## 本轮修复与真实图闭环

1. 原 Round 65 `0999b6d4` 的第 16 相机指向丝行，取景检查却沿用约 33 m 外的舢板包络，导致 Spatial/Web/Offline 中断。
2. 改为测量挑杆、牌面与两条流苏在帧 40/80/120/200 的实际求值几何。保留 52 mm 焦距、4.5% 画面边距门槛、01–14 核心机位及 15 总览。
3. 牌顶原来比 2.28 m 悬挂轴低 50 mm；把上缘接到轴点，保留 1.53 m 下缘和流苏。新增真实牌面最近点距离检查。
4. 中间候选 `ae3cf296` 的实图又发现挑杆根部高于墙顶而悬空。将既有三点曲线根部改为 `(13.432,70.88,1.98)m`，嵌入既有西院墙 2 mm；补充真实墙面距离和包络验证。
5. 最终图确认墙—挑杆—牌面连接可读。未隐藏建筑、移动机位或放宽预算；修复没有增加三角面、材质、图片、灯光或建筑。

## 实测与测试

- [CI · 40616825327](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/40616825327)：success
- [Blender Smoke · 40616825357](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/40616825357)：success
- [Spatial 16 views · 40616825374](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/40616825374)：success
- [Web Viewer · 40616825435](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/40616825435)：success
- [Offline Runtime · 40616825324](https://github.com/XDHRY/yanyu-jiangnan/actions/runs/40616825324)：success

- 128 项 Python 检查、10 项 Node 检查通过。
- 4,668 对象；3,145 Mesh、1,427 Curve；99,554 源面；167,686 源网格含实例三角面，低于 170,000 上限。
- 58 材质、15 图像、48 灯、4,444 对象驱动器；图像 RGBA8 趋势估算 44.49 MiB。
- 16 张 1024×640 Eevee 诊断图；总渲染 208.98 秒。
- 牌面—悬挂轴最大测得误差 0.000000954 m；挑杆墙面嵌入 0.001999855 m。
- GLB 为 625,355 求值后含实例三角面、51,805,592 bytes；3 个独立具名 rotation clips：工作纱灯、系泊舢板、丝行招幌。
- 离线 file URL、0 外部请求、0 页面错误；三段运动及暂停冻结、雨雪/昼夜、区域导航与 390×844 布局检查通过。同机位运动差分 2,125 像素。

Blender 源三角面不展开所有修改器，与 GLB 求值后三角面不能混算。图像估算不是实测显存；Chromium SwiftShader 与手机尺寸仿真也不是实体手机 FPS 测试。

## 封顶边界

这是本轮建模收尾候选。庭院与镇区的细节密度、牌面内容、北段夜景层次及总览可见的背景环幕边缘仍未达到参考游戏的成品美术质量，不宣称 3A 终验通过。

人工 Function / Form / Runtime 批准继续 pending。严格技能证据包检查仍失败：缺少 `plan-metadata.json`，props、layout、openings 使用历史 schema。项目工程 CI 不替代该门禁。

尚未声明完成：全场景 LOD、碰撞与导航、所有材质的 UV/PBR 等价导出、实体手机帧率、流体/浮力/积雪/绳索动力学。雨雪、水波和昼夜部分为查看器效果。

本交接不启动新的自动迭代或扩建任务。后续工作若开启，属于独立的美术或游戏运行时阶段。
