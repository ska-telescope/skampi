from conans import CMake, ConanFile


class ExampleConanPackageConan(ConanFile):
    name = "ska-example-conan-package"
    version = "0.0.1"
    generators = "cmake"
    exports_sources = "altsrc/*"

    def build(self):
        cmake = CMake(self)
        # The CMakeLists.txt file must be in `source_folder`
        cmake.configure(source_folder="altsrc")
        cmake.build()

    def package(self):
        # Copy headers to the include folder and libraries to the lib folder
        self.copy("MANIFEST.skao.int", src="altsrc")
        self.copy("*.h", dst="include", src="altsrc")
        self.copy("*.a", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = ["ExampleConanPackage"]
