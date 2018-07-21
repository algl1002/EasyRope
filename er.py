bl_info = {
    "name": "Easy Rope",
    "author": "Alexander Cortez",
    "version": (0, 8),
    "blender": (2, 79, 0),
    "location": "Tools",
    "description": "Create ropes easily!",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Tools"
}

import bpy
import bmesh
from bpy.types import PropertyGroup
from bpy.props import (PointerProperty, IntProperty, 
                       FloatProperty, EnumProperty,
                       BoolProperty)


class Props(bpy.types.PropertyGroup):
    d = {}
    
    points = []
    rope = None
    resolution = IntProperty(name="Resolution", 
                             default=7, 
                             min=1, max=50)
    stiffness = FloatProperty(name="Stiffness", 
                              default=0.1, 
                              min=0.01, max=1,
                              precision=3)
    as_shape = BoolProperty(name="Apply as shape key", default=False)
    modes = [("Static", "Static", "", "", 1), ("Dynamic", "Dynamic", "", "", 2)]
    mode = EnumProperty(items=modes)


class EasyRopeAddPoint(bpy.types.Operator):
    bl_idname = "object.easyrope_add_point"
    bl_label = "Easy Rope Add Point"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.easyrope
        cursor = context.scene.cursor_location
        bpy.ops.object.empty_add(type='PLAIN_AXES', radius=1, location=cursor)
        p = context.scene.objects.active
        props.points.append(p)
        return {'FINISHED'}


class EasyRope(bpy.types.Operator):
    bl_idname = "object.easyrope"
    bl_label = "Easy Rope"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.easyrope
        if len(props.points) >= 2:
            verts = [c.location for c in props.points]
            edges = [(i, i+1) for i in range(len(verts)-1)]
            mesh = bpy.data.meshes.new("mesh")
            mesh.from_pydata(verts, edges, [])
            mesh.validate()
            mesh.update()
            obj = bpy.data.objects.new("Rope", mesh)
            context.scene.objects.link(obj)
            for o in context.selected_objects:
                o.select = False
            context.scene.objects.active = obj
            
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='TOGGLE')
            bpy.ops.object.editmode_toggle()
            
            for o in props.points:
                o.select = True
                bpy.ops.object.delete(use_global=False)
                
            bpy.ops.object.mode_set(mode = 'EDIT')
            bm = bmesh.from_edit_mesh(obj.data)
            for i in range(len(bm.verts)):
                bpy.context.scene.objects.active = obj
                bpy.ops.mesh.select_all(action = 'DESELECT')
                bm = bmesh.from_edit_mesh(obj.data)
                bm.verts.ensure_lookup_table()
                v  = bm.verts[i]
                v.select = True
                bm.select_flush( True )
                bpy.ops.object.hook_add_newob()
            for i in obj.data.edges:
                i.select = True
                bpy.ops.mesh.subdivide(number_cuts=props.resolution)
                i.select = False
            bpy.ops.object.mode_set(mode = 'OBJECT')
            bpy.ops.object.mode_set(mode = 'EDIT')
            bpy.ops.mesh.select_all(action = 'SELECT')
            bpy.ops.mesh.subdivide(number_cuts=props.resolution)
            bpy.ops.object.mode_set(mode = 'OBJECT')
            bpy.ops.object.modifier_add(type='SOFT_BODY')
            pin_group = obj.vertex_groups.new("EasyRope_Pin")
            pin_group.add([i for i in range(len(props.points))], 1, "ADD")
            obj.modifiers["Softbody"].settings.vertex_group_goal = pin_group.name
            obj.modifiers["Softbody"].settings.goal_default = 1
            obj.modifiers["Softbody"].settings.goal_min = props.stiffness/2
            obj.modifiers["Softbody"].settings.goal_spring = 0.5
            obj.modifiers["Softbody"].settings.speed = 50
            if props.mode == 'Static':
                a = bpy.context.scene.frame_end
                bpy.context.scene.frame_end = 100
                override = {'scene': bpy.context.scene, 
                            'point_cache': obj.modifiers["Softbody"].point_cache}
                bpy.ops.ptcache.bake(override, bake=True)
                bpy.context.scene.frame_current = 99
                bpy.context.scene.objects.active = obj
                obj.select = True
                if not props.as_shape:
                    bpy.ops.object.convert(target='MESH')
                else:
                    bpy.ops.object.modifier_apply(apply_as='SHAPE', 
                                                  modifier="Softbody")
                    bpy.ops.object.convert(target='MESH')
                bpy.context.scene.frame_end = a
                bpy.context.scene.frame_current = 0

            props.points.clear()
        else:
            self.report({'WARNING'}, "You have to add at least 2 points!")
        return {'FINISHED'}
    
    
class Panel(bpy.types.Panel):
    bl_label = "Easy Rope"
    bl_region_type = 'TOOLS'
    bl_space_type = 'VIEW_3D'
    bl_category = 'Tools'
    
    def draw(self, context):
        props = context.scene.easyrope
        
        lay = self.layout.box()
        col = lay.split().column(align=True)
        col.operator("object.easyrope_add_point", "Add point")
        col.separator()
        row = col.row()
        row.prop(props, "resolution")
        col.separator()
        row = col.row()
        row.prop(props, "stiffness")
        col.separator()
        if props.mode == 'Static':
            row = col.row()
            row.prop(props, "as_shape")
            col.separator()
        row = col.row()
        row.prop(props, "mode", "radio", expand=True)
        col.separator()
        col.operator("object.easyrope", "Generate!")
        
def register():
    bpy.utils.register_class(Props)
    bpy.utils.register_class(EasyRope)
    bpy.utils.register_class(EasyRopeAddPoint)
    bpy.utils.register_class(Panel)
    bpy.types.Scene.easyrope = PointerProperty(type=Props)

def unregister():
    bpy.utils.unregister_class(Props)
    bpy.utils.unregister_class(EasyRope)
    bpy.utils.unregister_class(EasyRopeAddPoint)
    bpy.utils.unregister_class(Panel)
    del bpy.types.Scene.easyrope

if __name__ == "__main__":
    register()