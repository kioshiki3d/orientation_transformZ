import bpy
from bpy.types import Panel, Operator
from bpy.props import (
    PointerProperty,
    EnumProperty,
    StringProperty,
    IntProperty,
    FloatVectorProperty
    )
import bmesh
from mathutils import Matrix, Vector


bl_info = {
    "name": "orientation transform Z",
    "author": "Kageji",
    "version": (0, 0, 1),
    "blender": (4, 2, 0),
    "location": "3D View > Sidebar",
    "description": "orientation transform Z",
    "warning": "",
    "support": "COMMUNITY",
    "wiki_url": "https://github.com/kioshiki3d/orientation_transformZ/",
    "tracker_url": "https://twitter.com/shadow003min",
    "category": "Object",
}
CUSTOM_NAME = "Custom Orientation"


class KJ_CTZ_Panel(Panel):
    bl_label = "orientation transform Z"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "kjtools"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        # よく使うボタン
        layout.label(text="orientation transform")
        layout.operator(KJ_SetDefaultOrientation.bl_idname, text="Global").slot = 1
        layout.operator(KJ_SetDefaultOrientation.bl_idname, text="Local").slot = 2
        # カスタム作成
        layout.label(text="original orientation transform")
        custom_bottun = layout.row(align=True)
        custom_bottun.enabled = self.judge_custom_button()
        custom_bottun.operator(KJ_SetCustomOrientation.bl_idname, text="Original")
        ## プルダウンメニュー
        layout.prop(scene, "kjotOption", text="mode")
        if scene.kjotOption == "object":
            layout.label(text=" select Object for orientation transform")
            layout.prop_search(scene, "kjotObjdata", bpy.data, "objects", text="", icon="OBJECT_DATA")
 
        elif scene.kjotOption == "vertex":
            if context.mode == "EDIT_MESH":
                layout.label(text=" select Vertex")
                row1 = layout.row(align=True)
                row1.label(text="vert 1")
                btn_text1 = self.set_vertex_button("kjotVertexIdx1")
                row1.operator(KJ_SetVertex.bl_idname, text=btn_text1).slot = 1

                row2 = layout.row(align=True)
                row2.label(text="vert 2")
                btn_text2 = self.set_vertex_button("kjotVertexIdx2")
                row2.operator(KJ_SetVertex.bl_idname, text=btn_text2).slot = 2

                layout.label(text="  advanced vertex vector")
                row3 = layout.row(align=True)
                row3.label(text="vert 3")
                btn_text3 = self.set_vertex_button("kjotVertexIdx3")
                row3.operator(KJ_SetVertex.bl_idname, text=btn_text3).slot = 3
            else:
                layout.label(text=" select Mesh object")

        elif scene.kjotOption == "edge":
            if context.mode == "EDIT_MESH":
                layout.label(text=" select Edge (vert1,2)")
                row = layout.row(align=True)
                row.label(text="edge")
                btn_text = self.set_vertex_button("kjotVertexIdx1", "kjotVertexIdx2")
                row.operator(KJ_SetVertex.bl_idname, text=btn_text).slot = 0

                layout.label(text="  advanced vertex vector")
                row3 = layout.row(align=True)
                row3.label(text="vert 3")
                btn_text3 = self.set_vertex_button("kjotVertexIdx3")
                row3.operator(KJ_SetVertex.bl_idname, text=btn_text3).slot = 3
            else:
                layout.label(text=" select Mesh object")

        elif scene.kjotOption == "bone":
            if context.active_object and context.active_object.type == "ARMATURE":
                layout.label(text=" select Bone object")
                layout.prop_search(scene, "kjotBonedata", context.active_object.data, "bones", text="", icon="BONE_DATA")
            else:
                layout.label(text=" select Armature Object")
        # すべて削除
        layout.operator(KJ_SetDefaultOrientation.bl_idname, text="Delete custom orientation").slot = 0

    def judge_custom_button(self):
        """Originalの有効化"""
        scene = bpy.context.scene
        active_obj = bpy.context.active_object
        ret = False
        if scene.kjotOption == "object":
            if scene.kjotObjdata:
                ret = True
        elif scene.kjotOption == "bone":
            if active_obj.type == "ARMATURE":
                if scene.kjotBonedata in active_obj.data.bones:
                    ret = True
        else: #"vertex", "edge"
            if (scene.kjotVertexIdx1 != -1) and (scene.kjotVertexIdx2 != -1) and (bpy.context.mode == "EDIT_MESH"):
                ret = True
        return ret

    def set_vertex_button(self, idxname_a, idxname_b=""):
        """頂点設定済み時のボタン表記"""
        btn_text = "Set"
        idx_a = getattr(bpy.context.scene, idxname_a)
        if idxname_b:
            idx_b = getattr(bpy.context.scene, idxname_b)
            if (idx_a != -1) and (idx_b != -1):
                btn_text = "OK"
        else:
            if idx_a != -1:
                btn_text = "OK"
        return btn_text
        

class KJ_SetDefaultOrientation(Operator):
    bl_idname = "kjsetdefaultorientation.operator"
    bl_label = "set_default_orientation"
    bl_description = "Set Default Orientation"

    slot: IntProperty(name="Default Slot", default=0, min=0, max=2)
    
    def execute(self, context):
        if self.slot == 0:
            clear_orientations() # Delete
        elif self.slot == 1:
            context.scene.transform_orientation_slots[0].type = "GLOBAL"
        elif self.slot == 2:
            context.scene.transform_orientation_slots[0].type = "LOCAL"
        return {"FINISHED"}


class KJ_SetVertex(Operator):
    bl_idname = "kjsetvertex.operator"
    bl_label = "set_vertex"
    bl_description = "Set Vertex"

    slot: IntProperty(name="Vertex Slot", default=1, min=0, max=3)

    def execute(self, context):
        scene = context.scene
        active_obj = context.active_object
        bm = bmesh.from_edit_mesh(active_obj.data)

        if self.slot == 0: # edge
            selected_edges = [e for e in bm.edges if e.select]
            if len(selected_edges) < 1:
                self.report({"ERROR"}, "Select at least one edge")
                return {"CANCELLED"}
            active_edge = None
            if bm.select_history and isinstance(bm.select_history.active, bmesh.types.BMEdge):
                active_edge = bm.select_history.active

            edge = active_edge if active_edge else selected_edges[-1]
            vert1, vert2 = edge.verts
            scene.kjotVertexIdx1 = vert1.index
            scene.kjotVertexVec1 = vert1.co.copy()
            scene.kjotVertexIdx2 = vert2.index
            scene.kjotVertexVec2 = vert2.co.copy()
            s1 = "(" + ", ".join(f"{x:.2f}" for x in vert1.co) + ")"
            s2 = "(" + ", ".join(f"{x:.2f}" for x in vert2.co) + ")"
            self.report({"INFO"}, f"edge vector {s1} - {s2}")
            return {"FINISHED"}

        active_vert = None
        if bm.select_history and isinstance(bm.select_history.active, bmesh.types.BMVert):
            active_vert = bm.select_history.active

        selected_verts = [v for v in bm.verts if v.select]
        centroid = Vector((0, 0, 0))
        for vert in selected_verts:
            centroid += vert.co
        centroid /= len(selected_verts)
        vert_index = active_vert.index if active_vert else selected_verts[0].index
        s = "(" + ", ".join(f"{x:.2f}" for x in centroid) + ")"

        if self.slot == 1:
            scene.kjotVertexIdx1 = vert_index
            scene.kjotVertexVec1 = centroid
        elif self.slot == 2:
            scene.kjotVertexIdx2 = vert_index
            scene.kjotVertexVec2 = centroid
        elif self.slot == 3:
            scene.kjotVertexIdx3 = vert_index
            scene.kjotVertexVec3 = centroid
        self.report({"INFO"}, f"vert {self.slot}: {s}")
        return {"FINISHED"}


class KJ_SetCustomOrientation(Operator):
    bl_idname = "kjsetcustomorientation.operator"
    bl_label = "set_custom_orientation"
    bl_description = "Set Custom Orientation"
    active_obj = None
    obj = None
    
    def execute(self, context):
        scene = context.scene
        obj_mode = context.mode

        # orientation objectの設定
        if obj_mode != "OBJECT":
            bpy.ops.object.mode_set(mode = "OBJECT")
        self.active_obj = context.active_object
        if scene.kjotOption == "object":
            self.obj = scene.kjotObjdata
        else:
            if scene.kjotOption == "bone":
                bone = self.active_obj.data.bones[scene.kjotBonedata]
                # ボーンのローカル座標系を取得（アーマチュアのワールド座標系を考慮）
                bone_matrix = self.active_obj.matrix_world @ bone.matrix_local
                rotation_matrix = bone_matrix.to_3x3()
                location = self.active_obj.matrix_world @ bone.head_local
            else: #"vertex", "edge"
                # Z軸: 頂点1から頂点2への方向（正規化）
                location = self.active_obj.matrix_world @ Vector(scene.kjotVertexVec1)
                v2 = self.active_obj.matrix_world @ Vector(scene.kjotVertexVec2)
                z_axis = (v2 - location).normalized()

                # Y軸: Z軸とv1_to_v3の外積（正規化）
                if scene.kjotVertexIdx3 == -1:
                    vec_tmp = Vector((0, 1, 0))
                else:
                    # 頂点1から頂点3へのベクトル
                    v3 = self.active_obj.matrix_world @ Vector(scene.kjotVertexVec3)
                    vec_tmp = v3 - location
                y_axis = z_axis.cross(vec_tmp).normalized()
                if y_axis.length < 1e-6:
                    y_axis = z_axis.cross(Vector((0, 0, 1))).normalized()

                # X軸: Y軸とZ軸の外積（直交性を確保）
                x_axis = y_axis.cross(z_axis).normalized()
                # 回転行列を作成（X, Y, Z軸を列とする）
                rotation_matrix = Matrix([x_axis, y_axis, z_axis]).transposed()  # 行ベクトルとして設定

            reset_vertex()
            # エンプティオブジェクトを作成
            bpy.ops.object.empty_add(type="ARROWS", align="WORLD", location=location)
            self.obj = context.active_object
            self.obj.name = "Empty_6B6A6164646F6E"
            # エンプティの回転をボーンのオリエンテーションに設定
            self.obj.matrix_world = Matrix.Translation(location) @ rotation_matrix.to_4x4()

        # object比較
        same_obj = (self.active_obj == self.obj)
        if not same_obj:
            context.view_layer.objects.active = self.obj
        # 同じものがある場合削除する
        clear_orientations()
        # orientation作成set
        bpy.ops.transform.create_orientation(name=CUSTOM_NAME, use=True)
        scene.transform_orientation_slots[0].type = CUSTOM_NAME

        # 元の状態に戻す
        if self.obj.name == "Empty_6B6A6164646F6E":
            bpy.data.objects.remove(self.obj, do_unlink=True)
        if not same_obj:
            context.view_layer.objects.active = self.active_obj
        if obj_mode != "OBJECT":
            if "_" in obj_mode:
                obj_mode = obj_mode[:obj_mode.find("_")]
            bpy.ops.object.mode_set(mode = obj_mode)
        return {"FINISHED"}


def clear_orientations():
    try:
        bpy.context.scene.transform_orientation_slots[0].type = CUSTOM_NAME
        bpy.ops.transform.delete_orientation()
        bpy.context.scene.transform_orientation_slots[0].type = "GLOBAL"
    except:
        pass


def reset_vertex():
    scene = bpy.context.scene
    scene.kjotVertexIdx1 = -1
    scene.kjotVertexIdx2 = -1
    scene.kjotVertexIdx3 = -1
    scene.kjotVertexVec1 = Vector((0, 0, 0))
    scene.kjotVertexVec2 = Vector((0, 0, 0))
    scene.kjotVertexVec3 = Vector((0, 0, 0))


def set_orientation_names(orient):
    return 

def set_props():
    scene = bpy.types.Scene
    scene.kjotOption = EnumProperty(
        name="select orientation object mode",
        items=[
            ("object", "object", ""),
            ("vertex", "vertex", ""),
            ("edge", "edge", ""),
            ("bone", "bone", "")
        ],
        default="object"
    )
    # scene.kjotOrientationName = StringProperty(
    #     name="orientation name",
    #     description="Orientation name",
    #     default="Custom"
    # )
    # scene.kjotOrientationNames = EnumProperty(
    #     name="cleated orientation name",
    #     items=[("Custom", "Custom", "")]
    #     default="Custom"
    # )
    scene.kjotObjdata = PointerProperty(
        name="object data",
        type=bpy.types.Object,
    )
    scene.kjotBonedata = StringProperty(
        name="bone data",
        description="Selected bone name",
        default=""
    )
    scene.kjotVertexIdx1 = IntProperty(name="vertex index 1", default=-1)
    scene.kjotVertexIdx2 = IntProperty(name="vertex index 2", default=-1)
    scene.kjotVertexIdx3 = IntProperty(name="vertex index 3", default=-1)
    scene.kjotVertexVec1 = FloatVectorProperty(name="vertex coordinate 1")
    scene.kjotVertexVec2 = FloatVectorProperty(name="vertex coordinate 2")
    scene.kjotVertexVec3 = FloatVectorProperty(name="vertex coordinate 3")


def clear_props():
    scene = bpy.types.Scene
    del scene.kjotOption
    # del scene.kjotOrientationName
    # del scene.kjotOrientationNames
    del scene.kjotObjdata
    del scene.kjotBonedata
    del scene.kjotVertexIdx1
    del scene.kjotVertexIdx2
    del scene.kjotVertexIdx3
    del scene.kjotVertexVec1
    del scene.kjotVertexVec2
    del scene.kjotVertexVec3


classes = (
    KJ_CTZ_Panel,
    KJ_SetDefaultOrientation,
    KJ_SetCustomOrientation,
    KJ_SetVertex,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    set_props()


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    clear_props()
    clear_orientations()


if __name__ == "__main__":
    register()
