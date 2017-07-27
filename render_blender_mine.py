# A simple script that uses blender to render views of a single object by rotation the camera around it.
# Also produces depth map at the same time.
#
# Example:
# blender --background --python mytest.py -- --views 10 /path/to/my.obj
#

import argparse, sys, os
parser = argparse.ArgumentParser(description='Renders given obj file by rotation a camera around it.')
parser.add_argument('--views', type=int, default=36,
                   help='number of views to be rendered')
parser.add_argument('obj', type=str,
                   help='Path to the obj file to be rendered.')
parser.add_argument('--output_folder', type=str, default='/tmp',
                    help='The path the output will be dumped to.')
parser.add_argument('--remove_doubles', type=bool, default=True,
                    help='Remove double vertices to improve mesh quality.')
parser.add_argument('--edge_split', type=bool, default=True,
                    help='Adds edge split filter.')

argv = sys.argv[sys.argv.index("--") + 1:]
args = parser.parse_args(argv)
f = args.obj

import bpy
from mathutils import Vector


# Set up rendering of depth map:
bpy.context.scene.use_nodes = True
tree = bpy.context.scene.node_tree
links = tree.links

# Add passes for additionally dumping albed and normals.
bpy.context.scene.render.layers["RenderLayer"].use_pass_normal = True
bpy.context.scene.render.layers["RenderLayer"].use_pass_color = True

# clear default nodes
for n in tree.nodes:
    tree.nodes.remove(n)

# create input render layer node
rl = tree.nodes.new('CompositorNodeRLayers')

map = tree.nodes.new(type="CompositorNodeMapValue")
# Size is chosen kind of arbitrarily, try out until you're satisfied with resulting depth map.
map.offset = [-0.7]
map.size = [0.8]
# map.use_min = True
# map.min = [0]
# map.use_max = True
# map.max = [255]
links.new(rl.outputs['Z'], map.inputs[0])

invert = tree.nodes.new(type="CompositorNodeInvert")
links.new(map.outputs[0], invert.inputs[1])

# create a file output node and set the path
depthFileOutput = tree.nodes.new(type="CompositorNodeOutputFile")
depthFileOutput.label = 'Depth Output'
links.new(invert.outputs[0], depthFileOutput.inputs[0])

scale_normal = tree.nodes.new(type="CompositorNodeMixRGB")
scale_normal.blend_type = 'MULTIPLY'
#scale_normal.use_alpha = True
scale_normal.inputs[2].default_value = (0.5, 0.5, 0.5, 1)
links.new(rl.outputs['Normal'], scale_normal.inputs[1])

bias_normal = tree.nodes.new(type="CompositorNodeMixRGB")
bias_normal.blend_type = 'ADD'
#bias_normal.use_alpha = True
bias_normal.inputs[2].default_value = (0.5, 0.5, 0.5, 0)
links.new(scale_normal.outputs[0], bias_normal.inputs[1])


normalFileOutput = tree.nodes.new(type="CompositorNodeOutputFile")
normalFileOutput.label = 'Normal Output'
links.new(bias_normal.outputs[0], normalFileOutput.inputs[0])

albedoFileOutput = tree.nodes.new(type="CompositorNodeOutputFile")
albedoFileOutput.label = 'Albedo Output'
# For some reason,
links.new(rl.outputs['Color'], albedoFileOutput.inputs[0])

# Delete default cube
bpy.data.objects['Cube'].select = True
bpy.ops.object.delete()



bpy.ops.import_scene.obj(filepath=f)
print(list())
for object in bpy.context.scene.objects:
    if object.name in ['Camera', 'Lamp']:
        continue
    bpy.context.scene.objects.active = object
    # Some examples have duplicate vertices, these are removed here.
    if args.remove_doubles:
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.remove_doubles()
        bpy.ops.object.mode_set(mode='OBJECT')
    if args.edge_split:
        bpy.ops.object.modifier_add(type='EDGE_SPLIT')
        bpy.context.object.modifiers["EdgeSplit"].split_angle = 1.32645
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier="EdgeSplit")


# Make light just directional, disable shadows.
lamp = bpy.data.lamps['Lamp']
lamp.type = 'SUN'
lamp.shadow_method = 'NOSHADOW'
# Possibly disable specular shading:
lamp.use_specular = False

# Add another light source so stuff facing away from light is not completely dark
bpy.ops.object.lamp_add(type='SUN')
lamp2 = bpy.data.lamps['Sun']
lamp2.shadow_method = 'NOSHADOW'
lamp2.use_specular = False
lamp2.energy = 0.2
bpy.data.objects['Sun'].rotation_euler = bpy.data.objects['Lamp'].rotation_euler
bpy.data.objects['Sun'].rotation_euler[0] += 180

bpy.ops.object.lamp_add(type='SUN')
lamp3 = bpy.data.lamps['Sun']
lamp3.shadow_method = 'NOSHADOW'
lamp3use_specular = False
lamp3.energy = 0.2
bpy.data.objects['Sun.001'].rotation_euler = bpy.data.objects['Lamp'].rotation_euler
bpy.data.objects['Sun.001'].rotation_euler[0] += 90


def parent_obj_to_camera(b_camera):
    origin = (0,0,0)
    b_empty = bpy.data.objects.new("Empty", None)
    b_empty.location = origin
    b_camera.parent = b_empty #setup parenting

    scn = bpy.context.scene
    scn.objects.link(b_empty)
    scn.objects.active = b_empty
    return b_empty

scene = bpy.context.scene
scene.render.resolution_x = 600
scene.render.resolution_y = 600
scene.render.resolution_percentage = 100
scene.render.alpha_mode = 'TRANSPARENT'
cam = scene.objects['Camera']
# cam.location = Vector((0, 1, 0.6))
cam.location = (0, -1.5, 0.08)
cam_constraint = cam.constraints.new(type='TRACK_TO')
cam_constraint.track_axis = 'TRACK_NEGATIVE_Z'
cam_constraint.up_axis = 'UP_Y'
b_empty = parent_obj_to_camera(cam)
cam_constraint.target=b_empty



model_identifier = os.path.split(os.path.split(args.obj)[0])[1]
fp = os.path.join(args.output_folder, model_identifier, model_identifier)
scene.render.image_settings.file_format = 'PNG' # set output format to .png

from math import radians

stepsize = 360.0 / args.views
rotation_mode = 'XYZ'

for output_node in [depthFileOutput, normalFileOutput, albedoFileOutput]:
    output_node.base_path = ''


def get_bbox_world():
    points = []
    for obj in bpy.data.objects:
        if obj.name in ['Empty', 'Camera', 'Sun', 'Lamp']:
            continue
        points += [v[:] for v in obj.bound_box]
    xmin = min([p[0] for p in points])
    xmax = max([p[0] for p in points])
    ymin = min([p[1] for p in points])
    ymax = max([p[1] for p in points])
    zmin = min([p[2] for p in points])
    zmax = max([p[2] for p in points])
    return xmin, xmax, ymin, ymax, zmin, zmax

import bpy_extras
def get_pixel_coord(worldp):
    scene = bpy.context.scene
    obj = bpy.data.objects[0]
    co_2d = bpy_extras.object_utils.world_to_camera_view(scene, obj, worldp)
    print("2D Coords:", co_2d)

    # If you want pixel coords
    render_scale = scene.render.resolution_percentage / 100
    render_size = (
            int(scene.render.resolution_x * render_scale),
            int(scene.render.resolution_y * render_scale),
            )
    print("Pixel Coords:", (
          round(co_2d.x * render_size[0]),
          round(co_2d.y * render_size[1]),
          ))
    return co_2d.x * render_size[0], render_size[1] - co_2d.y * render_size[1]


for i in range(0, args.views):
    print("Rotation {}, {}".format((stepsize * i), radians(stepsize * i)))

    scene.render.filepath = fp + '_r_{0:03d}'.format(i)
    depthFileOutput.file_slots[0].path = scene.render.filepath + "_depth"
    normalFileOutput.file_slots[0].path = scene.render.filepath + "_normal"
    albedoFileOutput.file_slots[0].path = scene.render.filepath + "_albedo"

    bpy.ops.render.render(write_still=True) # render still

    b_empty.rotation_euler[2] += radians(stepsize)
    xmin, xmax, ymin, ymax, zmin, zmax = get_bbox_world()
    with open(scene.render.filepath + "_coord.txt", 'w') as filep:
        x2d, y2d = get_pixel_coord(Vector((xmin, ymin, zmin)))
        filep.write('%f %f %f %f %f\n' % (xmin, ymin, zmin, x2d, y2d))
        x2d, y2d = get_pixel_coord(Vector((xmin, ymin, zmax)))
        filep.write('%f %f %f %f %f\n' % (xmin, ymin, zmax, x2d, y2d))
        x2d, y2d = get_pixel_coord(Vector((xmin, ymax, zmax)))
        filep.write('%f %f %f %f %f\n' % (xmin, ymax, zmax, x2d, y2d))
        x2d, y2d = get_pixel_coord(Vector((xmin, ymax, zmin)))
        filep.write('%f %f %f %f %f\n' % (xmin, ymax, zmin, x2d, y2d))
        x2d, y2d = get_pixel_coord(Vector((xmax, ymin, zmin)))
        filep.write('%f %f %f %f %f\n' % (xmax, ymin, zmin, x2d, y2d))
        x2d, y2d = get_pixel_coord(Vector((xmax, ymin, zmax)))
        filep.write('%f %f %f %f %f\n' % (xmax, ymin, zmax, x2d, y2d))
        x2d, y2d = get_pixel_coord(Vector((xmax, ymax, zmax)))
        filep.write('%f %f %f %f %f\n' % (xmax, ymax, zmax, x2d, y2d))
        x2d, y2d = get_pixel_coord(Vector((xmax, ymax, zmin)))
        filep.write('%f %f %f %f %f\n' % (xmax, ymax, zmin, x2d, y2d))