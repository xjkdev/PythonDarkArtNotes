# Dataclasses 实现

## 元数据
读取annotations后，将构建dataclass的参数存至_PARAMS中，而field存至_FILEDS中。

## 获取annotations
```python
cls_annotations = cls.__dict__.get('__annotations__', {})
```

其他field
```python
# Do we have any Field members that don't also have annotations?
for name, value in cls.__dict__.items():
    if isinstance(value, Field) and not name in cls_annotations:
        raise TypeError(f'{name!r} is a field but has no type annotation')
```

## field(...)处理
在`_process_class`中，如果Field对象有默认值，将Field对象替换为real default。
This is so that normal class introspection sees a real default value, not a field.
如果没有默认值，就删除这条属性（类类型对象中）。


## 继承关系
使用`for b in cls.__mro__[-1:-:-1]: pass` 用反MRO的顺序，遍历基类，排除自身类。

## `__init__` function
实现是代码生成器，再用`exec()`生成函数。

在`_process_class`中，通过`sys.modules[cls.__module__].__dict__`提供了eval的上下文globals。 另外在特殊情况下，有的类被人为修改`cls.__module__`时，`globals = {}` .

## abstract base class
构建最后要使用，`abc.update_abstractmethods(cls)`，更新抽象基类。(Python 3.10+)
