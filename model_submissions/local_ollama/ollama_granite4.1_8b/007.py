import bpy
import math

# Clear the default scene
bpy.ops.wm.read_factory_settings(use_all_addons=False)

# Define parameters
radius = 3.0
num_posts = 8

# Calculate angle step
angle_step = 2 * math.pi / num_posts

# Create eight distinct posts on a circle of radius 3 in the XY plane
for i in range(num_posts):
    # Calculate position on the circle
    angle = i * angle_step
    x = radius * math.cos(angle)
    y = radius * math.sin(angle)
    z = 0.0

    # Create a new cylinder (post) at the calculated position
    bpy.ops.mesh.primitive_cylinder_add(radius=0.1, depth=1.0, location=(x, y, z))
    
    # Get the newly created object
    post = bpy.context.active_object
    
    # Optionally, name the post for clarity
    post.name = f'Post_{i+1}'
