"""Figuren-Werkstatt: baut eine weiche Minimal-Figur mit Skelett in Blender.

Die Figur ist ein durchgehender Körper (Skin-Modifier, geglättet) mit runder,
leicht abgesetzter Kopfkugel. Skelett mit IK-Beinen, damit Füße beim Gehen
fest auf dem Boden stehen bleiben.

Nutzung in einem Blender-Skript:
    from figur import make_figure
    rig = make_figure("A", color=(0.95, 0.95, 0.95))
Die Figur schaut nach -Y (zur Kamera, wenn die Kamera bei -Y steht).
"""
import bpy, bmesh
from mathutils import Vector

# Gelenkpunkte (Meter). x = seitlich, z = Höhe. Figur ca. 1,8 m.
J = {
    "pelvis": (0, 0, 0.98), "chest": (0, 0, 1.36), "neck": (0, 0, 1.47),
    "hip.L": (0.1, 0, 0.95), "knee.L": (0.105, -0.01, 0.52), "ankle.L": (0.11, 0.02, 0.07), "toe.L": (0.11, -0.1, 0.03),
    "hip.R": (-0.1, 0, 0.95), "knee.R": (-0.105, -0.01, 0.52), "ankle.R": (-0.11, 0.02, 0.07), "toe.R": (-0.11, -0.1, 0.03),
    "sho.L": (0.17, 0, 1.4), "elbow.L": (0.2, 0.02, 1.12), "wrist.L": (0.21, 0, 0.86),
    "sho.R": (-0.17, 0, 1.4), "elbow.R": (-0.2, 0.02, 1.12), "wrist.R": (-0.21, 0, 0.86),
}
EDGES = [("pelvis", "chest"), ("chest", "neck"),
         ("pelvis", "hip.L"), ("hip.L", "knee.L"), ("knee.L", "ankle.L"), ("ankle.L", "toe.L"),
         ("pelvis", "hip.R"), ("hip.R", "knee.R"), ("knee.R", "ankle.R"), ("ankle.R", "toe.R"),
         ("chest", "sho.L"), ("sho.L", "elbow.L"), ("elbow.L", "wrist.L"),
         ("chest", "sho.R"), ("sho.R", "elbow.R"), ("elbow.R", "wrist.R")]
RAD = {"pelvis": 0.085, "chest": 0.1, "neck": 0.038,
       "hip.L": 0.05, "knee.L": 0.04, "ankle.L": 0.034, "toe.L": 0.03,
       "hip.R": 0.05, "knee.R": 0.04, "ankle.R": 0.034, "toe.R": 0.03,
       "sho.L": 0.042, "elbow.L": 0.034, "wrist.L": 0.03,
       "sho.R": 0.042, "elbow.R": 0.034, "wrist.R": 0.03}
HEAD_R = 0.16
HEAD_Z = 1.69

# Knochen: name, kopf, schwanz, eltern
BONES = [
    ("root", (0, 0, 0), (0, 0.25, 0), None),
    ("pelvis", J["pelvis"], (0, 0, 1.12), "root"),
    ("spine", (0, 0, 1.12), J["chest"], "pelvis"),
    ("neck", J["chest"], J["neck"], "spine"),
    ("head", J["neck"], (0, 0, HEAD_Z + 0.1), "neck"),
]
for s in "LR":
    BONES += [
        (f"thigh.{s}", J[f"hip.{s}"], J[f"knee.{s}"], "pelvis"),
        (f"shin.{s}", J[f"knee.{s}"], J[f"ankle.{s}"], f"thigh.{s}"),
        (f"foot.{s}", J[f"ankle.{s}"], J[f"toe.{s}"], f"shin.{s}"),
        (f"upper_arm.{s}", J[f"sho.{s}"], J[f"elbow.{s}"], "spine"),
        (f"forearm.{s}", J[f"elbow.{s}"], J[f"wrist.{s}"], f"upper_arm.{s}"),
        # Steuer-Knochen (nicht verformend): Fußziel und Kniezeiger
        (f"foot_ctrl.{s}", J[f"ankle.{s}"], (J[f"ankle.{s}"][0], -0.15, J[f"ankle.{s}"][2]), "root"),
        (f"knee_pole.{s}", (J[f"knee.{s}"][0], -0.6, J[f"knee.{s}"][2]), (J[f"knee.{s}"][0], -0.7, J[f"knee.{s}"][2]), "root"),
    ]


def material(name, color, rough=0.42):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = 0.15
    return m


def make_figure(name, color=(0.92, 0.92, 0.92), location=(0, 0, 0)):
    col = bpy.data.collections.new(f"fig_{name}")
    bpy.context.scene.collection.children.link(col)
    mat = material(f"mat_{name}", color)

    # Körper aus Röhren mit runden Enden. Jede Röhre hängt an einem Knochen,
    # die Enden überlappen, dadurch bleiben die Gelenke bei jeder Pose nahtlos.
    parts = []
    def tube(a, b, ra, rb, bone):
        pa, pb = Vector(a), Vector(b)
        L = (pb - pa).length
        m = bpy.data.meshes.new(f"part_{name}_{bone}")
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=1.0)
        for v in bm.verts:  # Kugel zur Kapsel strecken, Radius zum Ende hin anpassen
            top = v.co.z > 0
            r = rb if top else ra
            v.co.x *= r; v.co.y *= r; v.co.z = v.co.z * r + (L if top else 0)
        bm.to_mesh(m)
        for poly in m.polygons:
            poly.use_smooth = True
        m.materials.append(mat)
        o = bpy.data.objects.new(f"part_{name}_{bone}", m)
        o.location = pa
        o.rotation_mode = "QUATERNION"
        o.rotation_quaternion = (pb - pa).to_track_quat("Z", "Y")
        col.objects.link(o)
        parts.append((o, bone))
    tube(J["pelvis"], J["chest"], 0.085, 0.1, "spine")
    tube(J["chest"], J["neck"], 0.04, 0.036, "neck")
    tube(J["sho.R"], J["sho.L"], 0.045, 0.045, "spine")
    tube(J["hip.R"], J["hip.L"], 0.06, 0.06, "pelvis")
    for s in "LR":
        tube(J[f"hip.{s}"], J[f"knee.{s}"], 0.055, 0.043, f"thigh.{s}")
        tube(J[f"knee.{s}"], J[f"ankle.{s}"], 0.043, 0.035, f"shin.{s}")
        tube(J[f"ankle.{s}"], J[f"toe.{s}"], 0.035, 0.03, f"foot.{s}")
        tube(J[f"sho.{s}"], J[f"elbow.{s}"], 0.042, 0.035, f"upper_arm.{s}")
        tube(J[f"elbow.{s}"], J[f"wrist.{s}"], 0.035, 0.03, f"forearm.{s}")

    # Kopf: Kugel, leicht abgesetzt
    hm = bpy.data.meshes.new(f"head_{name}")
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=HEAD_R)
    bm.to_mesh(hm)
    for p in hm.polygons:
        p.use_smooth = True
    hm.materials.append(mat)
    head = bpy.data.objects.new(f"head_{name}", hm)
    head.location = (0, 0, HEAD_Z)
    col.objects.link(head)

    # Skelett
    arm = bpy.data.armatures.new(f"rig_{name}")
    rig = bpy.data.objects.new(f"rig_{name}", arm)
    col.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    for bn, h, t, par in BONES:
        eb = arm.edit_bones.new(bn)
        eb.head, eb.tail = Vector(h), Vector(t)
        if par:
            eb.parent = arm.edit_bones[par]
            eb.use_connect = False
        if bn.startswith(("foot_ctrl", "knee_pole", "root")):
            eb.use_deform = False
    bpy.ops.object.mode_set(mode="OBJECT")

    # IK an den Beinen
    for s in "LR":
        pb = rig.pose.bones[f"shin.{s}"]
        ik = pb.constraints.new("IK")
        ik.target, ik.subtarget = rig, f"foot_ctrl.{s}"
        ik.pole_target, ik.pole_subtarget = rig, f"knee_pole.{s}"
        ik.pole_angle = -1.5708
        ik.chain_count = 2
        fb = rig.pose.bones[f"foot.{s}"]
        cr = fb.constraints.new("COPY_ROTATION")
        cr.target, cr.subtarget = rig, f"foot_ctrl.{s}"

    # Teile und Kopf fest an ihre Knochen hängen (Weltlage bleibt erhalten)
    parts.append((head, "head"))
    bpy.context.view_layer.update()
    for o, bone in parts:
        mw = o.matrix_world.copy()
        o.parent = rig
        o.parent_type = "BONE"
        o.parent_bone = bone
        bpy.context.view_layer.update()
        o.matrix_world = mw

    rig.location = location
    return rig
