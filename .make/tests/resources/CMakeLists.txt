cmake_minimum_required( VERSION 2.6 )
project( ska-rpm-correct )
add_executable(main main.cpp)

# Install executable and MANIFEST
install(TARGETS main RUNTIME)

# -- generic package settings
set(PACK_NAME ${PROJECT_NAME})
set(CPACK_PACKAGE_FILE_NAME "${PACK_NAME}-${VERSION}")
if(NOT DEFINED CPACK_GENERATOR)
    if(CMAKE_HOST_SYSTEM_NAME MATCHES "Linux")
        set(CPACK_GENERATOR "RPM")
    endif(CMAKE_HOST_SYSTEM_NAME MATCHES "Linux")
endif(NOT DEFINED CPACK_GENERATOR)
set(CPACK_STRIP_FILES YES)
set(CPACK_PACKAGE_HOMEPAGE_URL "https://gitlab.com/ska-telescope/sdi/ska-cicd-stencil")

# -- rpm specifics
set(CPACK_RPM_PACKAGE_REQUIRES "libboost >= 1.53")
set(CPACK_RPM_DEFAULT_DIR_PERMISSIONS OWNER_EXECUTE OWNER_WRITE OWNER_READ GROUP_EXECUTE GROUP_READ WORLD_EXECUTE WORLD_READ)
set(CPACK_RPM_PACKAGE_DESCRIPTION "Packaged with CPack (https://cmake.org)")
set(CPACK_RPM_PACKAGE_SUMMARY "Example STENCIL RPM Package")

include(CPack)
