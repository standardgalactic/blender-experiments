import bpy
import math

# Define the number of posts and their spacing in radians
num_posts = 8
spacing = (2 * math.pi) / num_posts

# Center position for the circle
center_x = 0.0
center_y = 0.0
center_z = 0.0

# Radius of the circle
radius = 3.0

# Create posts using primitive_uv_sphere_add
for i in range(num_posts):
    # Calculate the angle for the current post
    angle = i * spacing
    
    # Calculate the position for the current post on the circle
    x = center_x + radius * math.cos(angle)
    y = center_y + radius * math.sin(angle)
    z = center_z
    
    # Add a UV sphere at the calculated position
    bpy.ops.mesh.primitive_uv_sphere_add(
        size=0.5,  # Adjust size as needed
        location=(x, y, z)
    )
    
    # Rename the object for clarity
    obj = bpy.context.object
    obj.name = f"Post_{i+1}"
