"""Testbild: eine Figur im Lichtkegel, um Look und Renderzeit zu prüfen."""
import bpy, sys, time, math, os
sys.path.insert(0, os.path.dirname(__file__))
from figur import make_figure

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
rig = make_figure("A")

# leichte Standpose
pb = rig.pose.bones
pb["spine"].rotation_mode = pb["head"].rotation_mode = "XYZ"
pb["head"].rotation_euler = (0.12, 0, 0.1)
for s, sg in (("L", 1), ("R", -1)):
    pb[f"upper_arm.{s}"].rotation_mode = "XYZ"; pb[f"upper_arm.{s}"].rotation_euler = (0.05, 0, 0.06 * sg)
    pb[f"forearm.{s}"].rotation_mode = "XYZ"; pb[f"forearm.{s}"].rotation_euler = (0.15, 0, 0)

# Boden, Wand
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
fl = bpy.context.object; m = bpy.data.materials.new("floor"); m.use_nodes = True
b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.02, 0.02, 0.022, 1); b.inputs["Roughness"].default_value = 0.22
fl.data.materials.append(m)
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 6, 10), rotation=(math.pi / 2, 0, 0))
wl = bpy.context.object; m2 = bpy.data.materials.new("wall"); m2.use_nodes = True
b2 = m2.node_tree.nodes["Principled BSDF"]; b2.inputs["Base Color"].default_value = (0.03, 0.03, 0.035, 1); b2.inputs["Roughness"].default_value = 0.9
wl.data.materials.append(m2)

# Licht: weiches Flächenlicht von oben, schwaches Kantenlicht
bpy.ops.object.light_add(type="AREA", location=(0, -0.3, 3.4))
L = bpy.context.object.data; L.energy = 260; L.size = 0.8; L.color = (1.0, 0.86, 0.68)
bpy.ops.object.light_add(type="AREA", location=(-1.2, 1.6, 3.6), rotation=(math.radians(-35), math.radians(-25), 0))
R = bpy.context.object.data; R.energy = 60; R.size = 2; R.color = (0.7, 0.78, 1.0)
sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.004, 0.004, 0.005)

# Kamera
bpy.ops.object.camera_add(location=(0, -7.5, 1.35), rotation=(math.radians(88), 0, 0))
cam = bpy.context.object; cam.data.lens = 60; sc.camera = cam

sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = int(sys.argv[-1]) if sys.argv[-1].isdigit() else 48
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 3; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 2; sc.cycles.transmission_bounces = 0; sc.cycles.volume_bounces = 0; sc.cycles.use_adaptive_sampling = True
sc.render.resolution_x, sc.render.resolution_y = 720, 1280
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
sc.render.filepath = "/tmp/claude-0/fr/blender_still.png"
t = time.time(); bpy.ops.render.render(write_still=True); print("RENDER_SECONDS", round(time.time() - t, 1))
