"""Render one of 36 final 4K Jiangnan gallery shots."""
from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path
import bpy
from mathutils import Vector

SCENE_NAME = "烟雨江南 · 雪月江南"
CONTROL_NAME = "JN_总控_天气0雨1雪_风力"

# (slug, weather 0=rain/1=snow, existing camera suffix or None, custom camera)
SHOTS = {
  1: ("01-rain-hero-three-quarter",0,"三分之四",None),
  2: ("02-rain-front-courtyard",0,"正面",None),
  3: ("03-rain-borrowed-landscape",0,"顶视",None),
  4: ("04-snow-front-courtyard",1,"正面",None),
  5: ("05-snow-three-quarter",1,"三分之四",None),
  6: ("06-snow-elevated",1,"顶视",None),

  7: ("07-rain-water-west",0,None,((-11.0,-18.0,2.10),(0.2,3.4,2.05),48)),
  8: ("08-rain-water-east",0,None,((10.5,-17.0,2.25),(0.8,3.8,2.10),52)),
  9: ("09-rain-moon-gate-front",0,None,((9.8,-14.5,3.10),(-0.8,2.8,2.80),58)),
 10: ("10-rain-moon-gate-oblique",0,None,((14.0,-9.5,3.70),(-1.2,3.2,2.90),68)),
 11: ("11-rain-pavilion-west",0,None,((-11.5,-11.8,3.45),(2.8,4.7,3.00),62)),
 12: ("12-rain-pavilion-east",0,None,((12.8,-8.0,4.10),(2.0,4.6,3.05),65)),

 13: ("13-rain-side-garden-west",0,None,((-16.5,-4.5,4.60),(-0.5,2.8,2.70),55)),
 14: ("14-rain-side-garden-east",0,None,((16.2,-3.5,4.80),(0.0,3.1,2.75),58)),
 15: ("15-rain-bridge-low",0,None,((-5.0,-14.8,1.95),(1.0,4.2,2.30),44)),
 16: ("16-rain-courtyard-low",0,None,((2.5,-13.8,2.05),(0.0,3.2,2.45),46)),
 17: ("17-rain-eave-detail",0,None,((-8.4,-8.2,4.20),(1.8,3.8,4.00),82)),
 18: ("18-rain-plaster-and-window",0,None,((8.4,-7.5,3.50),(0.8,2.9,3.10),92)),

 19: ("19-rain-moon-reflection",0,None,((-2.0,-19.0,1.55),(1.5,5.0,2.00),72)),
 20: ("20-rain-lane-depth",0,None,((-14.0,-10.0,2.75),(1.2,4.5,2.65),60)),
 21: ("21-rain-high-north",0,None,((0.0,18.0,13.5),(0.0,1.5,2.40),70)),
 22: ("22-rain-high-south",0,None,((18.0,-22.0,12.0),(-1.0,3.0,2.40),72)),

 23: ("23-snow-water-west",1,None,((-10.5,-18.5,2.20),(0.4,3.3,2.10),50)),
 24: ("24-snow-water-east",1,None,((10.0,-18.0,2.35),(0.7,3.5,2.10),54)),
 25: ("25-snow-moon-gate",1,None,((10.2,-14.0,3.20),(-0.8,2.8,2.85),62)),
 26: ("26-snow-pavilion",1,None,((-10.8,-11.5,3.55),(2.8,4.7,3.05),66)),
 27: ("27-snow-side-garden",1,None,((-15.5,-4.0,4.80),(-0.3,3.0,2.75),58)),
 28: ("28-snow-bridge-low",1,None,((-4.5,-15.0,2.05),(1.0,4.0,2.30),46)),
 29: ("29-snow-courtyard",1,None,((3.0,-14.0,2.15),(0.0,3.4,2.45),48)),
 30: ("30-snow-high-oblique",1,None,((16.0,-18.0,11.0),(-1.0,3.0,2.50),68)),
 31: ("31-snow-roofline",1,None,((-13.5,-2.0,8.5),(1.0,3.5,4.20),78)),
 32: ("32-snow-lane",1,None,((-13.0,-10.5,2.90),(1.0,4.3,2.70),62)),

 33: ("33-rain-moon-close",0,None,((5.2,-8.5,6.8),(1.5,26.0,9.55),110)),
 34: ("34-rain-river-compressed",0,None,((-1.0,-23.0,3.0),(0.8,4.8,2.20),95)),
 35: ("35-rain-architecture-tele",0,None,((18.0,-12.0,5.5),(-1.0,3.5,3.2),105)),
 36: ("36-rain-poster-master",0,None,((20.0,-24.0,9.2),(-0.8,3.2,2.70),68)),
}
HERO_SHOTS={1,7,9,11,19,22,23,25,30,36}

def parse():
    argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    p=argparse.ArgumentParser()
    p.add_argument("--shot",type=int,required=True,choices=range(1,37))
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--width",type=int,default=3840)
    p.add_argument("--height",type=int,default=2160)
    p.add_argument("--samples",type=int,default=256)
    return p.parse_args(argv)

def look_at(obj,target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()

def custom_camera(scene,name,loc,target,lens):
    data=bpy.data.cameras.new("FINAL4K_"+name)
    obj=bpy.data.objects.new("FINAL4K_"+name,data)
    scene.collection.objects.link(obj)
    obj.location=loc
    data.lens=lens
    data.sensor_width=36
    data.clip_start=.04
    data.clip_end=800
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

    samples=max(cfg.samples,384 if cfg.shot in HERO_SHOTS else cfg.samples)
    scene.render.engine="CYCLES"
    scene.cycles.device="CPU"
    scene.cycles.samples=samples
    scene.cycles.use_denoising=True
    scene.cycles.use_adaptive_sampling=True
    scene.cycles.adaptive_threshold=.010
    scene.cycles.max_bounces=12
    scene.cycles.diffuse_bounces=4
    scene.cycles.glossy_bounces=5
    scene.cycles.transmission_bounces=6
    scene.cycles.volume_bounces=2
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
    print("FINAL_4K_GALLERY",json.dumps({
        "shot":cfg.shot,"file":str(out),"weather":weather,"camera":cam.name,
        "resolution":[cfg.width,cfg.height],"samples":samples,
        "seconds":round(time.time()-started,2)
    },ensure_ascii=False),flush=True)

if __name__=="__main__":
    main()
