from typing import Type, TypeVar, Callable, Any

T = TypeVar("T")

def lazy_proxy(factory_fn: Callable[[], T], base_class: Type[T]) -> T:
    """
    创建一个延迟初始化的代理对象，其类型表现为 base_class。
    用于替代 psyche/__init__.py 等地重复的 Proxy 样板代码。
    """

    class Proxy(base_class):
        def __init__(self):
            # 覆盖父类 __init__，防止在代理创建时触发原类的初始化逻辑（如文件 IO）
            pass

        def _get_instance(self) -> T:
            return factory_fn()

        def __getattribute__(self, name: str) -> Any:
            if name in ("__class__", "__instancecheck__", "__subclasscheck__", "_get_instance"):
                return super().__getattribute__(name)
            return getattr(self._get_instance(), name)

        def __setattr__(self, name: str, value: Any) -> None:
            if name == "_get_instance":
                super().__setattr__(name, value)
            else:
                setattr(self._get_instance(), name, value)

        def __call__(self, *args, **kwargs):
            return self._get_instance()(*args, **kwargs)

        def __getitem__(self, key):
            return self._get_instance()[key]

        def __setitem__(self, key, value):
            self._get_instance()[key] = value

        def __iter__(self):
            return iter(self._get_instance())

        def __len__(self):
            return len(self._get_instance())

        def __repr__(self):
            return repr(self._get_instance())

        def __str__(self):
            return str(self._get_instance())

        def __bool__(self):
            return bool(self._get_instance())

    return Proxy()
