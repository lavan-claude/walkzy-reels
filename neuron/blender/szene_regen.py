"""Szene 'Gleicher Regen. Anderer Tag.' in Blender (Cycles).

Aufruf:  python szene_regen.py [vorschau F1 F2 ...] | [alles]
Rendert PNG-Bilder nach /tmp/claude-0/regen_bl/. Regen und Text kommen danach in post.py dazu.
"""
import bpy, sys, os, math, random
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figur import make_figure
from bewegung import walk

FPS, SECS = 24, 12
OUT = "/tmp/claude-0/regen_bl"
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, FPS * SECS
rng = random.Random(7)


def mat(name, color, rough=0.5, emit=None, strength=0.0):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes["Principled BSDF"] if m.node_tree else None
    if b is None:
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m


def box(name, size, loc, m):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = size
    o.data.materials.append(m)
    return o


# --- Welt: dunkler Nachthimmel
sc.world = bpy.data.worlds.new("nacht")
sc.world.use_nodes = True
bg = sc.world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.004, 0.005, 0.009, 1)
bg.inputs["Strength"].default_value = 1.0

# --- Nasse Straße mit Pfützen (Rauheit schwankt)
bpy.ops.mesh.primitive_plane_add(size=120, location=(20, 10, 0))
road = bpy.context.object
m = bpy.data.materials.new("strasse"); m.use_nodes = True
nt = m.node_tree; b = nt.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value = (0.012, 0.012, 0.015, 1)
noise = nt.nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 0.35; noise.inputs["Detail"].default_value = 3
ramp = nt.nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements[0].position = 0.45; ramp.color_ramp.elements[0].color = (0.03, 0.03, 0.03, 1)
ramp.color_ramp.elements[1].position = 0.6; ramp.color_ramp.elements[1].color = (0.32, 0.32, 0.32, 1)
nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
nt.links.new(ramp.outputs["Color"], b.inputs["Roughness"])
road.data.materials.append(m)

# Bordstein und Gehweg hinten
stone = mat("stein", (0.03, 0.03, 0.034), 0.6)
box("bordstein", (120, 0.3, 0.14), (20, 2.2, 0.07), stone)
box("gehweg", (120, 6, 0.14), (20, 5.3, 0.07), mat("gehweg", (0.02, 0.02, 0.024), 0.3))

# --- Skyline: Häuser mit Fenstern (Fensterbild aus Zufallsmuster, fester Startwert)
def window_image(w, h, name):
    px = np.zeros((h * 8, w * 8, 4), dtype=np.float32); px[..., 3] = 1
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if rng.random() < 0.13:
                warm = rng.random() < 0.8
                c = (1.0, 0.72, 0.42) if warm else (0.7, 0.82, 1.0)
                k = 0.35 + rng.random() * 0.65
                px[y * 8 + 2:y * 8 + 7, x * 8 + 2:x * 8 + 6, :3] = [ci * k for ci in c]
    img = bpy.data.images.new(name, w * 8, h * 8)
    img.pixels = px.ravel()
    return img

for i in range(16):
    w, h = 3 + rng.random() * 4, 5 + rng.random() * 9
    x, y = -12 + i * 4.2 + rng.random() * 1.5, 30 + rng.random() * 14
    box(f"haus{i}", (w, 3, h), (x, y, h / 2), mat(f"hauskorpus{i}", (0.008, 0.008, 0.01), 0.9))
    bpy.ops.mesh.primitive_plane_add(size=1, location=(x, y - 1.51, h / 2), rotation=(math.pi / 2, 0, 0))
    o = bpy.context.object; o.scale = (w, h, 1)
    hm = mat(f"haus{i}", (0.008, 0.008, 0.01), 0.9); o.data.materials.append(hm)
    hnt = hm.node_tree; hb = hnt.nodes["Principled BSDF"]
    tex = hnt.nodes.new("ShaderNodeTexImage"); tex.image = window_image(int(w * 4), int(h * 4), f"fenster{i}")
    tex.interpolation = "Closest"
    hnt.links.new(tex.outputs["Color"], hb.inputs["Emission Color"])
    hb.inputs["Emission Strength"].default_value = 2.2

# --- Laternen
pole_m = mat("mast", (0.02, 0.02, 0.024), 0.5)
head_m = mat("lampe", (0.1, 0.1, 0.1), 0.5, emit=(1.0, 0.78, 0.5), strength=40)
for x in (1.0, 7.5, 14.0):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=4.4, location=(x, 2.6, 2.2)); bpy.context.object.data.materials.append(pole_m)
    box("arm", (0.8, 0.05, 0.05), (x + 0.35, 2.6, 4.38), pole_m)
    box("kopf", (0.42, 0.22, 0.07), (x + 0.7, 2.6, 4.32), head_m)
    bpy.ops.object.light_add(type="SPOT", location=(x + 0.7, 2.5, 4.25))
    L = bpy.context.object; L.data.energy = 900; L.data.color = (1.0, 0.78, 0.52)
    L.data.spot_size = math.radians(95); L.data.spot_blend = 0.8; L.data.shadow_soft_size = 0.25
    L.rotation_euler = (math.radians(12), 0, 0)

# weiches Kühllicht von vorne, damit die Figuren lesbar sind
bpy.ops.object.light_add(type="AREA", location=(0, -9, 5))
fill = bpy.context.object; fill.data.energy = 750; fill.data.size = 8; fill.data.color = (0.6, 0.68, 0.95)
fill.rotation_euler = (math.radians(55), 0, 0); fill.visible_glossy = False
# Kantenlicht von hinten oben
bpy.ops.object.light_add(type="AREA", location=(0, 8, 6))
rim = bpy.context.object; rim.data.energy = 500; rim.data.size = 10; rim.data.color = (0.75, 0.8, 1.0)
rim.rotation_euler = (math.radians(-50), 0, 0); rim.visible_glossy = False

# --- Figuren
F = FPS * SECS
A = make_figure("A", color=(0.22, 0.22, 0.24)); A.location = (-1.25, 0.55, 0); A.rotation_euler = (0, 0, math.pi / 2)
B = make_figure("B", color=(0.92, 0.92, 0.92)); B.location = (-0.15, -0.55, 0); B.rotation_euler = (0, 0, math.pi / 2)
walk(A, 1, F, fps=FPS, speed=0.82, step_len=0.5, lift=0.06, bob=0.02, lean=0.22, head_down=0.55,
     arm_swing=0.12, sway=0.035)
walk(B, 1, F, fps=FPS, speed=0.95, step_len=0.62, lift=0.09, bob=0.035, lean=0.02, head_down=-0.05,
     arm_swing=0.3, hold_arm="R", phase=0.5)

# B hält den Schirm: rechter Arm angewinkelt nach vorne oben
from bewegung import _set
from mathutils import Euler
pb = B.pose.bones
for f in (1, F):
    _set(pb["upper_arm.R"], rot=Euler((-0.9, 0, -0.15)), frame=f)
    _set(pb["forearm.R"], rot=Euler((-1.0, 0, 0)), frame=f)

# Schirm hängt am Oberkörper von B
um_m = mat("schirm", (0.16, 0.16, 0.18), 0.3)
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.6, segments=48, ring_count=24, location=(0, 0, 0))
can = bpy.context.object
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="DESELECT"); bpy.ops.object.mode_set(mode="OBJECT")
for v in can.data.vertices:
    v.select = v.co.z < -0.02
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.delete(type="VERT"); bpy.ops.object.mode_set(mode="OBJECT")
can.data.materials.append(um_m)
bpy.ops.object.shade_smooth()
bpy.ops.mesh.primitive_cylinder_add(radius=0.012, depth=1.9, location=(0, 0, -0.95))
shaft = bpy.context.object; shaft.data.materials.append(um_m)
shaft.parent = can
from mathutils import Matrix
sc.frame_set(1); bpy.context.view_layer.update()
pbm = B.pose.bones["spine"].matrix.copy()
rest = B.data.bones["spine"].matrix_local.copy()
can.parent = B; can.parent_type = "BONE"; can.parent_bone = "spine"
bpy.context.view_layer.update()
can.matrix_world = B.matrix_world @ pbm @ rest.inverted() @ Matrix.Translation((-0.2, -0.42, 2.12)) @ Matrix.Diagonal((1, 1, 0.5, 1))

# --- Kamera folgt der Mitte zwischen beiden
bpy.ops.object.camera_add(location=(0, -11, 1.75), rotation=(math.radians(87.5), 0, 0))
cam = bpy.context.object; cam.data.lens = 50; sc.camera = cam
for f in range(1, F + 1, 6):
    t = (f - 1) / FPS
    xa, xb = -1.25 + 0.82 * t, -0.15 + 0.95 * t
    cam.location.x = (xa + xb) / 2 + 0.15
    cam.keyframe_insert("location", index=0, frame=f)

# --- Render-Einstellungen
sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"
sc.cycles.samples = 20; sc.cycles.use_adaptive_sampling = True; sc.cycles.use_denoising = True
sc.cycles.max_bounces = 3; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 2
sc.cycles.transmission_bounces = 0; sc.cycles.volume_bounces = 0
sc.render.use_persistent_data = True
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.45
sc.render.resolution_x, sc.render.resolution_y = 720, 1280
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
sc.view_settings.exposure = -0.2

# Dunst: Nebel-Pass im Compositor über die Ferne legen
sc.view_layers[0].use_pass_mist = True
sc.world.mist_settings.start = 22; sc.world.mist_settings.depth = 35
sc.use_nodes = True
sc.render.compositor_device = "CPU"
ct = sc.node_tree if hasattr(sc, "node_tree") and sc.node_tree else None
if ct is None:
    sc.compositing_node_group = bpy.data.node_groups.new("comp", "CompositorNodeTree")
    ct = sc.compositing_node_group
for n in list(ct.nodes):
    ct.nodes.remove(n)
rl = ct.nodes.new("CompositorNodeRLayers")
mix = ct.nodes.new("ShaderNodeMix") if not hasattr(bpy.types, "CompositorNodeMixRGB") else ct.nodes.new("CompositorNodeMixRGB")
try:
    mix.data_type = "RGBA"
except Exception:
    pass
inputs = [i for i in mix.inputs if i.enabled]
fac, ca, cb = inputs[0], inputs[1], inputs[2]
ct.links.new(rl.outputs["Mist"], fac)
ct.links.new(rl.outputs["Image"], ca)
cb.default_value = (0.012, 0.012, 0.02, 1)
out = None
for t in ("CompositorNodeComposite", "NodeGroupOutput"):
    try:
        out = ct.nodes.new(t); break
    except Exception:
        continue
if out.bl_idname == "NodeGroupOutput":
    ct.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
ct.links.new([o for o in mix.outputs if o.enabled][0], out.inputs[0])

frames = [int(a) for a in sys.argv if a.isdigit()]
if "alles" in sys.argv:
    sc.render.filepath = OUT + "/f_"
    sc.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(animation=True)
else:
    for f in frames:
        sc.frame_set(f)
        sc.render.filepath = f"{OUT}/f_{f:04d}.png"
        bpy.ops.render.render(write_still=True)
bpy.context.view_layer.update()
print("SCHIRM", tuple(round(c,2) for c in can.matrix_world.translation), "PELVIS", tuple(round(c,2) for c in (B.matrix_world @ B.pose.bones["pelvis"].head)))
print("FERTIG")
