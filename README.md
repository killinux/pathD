# PMX Expression Builder (pathd)

给 mmd_tools 已导入的 PMX 模型批量添加面部表情（顶点 morph）。

> 实现原理详见 [PRINCIPLE.md](PRINCIPLE.md)。

## 安装

### 方式 A：本地手装

1. 把整个 `pathd/` 文件夹复制到 Blender 的用户 addons 目录：
   - Windows：`%APPDATA%\Blender Foundation\Blender\3.6\scripts\addons\pathd\`
   - macOS：`~/Library/Application Support/Blender/3.6/scripts/addons/pathd/`
2. Blender → Edit → Preferences → Add-ons → 搜 "PMX Expression"，勾选启用

### 方式 B：远程推送（开发用）

本机运行中继服务器后：

```powershell
cd C:\Users\Administrator\Desktop\winwork\remote-win
python install_pathd.py
```

脚本会把本地 7 个文件打包推送到远程 Blender，写入用户 addons 目录并 `addon_utils.enable(persistent=True)`。

## 前置条件

- Blender 3.6+
- mmd_tools 已安装且启用
- 已通过 mmd_tools 导入了 PMX 模型

## 使用流程

### 1. 打开面板

3D 视口右侧 N 面板（按 `N` 键唤出）→ 切到 "**PMX 表情**" 标签。

面板结构：
```
PMX 表情 (主面板)
├── 检测 MMD 模型
├── ☑ 跳过已存在
├── 预设套装
│   ├── 套装 [STANDARD_38 ▾]
│   └── [批量添加]
├── 单个添加
│   ├── 名称（中）
│   ├── 名称（英）
│   ├── 分类
│   └── [添加]
└── 现有表情 (默认收起)
```

### 2. 选中模型

3D 视口里点一下模型的**任何**部分（mesh / armature / model root empty 都行）——pathd 会自动沿 parent 链上溯找到 `mmd_type='ROOT'` 的根。

### 3. 检测确认

点 "**检测 MMD 模型**"。状态条会显示：

```
root='Inase54' mesh='Inase54_mesh' morphs=0 shape_keys=1
```

- `root` 是 model root 的对象名
- `mesh` 是被识别为表情主载体的 mesh
- `morphs` 是当前已注册的顶点表情数量
- `shape_keys` 是 mesh 上现有的形态键数量（含 Basis）

如果显示 "未检测到 MMD 模型"，回到第 2 步重选。

### 4. 批量添加预设

下拉选套装，点 "**批量添加**"：

| 套装 | 数量 | 内容 |
|------|------|------|
| `STANDARD_38` | 38 | MMD 标准（眉×6 / 目×12 / 口×20）|
| `EMOTION_KIT` |  8 | 照れ・涙・汗・感叹号 等附加情绪 |
| `FULL` | 46 | 上述两者合并 |

执行后状态条显示：

```
套装 'STANDARD_38': 新增 38 跳过 0 (mesh='Inase54_mesh')
```

**关键**：勾选了"跳过已存在"（默认勾上），重复点不会报错，已有的同名表情自动跳过。

### 5. 单个添加（可选）

预设套装之外的自定义表情：

| 字段 | 例 |
|------|----|
| 名称（中）| `照れ` |
| 名称（英）| `blush` |
| 分类 | `他 / Other` |

点 "**添加**"。中文名是必填，英文名和分类影响导出 PMX 后在 MMD 软件里的显示。

### 6. 雕刻顶点位移

**这一步是 pathd 不做的事**。pathd 只建立带名字的"空插槽"（Shape Key 顶点位移全为零），实际表情形变需要手动塑形：

#### 在 Blender 内

1. 选中 mesh（不是 root），切到 Edit Mode 或 Sculpt Mode
2. Properties 面板 → Object Data Properties (绿三角图标) → Shape Keys
3. 点中刚加的 shape key（例如"笑い"），把 `Value` 设为 1
4. 拖顶点（Edit Mode）或用雕刻笔刷（Sculpt Mode）改变嘴角形状
5. 把 `Value` 拖回 0 验证——应该回到 Basis 形态
6. 反复直到满意

#### 从其他 PMX 借

如果手头有已完整建表情的同模型 PMX：

1. mmd_tools → File → Import → MikuMikuDance Model 把另一份 PMX 导入新场景
2. 选中新场景里的 mesh → Object → Join Shapes 工具（或第三方插件）按顶点对应关系把 shape key 数据迁移过来
3. 删除导入的辅助模型

### 7. 现有表情管理

展开"现有表情"子面板：

- **列表**：显示所有已注册的顶点 morph，点选可改变 active morph
- **删除当前** —— 把当前 active morph 从两层（mmd_root + shape_keys）一起删掉
- **补登记孤立** —— 扫描 mesh 上手动建的、未在 mmd_root 注册的 shape key，按 `OTHER` 分类批量补登记

### 8. 导出 PMX

回到 mmd_tools 标准流程：

1. 选中 model root
2. File → Export → MikuMikuDance Model
3. 选保存路径，勾上 "Vertex Morphs" 类别
4. 导出后用 PMXEditor / MMD 打开应能看到全部 38 个表情条目

## 常见问题

### Q: 检测显示 "未检测到 MMD 模型"

确认：
- 选中了模型里的对象（不是空场景）
- 该对象的 parent 链上确实有 `mmd_type='ROOT'` 的 empty（mmd_tools 导入的模型必定有）
- mmd_tools 已启用

### Q: 添加后看不到形态变化

正常。pathd 创建的是空 shape key，**顶点位移为零**。需要手动雕刻（见上方步骤 6）。

### Q: 套装里某个表情已存在但元数据不全

先用 "**删除当前**" 移除（连同它的 shape key），再 "**批量添加**" 重建。

或者保留 shape key 顶点数据，只修元数据：直接在 mmd_tools 自带的 "**Display**" → "**Morph Tools**" 面板里改 `name_e` / `category`。

### Q: 想重置当前模型的所有表情

1. 选中 mesh
2. Properties → Object Data Properties → Shape Keys → 列表右侧 ▾ → "Delete All Shapes"
3. 选中 root，N 面板 PMX 表情 → 现有表情列表里手动删 morph 元数据
4. 重新走 "批量添加" 流程

未来 v0.2 会加一键 "清空全部表情" 操作器。

### Q: 多 mesh 模型，pathd 加错了 mesh

pathd 启发式选 mesh 时优先取**已有 shape_keys 的 mesh**，再其次顶点最多的。如果误判：当前版本只能手动把目标 mesh 加上一个 dummy shape key 让它"中签"，未来 v0.2 计划加 mesh 选择器 UI。

## 命令行 / 脚本调用

绕过 UI 直接走代码：

```python
import bpy
from pathd import morph_utils

root = morph_utils.find_mmd_root(bpy.context)
mesh = morph_utils.find_main_mesh(root)

# 加单个
morph_utils.add_vertex_morph(root, mesh,
    name="自定义", name_e="custom", category="OTHER")

# 套用预设
from pathd import presets
for nm, nm_e, cat in presets.PRESETS["STANDARD_38"]["items"]:
    morph_utils.add_vertex_morph(root, mesh, nm, nm_e, cat)

# 删除
morph_utils.remove_vertex_morph(root, mesh, "自定义")
```

或通过 operator（需要 VIEW_3D context）：

```python
bpy.context.scene.pmxexp.preset = 'FULL'
bpy.context.scene.pmxexp.skip_existing = True
bpy.ops.pmxexp.add_preset_set()
```

## 版本

v0.1.0 — 首发，38 标准 + 8 情绪套装，Shape Key / mmd_root.vertex_morphs 双层同步
