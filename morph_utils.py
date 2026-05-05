"""与 mmd_tools 交互的薄封装。

不重新发明数据模型——shape key 走 Blender 原生 API，morph 元数据走
mmd_root.vertex_morphs 集合。两者必须配对，否则 PMX 导出会丢东西。
"""
import bpy


def find_mmd_root(obj_or_context):
    """沿父级查找 mmd_type=='ROOT' 的 empty。接受 Object 或 Context。"""
    if hasattr(obj_or_context, "scene"):  # Context
        obj = obj_or_context.active_object
    else:
        obj = obj_or_context
    while obj is not None:
        if getattr(obj, "mmd_type", None) == 'ROOT':
            return obj
        obj = obj.parent
    # 退路：扫场景，取第一个 ROOT
    for o in bpy.data.objects:
        if getattr(o, "mmd_type", None) == 'ROOT':
            return o
    return None


def iter_meshes(root):
    """递归遍历 root 子树下所有 mesh。"""
    stack = list(root.children)
    while stack:
        o = stack.pop()
        stack.extend(o.children)
        if o.type == 'MESH':
            yield o


def find_main_mesh(root):
    """选最适合挂表情的 mesh：优先已有 shape key 的，否则取顶点最多的。"""
    meshes = list(iter_meshes(root))
    if not meshes:
        return None
    with_keys = [m for m in meshes if m.data.shape_keys]
    if with_keys:
        return max(with_keys, key=lambda m: len(m.data.shape_keys.key_blocks))
    return max(meshes, key=lambda m: len(m.data.vertices))


def ensure_basis_shape_key(mesh):
    """保证 mesh 有 Basis 形态键（mmd_tools/PMX 的零位形）。"""
    if mesh.data.shape_keys is None:
        mesh.shape_key_add(name="Basis", from_mix=False)
    elif "Basis" not in mesh.data.shape_keys.key_blocks:
        # 罕见：mesh 有 shape_keys 但无 Basis（reference key 名字被改）。
        # 直接补一个不会冲突。
        mesh.shape_key_add(name="Basis", from_mix=False)


def add_vertex_morph(root, mesh, name, name_e, category, skip_existing=True):
    """新增一个空顶点 morph：创建同名 shape key + 注册到 mmd_root.vertex_morphs。

    返回 ('added' | 'skipped' | 'error', 详情文本)。
    """
    if not name:
        return 'error', "name 为空"

    ensure_basis_shape_key(mesh)
    keys = mesh.data.shape_keys.key_blocks
    morphs = root.mmd_root.vertex_morphs

    sk_exists = name in keys
    mr_exists = any(m.name == name for m in morphs)

    if sk_exists and mr_exists:
        if skip_existing:
            return 'skipped', f"{name} 已存在（shape key + morph）"
        return 'error', f"{name} 已存在"

    # shape key
    if not sk_exists:
        sk = mesh.shape_key_add(name=name, from_mix=False)
        sk.value = 0.0

    # mmd 注册
    if not mr_exists:
        m = morphs.add()
        m.name = name
        try:
            m.name_e = name_e or ""
        except AttributeError:
            pass
        try:
            m.category = category
        except (AttributeError, TypeError):
            pass

    return 'added', name


def remove_vertex_morph(root, mesh, name):
    """删除 morph 元数据并删除对应 shape key（如果有）。"""
    morphs = root.mmd_root.vertex_morphs
    removed = False
    for i, m in enumerate(morphs):
        if m.name == name:
            morphs.remove(i)
            removed = True
            break

    if mesh and mesh.data.shape_keys and name in mesh.data.shape_keys.key_blocks:
        sk = mesh.data.shape_keys.key_blocks[name]
        mesh.shape_key_remove(sk)
        removed = True

    return removed


def rebind_orphan_shape_keys(root, mesh):
    """扫描 mesh 上未注册的 shape key，按 OTHER 分类补登记到 mmd_root."""
    if mesh.data.shape_keys is None:
        return 0
    morphs = root.mmd_root.vertex_morphs
    registered = {m.name for m in morphs}
    added = 0
    for sk in mesh.data.shape_keys.key_blocks:
        if sk.name == "Basis" or sk.name in registered:
            continue
        m = morphs.add()
        m.name = sk.name
        try:
            m.category = 'OTHER'
        except (AttributeError, TypeError):
            pass
        added += 1
    return added
