import bpy
from bpy.types import Operator
from bpy.props import StringProperty

from . import morph_utils, presets as _presets


def _resolve(self, context):
    """找 mmd_root + main mesh，失败时 self.report 并返回 (None, None)。"""
    root = morph_utils.find_mmd_root(context)
    if root is None:
        self.report({'ERROR'}, "未找到 MMD 模型（请先选中模型内任一对象）")
        return None, None
    mesh = morph_utils.find_main_mesh(root)
    if mesh is None:
        self.report({'ERROR'}, f"模型 '{root.name}' 下无 mesh")
        return None, None
    return root, mesh


class PMXEXP_OT_detect(Operator):
    bl_idname = "pmxexp.detect"
    bl_label = "检测 MMD 模型"
    bl_description = "扫描 mmd_root 与目标 mesh，显示当前已注册表情数"
    bl_options = {'REGISTER'}

    def execute(self, context):
        s = context.scene.pmxexp
        root, mesh = _resolve(self, context)
        if root is None:
            s.last_status = "未检测到 MMD 模型"
            return {'CANCELLED'}
        n_morph = len(root.mmd_root.vertex_morphs)
        n_sk = 0
        if mesh.data.shape_keys:
            n_sk = len(mesh.data.shape_keys.key_blocks)
        s.last_status = f"root='{root.name}' mesh='{mesh.name}' morphs={n_morph} shape_keys={n_sk}"
        self.report({'INFO'}, s.last_status)
        return {'FINISHED'}


class PMXEXP_OT_add_single(Operator):
    bl_idname = "pmxexp.add_single"
    bl_label = "添加单个表情"
    bl_description = "用上方表单 (中文名/英文名/分类) 添加一个空表情"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        s = context.scene.pmxexp
        root, mesh = _resolve(self, context)
        if root is None:
            return {'CANCELLED'}
        if not s.new_name:
            self.report({'ERROR'}, "中文名不能为空")
            return {'CANCELLED'}
        status, info = morph_utils.add_vertex_morph(
            root, mesh,
            s.new_name, s.new_name_e, s.new_category,
            skip_existing=s.skip_existing,
        )
        s.last_status = f"{status}: {info}"
        if status == 'error':
            self.report({'ERROR'}, info)
            return {'CANCELLED'}
        self.report({'INFO'}, s.last_status)
        return {'FINISHED'}


class PMXEXP_OT_add_preset_set(Operator):
    bl_idname = "pmxexp.add_preset_set"
    bl_label = "应用预设套装"
    bl_description = "批量添加预设套装中的全部表情"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        s = context.scene.pmxexp
        root, mesh = _resolve(self, context)
        if root is None:
            return {'CANCELLED'}
        kit = _presets.PRESETS.get(s.preset)
        if kit is None:
            self.report({'ERROR'}, f"未知预设 {s.preset}")
            return {'CANCELLED'}
        added = 0
        skipped = 0
        for name, name_e, cat in kit["items"]:
            status, _ = morph_utils.add_vertex_morph(
                root, mesh, name, name_e, cat,
                skip_existing=s.skip_existing,
            )
            if status == 'added':
                added += 1
            elif status == 'skipped':
                skipped += 1
        s.last_status = f"套装 '{s.preset}': 新增 {added} 跳过 {skipped} (mesh='{mesh.name}')"
        self.report({'INFO'}, s.last_status)
        return {'FINISHED'}


class PMXEXP_OT_remove(Operator):
    bl_idname = "pmxexp.remove"
    bl_label = "删除表情"
    bl_description = "按当前 active morph 删除（同时删除对应 shape key）"
    bl_options = {'REGISTER', 'UNDO'}

    target: StringProperty(name="表情名", default="")

    def execute(self, context):
        s = context.scene.pmxexp
        root, mesh = _resolve(self, context)
        if root is None:
            return {'CANCELLED'}
        name = self.target
        if not name:
            idx = root.mmd_root.active_morph
            morphs = root.mmd_root.vertex_morphs
            if 0 <= idx < len(morphs):
                name = morphs[idx].name
        if not name:
            self.report({'ERROR'}, "无 active 表情可删除")
            return {'CANCELLED'}
        ok = morph_utils.remove_vertex_morph(root, mesh, name)
        s.last_status = f"删除 '{name}': {'成功' if ok else '未找到'}"
        self.report({'INFO'}, s.last_status)
        return {'FINISHED'}


class PMXEXP_OT_rebind(Operator):
    bl_idname = "pmxexp.rebind"
    bl_label = "补登记孤立 shape key"
    bl_description = "扫描 mesh 上手工建的 shape key, 按 OTHER 分类补登记到 mmd_root"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        s = context.scene.pmxexp
        root, mesh = _resolve(self, context)
        if root is None:
            return {'CANCELLED'}
        n = morph_utils.rebind_orphan_shape_keys(root, mesh)
        s.last_status = f"补登记 {n} 个孤立 shape key"
        self.report({'INFO'}, s.last_status)
        return {'FINISHED'}


_classes = (
    PMXEXP_OT_detect,
    PMXEXP_OT_add_single,
    PMXEXP_OT_add_preset_set,
    PMXEXP_OT_remove,
    PMXEXP_OT_rebind,
)


def register():
    for c in _classes:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(_classes):
        bpy.utils.unregister_class(c)
