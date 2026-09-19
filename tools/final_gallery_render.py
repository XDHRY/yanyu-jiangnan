"""Render one shot from the 12-view final Jiangnan gallery."""
from __future__ import annotations
import argparse, json, math, sys, time
from pathlib import Path
import bpy
from mathutils import Vector

SCENE_NAME = "烟雨江南 · 雪月江南"
CONTROL_NAME = "JN_总控_天气0雨1雪_风力"

SHOTS = {
  1: ("01-rain-hero-three-quarter", 0, "三分之四", None),
  2: ("02-rain-front-courtyard", 0, "正面", None),
  3: ("03-rain-borrowed-landscape", 0, "顶视", None),
  4: ("04-snow-front-courtyard", 1, "正面", None),
  5: ("05-snow-three-quarter", 1, "三分之四", None),
  6: ("06-snow-elevated", 1, "顶视", None),
  7: ("07-rain-water-level", 0, None, ((-9.5,-17.5,2.15),(0.2,3.6,2.05),48)),
  8: ("08-rain-moon-gate", 0, None, ((10.5,-14.0,3.20),(-1.0,2.8,2.85),58)),
  9: ("09-rain-pavilion-detail", 0, None, ((-10.8,-11.5,3.55),(2.8,4.7,3.05),62)),
 10: ("10-rain-side-garden", 0, None, ((-15.8,-4.2,4.70),(-0.6,2.8,2.70),55)),
 11: ("11-snow-water-level", 1, None, ((-8.8,-18.0,2.30),(0.4,3.2,2.15),52)),
 12: ("12-rain-high-oblique", 0, None, ((17.0,-18.0,10.5),(-1.0,3.0,2.40),64)),
}

def parse():
    argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser()
    p.add_argument("--shot",type=int,required=True,choices=range(1,13))
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--width",type=int,default=2560)
    p.add_argument("--height",type=int,default=1600)
    p.add_argument("--samples",type=int,default=320)
    return p.parse_args(argv)

def look_at(obj,target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()

def custom_camera(scene,name,loc,target,lens):
    data=bpy.data.cameras.new("FINAL_"+name)
    obj=bpy.data.objects.new("FINAL_"+name,data)
    scene.collection.objects.link(obj)
    obj.location=loc
    data.lens=lens
    data.sensor_width=36
    data.clip_start=.05
    data.clip_end=500
    data.dof.use_dof=False
    look_at(obj,target)
    return obj

def main():
    cfg=parse()
    scene=bpy.data.scenes.get(SCENE_NAME) or bpy.context.scene
    bpy.context.window.scene=scene
    control=bpy.data.objects.get(CONTROL_NAME)
    if control is None:
        raise RuntimeError("missing weather control")
    file_name,weather,existing,custom=SHOTS[cfg.shot]
    control["Weather"]=weather
    control.update_tag()
    scene.frame_set(80)
    bpy.context.view_layer.update()
    if existing:
        cam=bpy.data.objects.get("JN_"+existing)
        if cam is None or cam.type!="CAMERA":
            raise RuntimeError("missing camera JN_"+existing)
    else:
        loc,target,lens=custom
        cam=custom_camera(scene,file_name,loc,target,lens)
    scene.camera=cam
    scene.render.engine="CYCLES"
    scene.cycles.device="CPU"
    scene.cycles.samples=cfg.samples
    scene.cycles.use_denoising=True
    scene.cycles.use_adaptive_sampling=True
    scene.cycles.adaptive_threshold=.025
    scene.cycles.max_bounces=12
    scene.cycles.diffuse_bounces=4
    scene.cycles.glossy_bounces=4
    scene.cycles.transmission_bounces=6
    scene.render.resolution_x=cfg.width
    scene.render.resolution_y=cfg.height
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.image_settings.color_mode="RGB"
    scene.render.image_settings.color_depth="16"
    scene.render.film_transparent=False
    cfg.out.mkdir(parents=True,exist_ok=True)
    out=(cfg.out/(file_name+".png")).resolve()
    scene.render.filepath=str(out)
    started=time.time()
    bpy.ops.render.render(write_still=True)
    print("FINAL_GALLERY",json.dumps({
        "shot":cfg.shot,"file":str(out),"weather":weather,
        "camera":cam.name,"resolution":[cfg.width,cfg.height],
        "samples":cfg.samples,"seconds":round(time.time()-started,2)
    },ensure_ascii=False),flush=True)

if __name__=="__main__":
    main()
