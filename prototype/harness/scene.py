import bpy, json, sys, math
from pathlib import Path

def main():
    argv=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    task_file, output_dir, submission = map(Path, argv[:3])
    task=json.loads(task_file.read_text())
    output_dir.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        if task.get('setup'):
            import importlib.util
            setup_path = Path(__file__).resolve().with_name("setup.py")
            spec = importlib.util.spec_from_file_location("blender_experiments_setup", setup_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            module.build(task["setup"])
        bpy.context.view_layer.update()
        def snapshot():
            return {o.name:{'type':o.type,'location':list(o.matrix_world.translation),'dimensions':list(o.dimensions),
                    'mesh_vertices':[list(o.matrix_world @ v.co) for v in o.data.vertices] if o.type=='MESH' else []}
                    for o in bpy.context.scene.objects if o.type in {'MESH','CURVE','EMPTY'}}
        initial=snapshot()
        exec(compile(submission.read_text(),str(submission),"exec"),{"__name__":"__main__","bpy":bpy})
        bpy.context.view_layer.update()
        objects=[]
        for obj in bpy.context.scene.objects:
            if obj.type not in {"MESH","CURVE","EMPTY"}: continue
            record={"name":obj.name,"type":obj.type,"location":list(obj.matrix_world.translation),"dimensions":list(obj.dimensions),"rotation":list(obj.rotation_euler),"vertices":len(obj.data.vertices) if obj.type=="MESH" else None}
            if obj.type=="MESH":
                record["faces"]=len(obj.data.polygons)
                obj.data.calc_loop_triangles()
                record["triangles"]=[list(t.vertices) for t in obj.data.loop_triangles]
                record["mesh_vertices"]=[list(obj.matrix_world @ v.co) for v in obj.data.vertices]
            elif obj.type=="CURVE":
                record["curve_points"]=[list(obj.matrix_world @ p.co.xyz) for spline in obj.data.splines for p in spline.points]
            objects.append(record)
        (output_dir/"scene.json").write_text(json.dumps({"objects":objects,"initial":initial},indent=2))
        coords=[obj.matrix_world.translation for obj in bpy.context.scene.objects if obj.type in {'MESH','CURVE'}]
        from mathutils import Vector
        target=sum(coords,Vector((0,0,0)))/len(coords) if coords else Vector((0,0,0))
        if bpy.context.scene.camera is None:
            bpy.ops.object.camera_add(location=(8,-10,8))
            camera=bpy.context.object
            direction=target-camera.location
            camera.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
            bpy.context.scene.camera=camera
        scene=bpy.context.scene
        scene.render.engine='BLENDER_WORKBENCH'
        scene.render.resolution_x=384
        scene.render.resolution_y=384
        scene.render.resolution_percentage=100
        scene.render.image_settings.file_format='PNG'
        scene.render.filepath=str((output_dir/'render.png').resolve())
        bpy.ops.wm.save_as_mainfile(filepath=str((output_dir/'scene.blend').resolve()))
        bpy.ops.render.render(write_still=True)
    except Exception as exc:
        import traceback
        (output_dir/'error.txt').write_text(traceback.format_exc())
        raise

if __name__=='__main__': main()
