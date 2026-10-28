# 烟雨江南 · 雪月江南

可编辑、可从源码重建的江南庭院与水镇 Blender 场景。庭院以斜梅、月门、曲水和听雨轩为中心，向双岸民居、桥梁、茶集、工坊、仓院和码头延伸。

**当前版本：Round 65 建模封顶候选（2026-10-28），已合并 main。** 五项工程检查全部通过。模型源 [`e9d69e6026`](https://github.com/XDHRY/yanyu-jiangnan/commit/e9d69e60263f6e1b611bdf13fcce730210f46064)；详见 [完整交接](docs/iterations/20261028-modeling-closeout.md)。

- [离线交互预览](https://chatgpt.com/library?file_id=libfile_e0af2c97d93481918c63031962dcbbad&account_id=personal)
- [完整模型与审阅包](https://chatgpt.com/library?file_id=libfile_ad4f174bf1e881918181bac4c5d6611e&account_id=personal)
- [16 图总览](https://chatgpt.com/library?file_id=libfile_0dd08c6ac85c8191ad82d84c9fc695cf&account_id=personal)

## 当前规模

| 指标 | 实测 |
|---|---:|
| 对象 | 4,668 |
| Mesh / Curve 对象 | 3,145 / 1,427 |
| 源网格含实例三角面 | 167,686 / 170,000 预算 |
| 材质 / 打包图像 | 58 / 15 |
| 图像 RGBA8 趋势估算 | 44.49 MiB |
| GLB 求值后含实例三角面 | 625,355 |
| 原生 GLB 动画 | 灯笼、舢板、店幌，共 3 段 |
| 空间审阅 | 16 张 1024×640 Eevee 图 |

本轮修复店幌的真实墙体支撑与相机检查阻塞；保持现有建筑范围、三角面和贴图预算。源网格与 GLB 求值几何是不同统计口径；图像估算不等于显存或 FPS。

## 使用与重建

- 下载上述模型包后，用 Blender 4.5.14 LTS 打开 `Jiangnan.blend`；纹理已打包。仓库根目录旧 `Jiangnan.blend` 是早期快照，当前权威模型来自与源码提交绑定的 CI 产物。
- 离线 HTML 约 71 MB，首次载入需要等待；手机请在支持 WebGL 的浏览器中打开。
- 完整场景、贴图、天气与驱动由 `jiangnan.py` 和 `textures/` 重建。额外 PBR 图会在构建中生成并打包。

```bash
mkdir -p build/textures
cp textures/*.png build/textures/
JN_OUT="$PWD/build" blender --background --python-exit-code 1 --python jiangnan.py
JN_OUT="$PWD/build" blender --background build/Jiangnan.blend --python-exit-code 1 --python tools/verify_render.py
```

控制对象 `JN_总控_天气0雨1雪_风力` 上的 `Weather` 为 0 雨 / 1 雪，`Wind` 为 0–2；时间轴 240 帧 / 24 fps。默认关闭高成本正式静帧，空间检查使用 16 机位诊断。

## 验收范围

本轮冻结现有建模范围，交付可审阅候选。人工 Function/Form/Runtime 批准、全场景 LOD、碰撞/导航、完整材质等价性和实体手机 FPS 仍未验收；不宣称达到 3A 成品质量。雨雪、水波、昼夜部分是查看器效果。

最新证据见 [交接](docs/iterations/LATEST.md)；历史协议见 [资产生产](docs/asset-production-loop.md) 和 [美术契约](docs/town-art-contract.md)。旧文档的轮次数据应以对应 SHA 的实测产物为准。

## 许可与来源

场景和脚本为本项目程序化创作；AI albedo 提示词在 `textures/generation_prompts.json`。本轮没有外部资产或付费生成。美术方向参考《燕云十六声》和《黑神话：悟空》，不代表成品质量等同。本仓库未附带开源许可，引用请联系所有者。
