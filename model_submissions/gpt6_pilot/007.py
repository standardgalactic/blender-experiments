"""Model-authored pilot: eight separate cylindrical posts at equal angular intervals."""
import bpy
from math import cos, sin, tau

for index in range(8):
    theta = tau * index / 8
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=24,
        radius=0.2,
        depth=1.6,
        location=(3.0 * cos(theta), 3.0 * sin(theta), 0.8),
    )
    bpy.context.object.name = f"Post_{index:02d}"
