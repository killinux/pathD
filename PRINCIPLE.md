# pathd 实现原理

## 一、问题域：PMX 表情在 Blender 中的存储

PMX 模型的"表情"（morph，俗称面部表情/モーフ）在 Blender 内**不是单一对象**，而是横跨两层数据：

### 1. Blender 原生层 —— Shape Key

每个 mesh 的 `bpy.data.meshes[X].shape_keys.key_blocks` 是一个集合：

```
Basis             ← 零位形（参考形态，所有顶点的原始位置）
笑い              ← 形变形（每个顶点的偏移向量）
あ
まばたき
...
```

`key_blocks[name].data[i].co` 存放第 i 个顶点在该形态下的目标坐标。播放表情就是 `value` 滑块从 0→1 在 Basis 与目标之间插值。**这是 Blender 引擎认识的、能渲染、能动画的部分。**

### 2. mmd_tools 元数据层 —— mmd_root.vertex_morphs

mmd_tools 在导入 PMX 时，在 `bpy.types.Object` 上挂了一个自定义的 PropertyGroup `mmd_root`。其中：

```
root.mmd_root.vertex_morphs    ← 顶点表情元数据集合
            .bone_morphs       ← 骨骼表情
            .material_morphs   ← 材质表情
            .uv_morphs         ← UV 表情
            .group_morphs      ← 组合表情
```

每条 `vertex_morphs[i]` 是一个 PropertyGroup 实例，含：

| 字段 | 类型 | 含义 |
|------|------|------|
| `name` | str | MMD 中文/日文名（如 "笑い"）|
| `name_e` | str | MMD 英文名（如 "smile"）|
| `category` | enum | `SYSTEM` / `EYEBROW` / `EYE` / `MOUTH` / `OTHER` |

**注意**：这一层**不存顶点位移数据**，它只是个登记簿。位移数据全部在 shape_keys 那边。

### 3. 两层的契约

mmd_tools 的 PMX 导出器（`mmd_tools.core.pmx.exporter`）只导出**两边都登记**的表情：
- 顶点位移从 `mesh.data.shape_keys.key_blocks[name]` 读
- 表情元数据（中/英文名、分类）从 `root.mmd_root.vertex_morphs` 读
- **按 name 匹配两边**

如果只有 shape key 没在 mmd_root 注册 → 导出 PMX 时丢失。
如果只在 mmd_root 注册没 shape key → 导出时该表情顶点偏移全为零（空表情）。

**pathd 插件存在的意义就是同步操作这两层**，避免手动维护配对。

---

## 二、pathd 的处理流程

### 添加表情 `add_vertex_morph(root, mesh, name, name_e, category)`

```
┌────────────────────────────────────────┐
│ 1. ensure_basis_shape_key(mesh)        │
│    若 mesh 无 shape_keys 数据块, 用    │
│    mesh.shape_key_add(name="Basis")    │
│    建立 reference key                  │
├────────────────────────────────────────┤
│ 2. 检查重名                             │
│    sk_exists = name in key_blocks      │
│    mr_exists = name in vertex_morphs   │
│    根据 skip_existing 决定 skip/error  │
├────────────────────────────────────────┤
│ 3. 不存在时建 shape key                 │
│    sk = mesh.shape_key_add(            │
│        name=name, from_mix=False)      │
│    sk.value = 0.0                      │
│    （from_mix=False 保证新形与 Basis    │
│      初始顶点完全一致, 无任何偏移）     │
├────────────────────────────────────────┤
│ 4. 注册 mmd 元数据                       │
│    m = root.mmd_root.vertex_morphs.add()│
│    m.name = name                        │
│    m.name_e = name_e                    │
│    m.category = category                │
└────────────────────────────────────────┘
```

`shape_key_add(from_mix=False)` 的关键：每个顶点的 co 直接拷贝 Basis 的 co，所以 `value` 滑块从 0 到 1 时**无可见变化**——这就是"空表情"的本质。后续用户进 Sculpt 模式或 Edit 模式拖顶点时，引擎记录的就是相对 Basis 的偏移。

### 删除表情 `remove_vertex_morph(root, mesh, name)`

反过来：
1. 在 `vertex_morphs` 中找到 `name == name` 的条目，`morphs.remove(i)` 移除
2. `mesh.shape_key_remove(key_blocks[name])` 删 Blender 数据块

两步任一缺失，就会回到上面"两层失配"的状态，所以必须同时做。

### 找模型 `find_mmd_root(context)`

mmd_tools 用一个 `Empty` 对象作为模型根（俗称 "model root"），打了标记 `mmd_type == 'ROOT'`：

```
Inase54 (Empty, mmd_type='ROOT')
├── Inase54_arm (Armature)
├── Inase54_mesh (Mesh) ← shape_keys 挂这里
├── rigid_bodies (Empty)
└── joints (Empty)
```

pathd 沿当前选中对象的 parent 链一路上溯找 `mmd_type == 'ROOT'`；找不到就扫描整个 `bpy.data.objects` 取第一个。这样用户可以选中模型里**任何**对象（mesh / armature / rigid body）执行 operator，都能定位到正确的根。

### 找主 mesh `find_main_mesh(root)`

一个 PMX 模型可能有多个 mesh（身体 / 衣服 / 头发），但表情通常只挂在**身体 mesh** 上。策略：

1. 递归遍历 root 子树取所有 `type == 'MESH'`
2. 优先选**已经有 shape_keys 的 mesh**（说明它原本就有表情）
3. 多个候选时，取 shape_keys 数量最多的（最像表情主载体）
4. 全无候选时退化为顶点最多的 mesh

这是个启发式策略，对 99% 的 PMX 模型有效。极端情况（衣服 mesh 也带 shape key 但身体没有）需要用户手动选定 mesh，目前未支持，留作 v0.2。

---

## 三、与 mmd_tools 的边界

pathd **完全不重新发明 mmd 的数据模型**，三个原则：

1. **读写都走官方字段**：`mmd_root.vertex_morphs` 是 mmd_tools 定义的 CollectionProperty，pathd 直接 `add()`/`remove()` 它，让 mmd_tools 自带的 UI / 导出器都看得见。

2. **Shape key 走 Blender 原生 API**：`mesh.shape_key_add` / `mesh.shape_key_remove` 是 Blender 引擎方法，所有 mmd_tools 的 morph 编辑器、Sculpt 工具、PMX 导出器都依赖它们。

3. **不绑定 mmd_tools 内部模块**：pathd 不 `from mmd_tools.core.... import ...`，只通过 Blender 暴露的 RNA 字段（`mmd_type`、`mmd_root`）交互。这样 mmd_tools 升级不容易把 pathd 打挂。

副作用：pathd 完全失效的话，已经建好的表情**仍然能被 mmd_tools 正常识别**（因为数据本身合法），不会污染模型文件。

---

## 四、远程安装链路

```
本地 pathd/                        远程 Blender (3.6.15)
  ├── __init__.py        ┐       ┌────────────────────────┐
  ├── properties.py      │       │ user_resource(SCRIPTS, │
  ├── operators.py       │ 打包  │   path='addons')/pathd │
  ├── ui.py              ├──────►│   ├── __init__.py      │
  ├── morph_utils.py     │       │   ├── ...              │
  ├── presets.py         │       │ addon_utils.enable     │
  └── README.md          ┘       └────────────────────────┘
                              │
                  install_pathd.py
                  ↓ via relay
                  ┌────────────────────┐
                  │ HTTP /command      │
                  │ Mac client polls   │
                  │ blender-mcp:9876   │
                  └────────────────────┘
```

`install_pathd.py` 把 7 个文件全部 `read_text()` 成字符串，拼成一段 Python 代码（`json.dumps` 内嵌文件内容字典），通过 `server.py` 中继和 Mac 客户端推到远程 Blender 执行。远程端：

1. 删旧的 pathd 目录（如果存在）
2. 写新文件到 user addons
3. `addon_utils.modules_refresh()` 让 Blender 重新发现
4. `addon_utils.enable('pathd', persistent=True)` 启用并写入偏好设置
5. 通过 `bl_info['version']` 回报实际加载到的版本号

`persistent=True` 保证 Blender 重启后插件依然启用。

---

## 五、为什么 v0.1 只创建空 shape key

理论上可以让插件直接生成表情顶点偏移：例如"笑い"自动让嘴角对应顶点向上 2mm。但实际**自动雕刻不可行**：

- 不同模型嘴的几何形态不同（卡通 / 写实 / Q 版）
- 顶点编号不是规范的——同样是嘴角，A 模型在 1234 号，B 模型在 5678 号
- 需要先做 **顶点分组识别**（找嘴 / 眼 / 眉的语义区域），这本身是个机器视觉级的问题

工程取舍：v0.1 只建"空插槽"，附带正确的中/英文名和分类标签。后续路线：
- 用户自己进 Sculpt 模式雕
- 从有完整表情的 PMX 模型按顶点位置近邻匹配迁移位移（v0.3 计划）
- 用预训练几何模型做语义识别后程序化生成（远期）

---

## 六、文件依赖图

```
__init__.py
  ↓ register
  ├─→ properties.py  (PMXEXP_Settings PropertyGroup)
  │     ↑ uses presets.PRESETS for EnumProperty items
  ├─→ operators.py
  │     ↓ uses morph_utils for find/add/remove
  │     ↓ uses presets for batch items
  └─→ ui.py
        ↓ reads scene.pmxexp (from properties)
        ↓ calls bpy.ops.pmxexp.* (registered by operators)
        ↓ optionally uses morph_utils.find_mmd_root for live status

morph_utils.py  ← 仅依赖 bpy（无 mmd_tools 直接 import）
presets.py      ← 纯数据，无 bpy 依赖
```

`morph_utils` 和 `presets` 完全无 Blender Operator 副作用，可以单元测试或脚本直接调用。

---

## 七、核心代码摘要

最关键的同步逻辑只有 25 行（`morph_utils.py:add_vertex_morph`）：

```python
def add_vertex_morph(root, mesh, name, name_e, category, skip_existing=True):
    ensure_basis_shape_key(mesh)
    keys = mesh.data.shape_keys.key_blocks
    morphs = root.mmd_root.vertex_morphs
    sk_exists = name in keys
    mr_exists = any(m.name == name for m in morphs)
    if sk_exists and mr_exists:
        return ('skipped', ...) if skip_existing else ('error', ...)
    if not sk_exists:
        mesh.shape_key_add(name=name, from_mix=False).value = 0.0
    if not mr_exists:
        m = morphs.add()
        m.name = name
        m.name_e = name_e or ""
        m.category = category
    return 'added', name
```

读懂这 25 行就读懂了 pathd 全部。
