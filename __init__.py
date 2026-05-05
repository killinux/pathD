bl_info = {
    "name": "PMX Expression Builder",
    "author": "pathd addon",
    "version": (0, 1, 0),
    "blender": (3, 6, 0),
    "location": "View3D > N-Panel > PMX 表情",
    "description": "Batch add / edit facial expressions (vertex morphs) on PMX models imported via mmd_tools.",
    "category": "Object",
    "warning": "Requires the mmd_tools addon to be installed and enabled.",
}

from . import properties, operators, ui


_modules = (properties, operators, ui)


def register():
    for m in _modules:
        m.register()


def unregister():
    for m in reversed(_modules):
        m.unregister()


if __name__ == "__main__":
    register()
