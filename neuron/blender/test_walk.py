"""Gehtest: Figur von der Seite, einige Bilder in niedriger Auflösung."""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
from figur import make_figure
from bewegung import walk
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.fps = 24
rig = make_figure("A"); rig.rotation_euler = (0, 0, math.pi / 2)   # geht nach +X
walk(rig, 1, 72, speed=1.0)
cam_follow = True
bpy.ops.mesh.primitive_plane_add(size=60)
m = bpy.data.materials.new("f"); m.use_nodes = True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.05, 0.05, 0.055, 1)
bpy.context.object.data.materials.append(m)
bpy.ops.object.light_add(type="SUN", rotation=(0.6, 0.3, 0.4)); bpy.context.object.data.energy = 3
sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.05, 0.05, 0.06)
bpy.ops.object.camera_add(location=(1.0, -4.2, 0.9), rotation=(math.radians(90), 0, 0)); sc.camera = bpy.context.object
sc.camera.data.lens = 35
sc.render.engine = "BLENDER_WORKBENCH" if "wb" in sys.argv else "CYCLES"
sc.cycles.samples = 4; sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 480, 360
for f in ([int(a) for a in sys.argv if a.isdigit()] or range(1, 49)):
    sc.camera.location.x = 0.2 + f / 24 * 1.0; sc.frame_set(f); sc.render.filepath = f"/tmp/claude-0/fr/w_{f:03d}.png"; bpy.ops.render.render(write_still=True)
print("OK")
