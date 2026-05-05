import bpy
from bpy.props import StringProperty, EnumProperty, BoolProperty, PointerProperty

from . import presets as _presets


def _preset_items(self, context):
    return [(k, k, v["desc"]) for k, v in _presets.PRESETS.items()]


_CATEGORY_ITEMS = [
    ('SYSTEM', "系统 / System", ""),
    ('EYEBROW', "眉 / Eyebrow", ""),
    ('EYE', "目 / Eye", ""),
    ('MOUTH', "口 / Mouth", ""),
    ('OTHER', "他 / Other", ""),
]


class PMXEXP_Settings(bpy.types.PropertyGroup):
    preset: EnumProperty(
        name="预设套装",
        description="批量添加的表情套装",
        items=_preset_items,
    )

    new_name: StringProperty(
        name="名称（中）",
        description="MMD 表情名（中文/日文）",
        default="",
    )
    new_name_e: StringProperty(
        name="名称（英）",
        description="MMD 表情名（英文）",
        default="",
    )
    new_category: EnumProperty(
        name="分类",
        items=_CATEGORY_ITEMS,
        default='OTHER',
    )

    skip_existing: BoolProperty(
        name="跳过已存在",
        description="如果同名表情或 shape key 已存在则跳过，不报错",
        default=True,
    )

    last_status: StringProperty(default="")


def register():
    bpy.utils.register_class(PMXEXP_Settings)
    bpy.types.Scene.pmxexp = PointerProperty(type=PMXEXP_Settings)


def unregister():
    del bpy.types.Scene.pmxexp
    bpy.utils.unregister_class(PMXEXP_Settings)
