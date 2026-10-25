"""Bewegungs-Regie: Gehzyklus mit festen Füßen, Beckenwippen und Nachschwingen.

Regeln, die eine Bewegung lebendig machen (statt mechanisch):
- Fuß steht fest, solange er Gewicht trägt (kein Rutschen) -> IK-Ziele bleiben stehen.
- Becken ist beim Aufsetzen am tiefsten, beim Durchschwingen am höchsten.
- Becken dreht und kippt leicht mit jedem Schritt, der Oberkörper dreht dagegen.
- Arme schwingen gegengleich zu den Beinen und ein paar Bilder verzögert,
  der Unterarm noch etwas später (Nachschwingen).
- Kopf bleibt ruhig und gleicht das Wippen etwas aus.
- Ferse setzt zuerst auf, Zehen lösen sich zuletzt.

Alles wird pro Bild als Keyframe gesetzt (gebacken), in Rig-Koordinaten:
vorne = -Y, seitlich = X, oben = Z.
"""
import math
from mathutils import Matrix, Vector, Euler


def _smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def _set(pb, loc=None, rot=None, frame=None):
    """Setzt einen Posenknochen und keyt ihn.

    rot: Drehung um die Achsen der Figur (vorne -Y, seitlich X, oben Z), relativ
    zum Elternknochen. loc: absolute Position im Rig (nur für Becken und Fußziele).
    """
    R = pb.bone.matrix_local.to_3x3()
    Ri = R.inverted()
    if rot is not None:
        pb.rotation_quaternion = (Ri @ rot.to_matrix() @ R).to_quaternion()
        pb.keyframe_insert("rotation_quaternion", frame=frame)
    if loc is not None:
        pb.location = Ri @ (Vector(loc) - pb.bone.matrix_local.translation)
        pb.keyframe_insert("location", frame=frame)


def walk(rig, f0, f1, fps=24, x0=0.0, speed=0.95, step_len=0.62, lift=0.13, crouch=0.06,
         bob=0.035, lean=0.04, arm_swing=0.35, head_down=0.0, sway=0.025,
         arm_base=0.0, hold_arm=None, phase=0.0, stop_at=None):
    """Lässt die Figur von Bild f0 bis f1 geradeaus gehen (in Rig-Richtung).

    speed: Meter pro Sekunde, step_len: Schrittlänge. lean: Vorbeugen (rad).
    hold_arm: "R" oder "L" -> dieser Arm wird nicht animiert (z. B. hält Schirm).
    stop_at: Bild, ab dem die Figur ausläuft und stehen bleibt.
    """
    import bpy
    sc = bpy.context.scene
    pbs = rig.pose.bones
    for pb in pbs:
        pb.rotation_mode = "QUATERNION"
    Ts = step_len / speed * fps            # Bilder pro Schritt
    swing = 0.42                            # Anteil des Fußzyklus in der Luft
    rest = {n: pbs[n].bone.matrix_local.translation.copy() for n in ("pelvis", "foot_ctrl.L", "foot_ctrl.R")}

    def body_dist(f):
        t = f - f0
        if stop_at is not None and f > stop_at:
            # weich auslaufen: noch eine halbe Schrittlänge
            d0 = (stop_at - f0) / Ts * step_len
            k = _smooth((f - stop_at) / (Ts * 1.2))
            return d0 + k * step_len * 0.6
        return t / Ts * step_len

    def foot(side, f):
        # Fuß-Zyklus über 2 Schritte; linker und rechter Fuß um einen Schritt versetzt
        off = 0.0 if side == "L" else 1.0
        c = ((f - f0) / Ts + off + phase) / 2.0
        n, u = math.floor(c), c - math.floor(c)
        # Stand: u in [0, 1-swing), Luft: u in [1-swing, 1)
        base = (n * 2 - off - phase) * step_len   # Position beim letzten Aufsetzen
        if stop_at is not None and f > stop_at:
            return min(base + 2 * step_len, body_dist(f) + 0.05), 0.0, 0.0
        if u < 1 - swing:
            return base + 0.5 * step_len, 0.0, 0.0
        s = (u - (1 - swing)) / swing
        e = _smooth(s)
        y = base + 0.5 * step_len + e * 2 * step_len
        z = lift * math.sin(math.pi * s ** 0.75)   # Fuß hebt früh ab, Knie beugt sich stark
        pitch = -0.55 * math.sin(math.pi * min(s * 1.6, 1)) * (1 - s) + 0.28 * _smooth((s - 0.7) / 0.3) * (1 - _smooth((s - 0.95) / 0.05))
        return y, z, pitch

    for f in range(f0, f1 + 1):
        moving = 1.0 if (stop_at is None or f <= stop_at) else 1 - _smooth((f - stop_at) / (Ts * 1.2))
        d = body_dist(f) + x0
        sp = ((f - f0) / Ts + phase)                 # Schritt-Phase
        w = math.cos(2 * math.pi * sp)               # +1 beim Aufsetzen, -1 beim Durchschwingen
        # Becken
        pz = rest["pelvis"].z - crouch - bob * (0.5 + 0.5 * w) * moving   # Becken etwas tiefer: Beine nie ganz gestreckt
        px = sway * math.sin(math.pi * sp) * moving
        yaw = 0.09 * math.sin(math.pi * sp) * moving
        roll = 0.04 * math.sin(math.pi * sp) * moving
        _set(pbs["pelvis"], loc=(px, -d, pz), rot=Euler((lean * 0.3, roll, yaw)), frame=f)
        _set(pbs["spine"], rot=Euler((lean, -roll * 0.5, -yaw * 1.3)), frame=f)
        _set(pbs["neck"], rot=Euler((head_down * 0.5, 0, yaw * 0.3)), frame=f)
        _set(pbs["head"], rot=Euler((head_down * 0.5 - 0.02 * w * moving, 0, 0)), frame=f)
        # Füße
        for side in "LR":
            fy, fz, pitch = foot(side, f)
            r = rest[f"foot_ctrl.{side}"]
            _set(pbs[f"foot_ctrl.{side}"], loc=(r.x, r.y - (fy + x0), r.z + fz), rot=Euler((-pitch * moving, 0, 0)), frame=f)
        # Arme: gegengleich, 2-3 Bilder verzögert, Unterarm noch später
        for side, sg in (("L", 1), ("R", -1)):
            if hold_arm == side:
                continue
            lag = 2.5 / Ts
            a = arm_swing * math.sin(math.pi * (sp - lag)) * sg * moving
            fa = arm_swing * 0.5 * math.sin(math.pi * (sp - lag * 2.2)) * sg * moving
            _set(pbs[f"upper_arm.{side}"], rot=Euler((-a + arm_base, 0, 0.06 * sg)), frame=f)
            _set(pbs[f"forearm.{side}"], rot=Euler((-max(fa, 0) * 0.8 - 0.25 - abs(a) * 0.3 + arm_base, 0, 0)), frame=f)
