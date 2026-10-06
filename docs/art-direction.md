# 烟雨江南 / 雪月江南 — 美术指导

营造一处可步入、可停留的江南夜庭。以《燕云十六声》的写意山水与古建气韵为方向，以《黑神话：悟空》的材质分量和幽深层次校准。画面主次是“斜梅—月门—远山”，冷月塑形，暖灯只照亮局部；粉墙有湿痕，黛瓦有岁月，苔石有孔隙，花瓣有透光。用前景遮挡、曲折动线、借景与留白营造道家意境。风、雨、雪、云、水各有节奏。每项细节必须在镜头中发挥作用，每轮都用真实 Blender 渲染审视，而不能仅以对象齐全为完成标准。

## 验收标准

- 第一眼感知月、梅与空庭，而不是矩形底板与整齐排列的模型。
- 白墙、瓦、石、木、树皮应具有不同的尺度、纹理方向和反射特征。
- 园林的曲折、障景、借景、疏密与枯荣，应由真实的空间关系成立。
- 主体近景需有可读细节；中景有节奏；远景退隐于云雾。
- 3D 几何、灯光、材质和动态保持可编辑。概念图不能冒充场景渲染。
- 生图资产须保存、映射到对应资产、打包进 .blend；保留提示词和用途记录。

## 生成方式

使用内置 image_gen。下面各段为实际生成提示词，材质按独立资产生成，不将不同材质混装为拼贴图。

### 01 古白墙 / plaster_albedo

Use case: photorealistic-natural. Asset type: production albedo texture for a Blender Jiangnan classical garden wall. A square, straight-on orthographic material scan of aged off-white lime plaster from a refined historic Suzhou courtyard. Extremely detailed fine chalky lime grains, hairline irregular cracks, restrained pale warm-gray mineral variation and subtly damp cool-gray mottling. Quiet elegant weathering, mostly intact plaster, no exposed bricks. Flat uniform neutral illumination, no cast shadows, no light gradients, no ambient occlusion baked in. Seamlessly tileable on all four sides, non-directional, full bleed. Neutral ivory-gray color, not yellow. No objects, frames, text, grids, watermark, scenery or perspective. Material texture only, high resolution.

### 02 苔石 / moss_stone_albedo

Use case: photorealistic-natural. Asset type: production albedo texture for sculpted scholar rocks and garden shore rocks in Blender. Square orthographic close material scan of ancient Jiangnan gray limestone with muted charcoal mineral veins, tiny erosion pits, pale calcite speckles, thin restrained olive-gray moss and lichen scattered irregularly over about twenty percent of the surface. Realistic fine-scale microstructure, substantial natural stone, refined restrained colors, no neon greens. Seamlessly tileable in both directions. Flat diffuse cross-polarized lighting, no baked highlights, shadows or perspective. Full frame continuous rock material only, no isolated rock object, no background, text, borders, grids or watermark. High resolution game environment material.

### 03 苍梅树皮 / plum_bark_albedo

Use case: photorealistic-natural. Asset type: seamless bark albedo texture for editable 3D ancient plum trunks in Blender. Square orthographic macro material scan of old Chinese flowering plum bark. Deep vertical meandering fissures and fine irregular flaking ridges, subtly twisted age lines, charcoal umber with desaturated warm gray highlights, sparse dusty sage lichen. Detailed but restrained, believable aged tree surface. Grain runs vertically. Seamlessly tileable left-right and top-bottom. Flat neutral diffuse lighting, no shadows or glossy highlights baked in, no cylinder shape or perspective, no tree silhouette, no scenery, no words, border, labels, grid or watermark. High resolution material texture only.

> 以下 04–07 四段录自 `textures/generation_prompts.json`（同批实际生成提示词），与原三段合并存档。

### 04 黛瓦黏土 / clay_albedo

Use case: photorealistic-natural. Asset type: seamless base color texture to apply on individual 3D traditional Chinese roof tiles. Square flat orthographic material scan of weathered dark charcoal blue-gray fired clay, subtle fine mineral speckles, tiny pits, faint irregular ancient soot and silvery wear, a little dusty muted sage lichen. Refined old Jiangnan black clay roof material, rich detailed matte surface. Continuous material only, NO tile outlines, NO roof shapes, NO grout lines. Even diffuse neutral cross polarized lighting with NO directional shadows or highlights baked in. Seamless all four sides. No words, borders, objects, perspective, montage or watermarks. High resolution.

### 05 老木 / wood_albedo

Use case: photorealistic-natural. Asset type: seamless albedo for a Blender historic Chinese wooden tea pavilion. Square straight-on orthographic scan of old dark warm walnut-umber timber, vertical long close wood grain, fine worn cracks, restrained traces of age, subtle hand-polished areas, traditional natural oil finish. No separate planks or panel boundaries. Dark desaturated refined wood, not orange, not glossy. Flat neutral diffuse illumination with no baked shadows or specular highlights. Tileable left right and top bottom. Full-frame material only, high detail, no text, no frame, no watermark, no objects.

### 06 梅花瓣 / petal_albedo

Use case: photorealistic-natural. Asset type: square albedo texture mapped across one 3D plum blossom petal. Extreme macro close-up of pale blush-white plum petal tissue, entire frame filled with petal material, base at bottom-center gently warmer dusty carmine, outer tip at top softly ivory, extraordinarily fine branching translucent veins fanning upward, subtle silken living cells, restrained soft color variation, delicate waxy natural botanical material, realistic not painted. Flat neutral illumination, no cast shadows, no scenery, no petal outline, no background, no lettering, no grid, no watermark. Image will be applied to curved petal geometry. High resolution.

### 07 远山夜景 / landscape_background

Use case: stylized-concept. Asset type: wide panoramic distant background painting used ONLY behind an editable Blender Jiangnan courtyard. Ultra-wide 3:1 landscape, no foreground architecture. Remote Chinese Jiangnan lake and layered low mountain silhouettes, poetic Song dynasty landscape composition rendered with realistic atmospheric depth, nocturnal indigo and charcoal blue-gray, delicate low milky mist drifting between foothills, pale muted blue twilight along horizon, dark open sky in upper 60 percent, still dark lake lower 15 percent. Night, restrained low contrast so foreground garden dominates. No moon (a separate 3D moon will be added), no stars, no boats, no people, no buildings, no dominant trees, no text, no border, no watermark, no bright highlights. Elegant meditative Taoist emptiness, subtle grain, believable landscape, painterly only in distant silhouettes. Horizon level, frontal camera, no perspective distortion.
