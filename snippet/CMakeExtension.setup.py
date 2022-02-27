import os
import re
import sys
import pathlib
import subprocess
from typing import Dict, List

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import pybind11

# Convert distutils Windows platform specifiers to CMake -A arguments
PLAT_TO_CMAKE = {
    "win32": "Win32",
    "win-amd64": "x64",
    "win-arm32": "ARM",
    "win-arm64": "ARM64",
}


class CMakeExtension(Extension):
    def __init__(self, name: str, cmake_args: Dict[str, str] = None, cmakelists_dir: str = None, target_name=None):
        """
            name: name of extension, package format.
                  for example: 'example_dir.example' will output a example extension in example_dir folder.
            cmake_args: dict of cmake arguments, equalivant to cmake command arguments '-DKey=Value'.
                  for example, assigning pybind11 path to cmake:
                      `cmake_args={'pybind11_dir': Pybind11.get_cmake_path()}`
            cmakelists_dir: parent path to CMakeLists.txt, default to package dir.
                  for example: for name='example.ext', it will default use ./example/CMakeLists.txt.
        """
        # don't invoke the original build_ext for this special extension
        super().__init__(name, sources=[])
        self.cmake_args = cmake_args or {}
        package_parts = name.split('.')
        if cmakelists_dir is None:
            self.cmakelists_dir = os.path.join('.', *package_parts[:-1])
        else:
            self.cmakelists_dir = cmakelists_dir

        if target_name is None:
            if cmakelists_dir is None:
                self.target_name = package_parts[-1]
            else:
                self.target_name = None
        else:
            self.target_name = target_name


def CMakeExtensionize(names: List[str], cmake_args: Dict[str, str] = None, cmakelists_dir: str = None) -> List[CMakeExtension]:
    """
        Accept multiple extension in one CMakeLists
    """
    return [CMakeExtension(name, cmake_args, cmakelists_dir) for name in names]


class CMakeBuild(build_ext):
    def build_extension(self, ext):
        if not isinstance(ext, CMakeExtension):
            return super().build_extension(ext)
        cmakelists_dir = pathlib.Path(ext.cmakelists_dir).absolute()
        temp_subdir = "CMakeTemp_" + "".join(x if x.isalnum() else '_' for x in ext.cmakelists_dir)
        # these dirs will be created in build_py, so if you don't have
        # any python sources to bundle, the dirs will be missing
        build_temp = pathlib.Path(self.build_temp) / temp_subdir
        build_temp.mkdir(parents=True, exist_ok=True)
        extdir = pathlib.Path(self.get_ext_fullpath(ext.name)).parent
        extdir.mkdir(parents=True, exist_ok=True)

        debug = int(os.environ.get("DEBUG", 0)) if self.debug is None else self.debug
        cfg = 'Debug' if debug else 'Release'

        # CMake lets you override the generator - we need to check this.
        # Can be set with Conda-Build, for example.
        cmake_generator = os.environ.get("CMAKE_GENERATOR", "")

        cmake_args = [
            '-DCMAKE_LIBRARY_OUTPUT_DIRECTORY={}'.format(extdir.absolute()),
            "-DPYTHON_EXECUTABLE={}".format(sys.executable),
            '-DCMAKE_BUILD_TYPE={}'.format(cfg),
            # INFO: You can add custom cmake_args here.
        ]

        build_args = []
        # Adding CMake arguments set as environment variable
        # (needed e.g. to build for ARM OSx on conda-forge)
        if "CMAKE_ARGS" in os.environ:
            cmake_args += [item for item in os.environ["CMAKE_ARGS"].split(" ") if item]
        for k, v in ext.cmake_args.items():
            cmake_args.append('-D{}={}'.format(k, v))

        if self.compiler.compiler_type != "msvc":
            # Using Ninja-build since it a) is available as a wheel and b)
            # multithreads automatically. MSVC would require all variables be
            # exported for Ninja to pick it up, which is a little tricky to do.
            # Users can override the generator with CMAKE_GENERATOR in CMake
            # 3.15+.
            if not cmake_generator:
                try:
                    import ninja  # noqa: F401
                    cmake_args += ["-GNinja"]
                except ImportError:
                    pass

        else:
            # Single config generators are handled "normally"
            single_config = any(x in cmake_generator for x in {"NMake", "Ninja"})

            # CMake allows an arch-in-generator style for backward compatibility
            contains_arch = any(x in cmake_generator for x in {"ARM", "Win64"})

            # Specify the arch if using MSVC generator, but only if it doesn't
            # contain a backward-compatibility arch spec already in the
            # generator name.
            if not single_config and not contains_arch:
                cmake_args += ["-A", PLAT_TO_CMAKE[self.plat_name]]

            # Multi-config generators have a different way to specify configs
            if not single_config:
                cmake_args += [
                    f"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{cfg.upper()}={extdir}"
                ]
                build_args += ["--config", cfg]

        if sys.platform.startswith("darwin"):
            # Cross-compile support for macOS - respect ARCHFLAGS if set
            archs = re.findall(r"-arch (\S+)", os.environ.get("ARCHFLAGS", ""))
            if archs:
                cmake_args += ["-DCMAKE_OSX_ARCHITECTURES={}".format(";".join(archs))]

        # example of build args
        # Set CMAKE_BUILD_PARALLEL_LEVEL to control the parallel build level
        # across all generators.
        if "CMAKE_BUILD_PARALLEL_LEVEL" not in os.environ:
            # self.parallel is a Python 3 only way to set parallel jobs by hand
            # using -j in the build_ext call, not supported by pip or PyPA-build.
            if hasattr(self, "parallel") and self.parallel:
                # CMake 3.12+ only.
                build_args += [f"-j{self.parallel}"]

        if ext.target_name is not None:
            build_args += ["--target={}".format(ext.target_name)]

        subprocess.check_call(
            ["cmake", str(cmakelists_dir)] + cmake_args, cwd=str(build_temp)
        )

        if not self.dry_run:
            subprocess.check_call(
                ["cmake", "--build", "."] + build_args, cwd=str(build_temp)
            )


__doc__ = """
Example:
Project Tree:
├── ext1
│   ├── CMakeLists.txt
│   ├── ext1.cpython-39-darwin.so  # Extension output to here (--inplace).
│   └── src
│       └── ext1.cpp
├── ext2
│   ├── CMakeLists.txt
│   ├── ext2.cpython-39-darwin.so  # Extension output to here (--inplace).
│   ├── ext3.cpython-39-darwin.so  # Extension output to here (--inplace).
│   └── src
│       ├── ext2.cpp
│       └── ext3.cpp
└── setup.py

And see setup function.
"""

setup(
    name='example',
    version='0.1',
    packages=['example'],
    ext_modules=[CMakeExtension('ext1.ext1', cmake_args={"pybind11_DIR": pybind11.get_cmake_dir()}),
                 *CMakeExtensionize(['ext2.ext2', 'ext2.ext3'], cmake_args={"pybind11_DIR": pybind11.get_cmake_dir()})],
    cmdclass={
        'build_ext': CMakeBuild,
    }
)
