from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.gnu import AutotoolsToolchain, Autotools
from conan.tools.layout import basic_layout
from conan.tools.files import apply_conandata_patches, collect_libs, copy, export_conandata_patches, get, rmdir
from conan.tools.microsoft import is_msvc, is_msvc_static_runtime
import os

required_conan_version = ">=1.53.0"


class ExpatConan(ConanFile):
    name = "expat"
    description = "Fast streaming XML parser written in C."
    license = "MIT"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/libexpat/libexpat"
    topics = ("xml", "parsing")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "char_type": ["char", "wchar_t", "ushort"],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "char_type": "char",
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def layout(self):
        if is_msvc(self):
            cmake_layout(self, src_folder="src")
        else:
            basic_layout(self)
            self.folders.source = "src"
            self.folders.build = "build"
            self.folders.generators = "build/generators"

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        if is_msvc(self):
            tc = CMakeToolchain(self)
            tc.variables["EXPAT_BUILD_DOCS"] = False
            tc.variables["EXPAT_BUILD_EXAMPLES"] = False
            tc.variables["EXPAT_SHARED_LIBS"] = self.options.shared
            tc.variables["EXPAT_BUILD_TESTS"] = False
            tc.variables["EXPAT_BUILD_TOOLS"] = False
            tc.variables["EXPAT_CHAR_TYPE"] = self.options.char_type
            if is_msvc(self):
                tc.variables["EXPAT_MSVC_STATIC_CRT"] = is_msvc_static_runtime(self)
            tc.variables["EXPAT_BUILD_PKGCONFIG"] = False
            tc.generate()
        else:
            tc = AutotoolsToolchain(self)
            if self.options.shared:
                tc.configure_args.append("--enable-shared")
                tc.configure_args.append("--disable-static")
            else:
                tc.configure_args.append("--disable-shared")
                tc.configure_args.append("--enable-static")
            tc.generate()

    def build(self):
        apply_conandata_patches(self)
        if is_msvc(self):
            cmake = CMake(self)
            cmake.configure()
            cmake.build()
        else:
            autotools = Autotools(self)
            autotools.configure()
            autotools.make()

    def package(self):
        copy(self, "COPYING", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        if is_msvc(self):
            cmake = CMake(self)
            cmake.install()
        else:
            autotools = Autotools(self)
            autotools.install()
        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.set_property("cmake_module_target_name", "EXPAT::EXPAT")
        self.cpp_info.set_property("cmake_file_name", "EXPAT")
        self.cpp_info.set_property("cmake_target_name", "EXPAT::EXPAT")
        self.cpp_info.set_property("pkg_config_name", "expat")

        self.cpp_info.libs = collect_libs(self)

        if not self.options.shared:
            self.cpp_info.defines = ["XML_STATIC"]
        if self.options.get_safe("char_type") in ("wchar_t", "ushort"):
            self.cpp_info.defines.append("XML_UNICODE")
        elif self.options.get_safe("char_type") == "wchar_t":
            self.cpp_info.defines.append("XML_UNICODE_WCHAR_T")

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("m")
