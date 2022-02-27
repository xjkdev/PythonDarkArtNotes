# 使用Pybind11

## 编译系统
### CMake
```
add_subdirectory(pybind11)
pybind11_add_module(cmake_example src/main.cpp)
```

### Setuptools
```python
from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup

ext_modules = [
    Pybind11Extension("python_example",
        ["src/main.cpp"],
        # Example: passing in the version to the compiled code
        define_macros = [('VERSION_INFO', __version__)],
        ),
]

setup(
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    python_requires=">=3.6",
)
```
## 函数



## Classes

# 成员变量（字段）
```cpp
py::class_<Pet>(m, "Pet")
    .def(py::init<>())
    .def_readwrite("name", &Pet::name);
```

# 构造函数
```cpp
py::class_<Foo>(m, "Foo")
    .def(py::init<>())          // 空构造函数
    .def(py::init<Args...>())   // 其他已知的构造函数重载
    .def(py::init(Function))    // 自定义构造函数
```

> pybind11::init<> internally uses C++11 brace initialization to call the constructor of the target class. This means that it can be used to bind implicit constructors as well.
>
> Note that brace initialization preferentially invokes constructor overloads taking a std::initializer_list. In the rare event that this causes an issue, you can work around it by using py::init(...) with a lambda function that constructs the new object as desired.

# 函数重载
```cpp
py::class_<Pet>(m, "Pet")
   .def(py::init<const std::string &, int>())
   .def("set", static_cast<void (Pet::*)(int)>(&Pet::set), "Set the pet's age")
   .def("set", static_cast<void (Pet::*)(const std::string &)>(&Pet::set), "Set the pet's name");
```

If you have a C++14 compatible compiler 2, you can use an alternative syntax to cast the overloaded function:

```cpp
py::class_<Pet>(m, "Pet")
    .def("set", py::overload_cast<int>(&Pet::set), "Set the pet's age")
    .def("set", py::overload_cast<const std::string &>(&Pet::set), "Set the pet's name");
```


## Numpy

Methods of `py::array_t`:


- `.ndim()` returns the number of dimensions
- `.data(1, 2, ...)` and `r.mutable_data(1, 2, ...)` returns a pointer to the const T or T data, respectively, at the given indices. The latter is only available to proxies obtained via a.mutable_unchecked().
- `.itemsize()` returns the size of an item in bytes, i.e. sizeof(T).
- `.ndim()` returns the number of dimensions.
- `.shape(n)` returns the size of dimension n
- `.size()` returns the total number of elements (i.e. the product of the shapes).
- `.nbytes()` returns the number of bytes used by the referenced elements (i.e. itemsize() times size()).

- `.request()` returns `buffer_info` of array
- `.unchecked<n>()` and `.mutable_unchecked<n>()` returns direct access proxy of dimension n. Use `Proxy(i, j, k, ...)` to access data[i,j,k,...].

Example codes:
```cpp

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

namespace py = pybind11;

// Use pointer from buffer_info.

py::array_t<double> add_arrays(py::array_t<double> input1, py::array_t<double> input2) {
    py::buffer_info buf1 = input1.request(), buf2 = input2.request();

    if (buf1.ndim != 1 || buf2.ndim != 1)
        throw std::runtime_error("Number of dimensions must be one");

    if (buf1.size != buf2.size)
        throw std::runtime_error("Input shapes must match");

    /* No pointer is passed, so NumPy will allocate the buffer */
    auto result = py::array_t<double>(buf1.size);

    py::buffer_info buf3 = result.request();


    double *ptr1 = static_cast<double *>(buf1.ptr);
    double *ptr2 = static_cast<double *>(buf2.ptr);
    double *ptr3 = static_cast<double *>(buf3.ptr);

    for (size_t idx = 0; idx < buf1.shape[0]; idx++)
        ptr3[idx] = ptr1[idx] + ptr2[idx];

    return result;
}

// Direct Access

m.def("sum_3d", [](py::array_t<double> x) {
    auto r = x.unchecked<3>(); // x must have ndim = 3; can be non-writeable
    double sum = 0;
    for (py::ssize_t i = 0; i < r.shape(0); i++)
        for (py::ssize_t j = 0; j < r.shape(1); j++)
            for (py::ssize_t k = 0; k < r.shape(2); k++)
                sum += r(i, j, k);
    return sum;
});
m.def("increment_3d", [](py::array_t<double> x) {
    auto r = x.mutable_unchecked<3>(); // Will throw if ndim != 3 or flags.writeable is false
    for (py::ssize_t i = 0; i < r.shape(0); i++)
        for (py::ssize_t j = 0; j < r.shape(1); j++)
            for (py::ssize_t k = 0; k < r.shape(2); k++)
                r(i, j, k) += 1.0;
}, py::arg().noconvert());
```

buffer_info Definination:
```cpp
struct buffer_info {
    void *ptr;
    py::ssize_t itemsize;
    std::string format;
    py::ssize_t ndim;
    std::vector<py::ssize_t> shape;
    std::vector<py::ssize_t> strides;
};
```

## 已知问题
### CMake PCL造成未定义符号`__Py_ZeroStruct`
原因：CMake中使用`find_package(PCL)`会引入vtk的python2.7链接路径，造成问题。

解决方法：不要使用`find_package(PCL)`来引入PCL。用以下代替：
```CMake
find_package(Eigen3 REQUIRED) # Eigen3 is required
include_directories(${EIGEN3_INCLUDE_DIRECTORIES})

include_directories(/usr/include/pcl-1.8)
link_directories(/usr/lib/x86_64-linux-gnu)
pybindll_add_module(example example.cpp)
target_link_libraries(example PUBLIC pcl_io) # PCL Libraries
```
