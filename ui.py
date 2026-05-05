import bpy
from bpy.types import Panel


class PMXEXP_PT_main(Panel):
    bl_label = "PMX 表情"
    bl_idname = "PMXEXP_PT_main"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "PMX 表情"

    def draw(self, context):
        s = context.scene.pmxexp
        layout = self.layout

        if s.last_status:
            box = layout.box()
            for chunk in s.last_status.split(" | "):
                box.label(text=chunk)

        layout.operator("pmxexp.detect", icon="VIEWZOOM", text="检测 MMD 模型")
        layout.prop(s, "skip_existing")


class PMXEXP_PT_preset(Panel):
    bl_label = "预设套装"
    bl_idname = "PMXEXP_PT_preset"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "PMX 表情"
    bl_parent_id = "PMXEXP_PT_main"

    def draw(self, context):
        s = context.scene.pmxexp
        layout = self.layout

        layout.prop(s, "preset", text="套装")
        layout.operator("pmxexp.add_preset_set", icon="ADD", text="批量添加")


class PMXEXP_PT_single(Panel):
    bl_label = "单个添加"
    bl_idname = "PMXEXP_PT_single"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "PMX 表情"
    bl_parent_id = "PMXEXP_PT_main"

    def draw(self, context):
        s = context.scene.pmxexp
        layout = self.layout

        col = layout.column(align=True)
        col.prop(s, "new_name")
        col.prop(s, "new_name_e")
        col.prop(s, "new_category")
        layout.operator("pmxexp.add_single", icon="PLUS", text="添加")


class PMXEXP_PT_list(Panel):
    bl_label = "现有表情"
    bl_idname = "PMXEXP_PT_list"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "PMX 表情"
    bl_parent_id = "PMXEXP_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        from . import morph_utils
        layout = self.layout
        root = morph_utils.find_mmd_root(context)
        if root is None:
            layout.label(text="未检测到 MMD 模型", icon='ERROR')
            return

        morphs = root.mmd_root.vertex_morphs
        layout.label(text=f"共 {len(morphs)} 个顶点表情")
        layout.template_list(
            "MMD_TOOLS_UL_VertexMorphs" if hasattr(bpy.types, "MMD_TOOLS_UL_VertexMorphs") else "UI_UL_list",
            "pmxexp_morphs",
            root.mmd_root, "vertex_morphs",
            root.mmd_root, "active_morph",
            rows=8,
        )
        row = layout.row(align=True)
        row.operator("pmxexp.remove", icon="X", text="删除当前")
        row.operator("pmxexp.rebind", icon="FILE_REFRESH", text="补登记孤立")


_classes = (
    PMXEXP_PT_main,
    PMXEXP_PT_preset,
    PMXEXP_PT_single,
    PMXEXP_PT_list,
)


def register():
    for c in _classes:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(_classes):
        bpy.utils.unregister_class(c)
