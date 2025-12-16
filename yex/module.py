import types

# Cast ourselves to a subtype. This means we can call yex().
# See https://stackoverflow.com/questions/1060796/callable-modules .
class YexModule(types.ModuleType):
    def __call__(self, *args, **kwargs):
        import yex.put # avoid circular dependency

        return yex.put.put(*args, **kwargs)

def make_module_into_yexmodule(name):
    import sys
    sys.modules[name].__class__ = YexModule

__all__ = ['YexModule', 'make_module_into_yexmodule']
