cmake_minimum_required(VERSION 3.16)
project(Paralox3D LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

add_library(paralox3d SHARED
    native/src/paralox3d.cpp
    native/src/renderer.cpp
)

target_include_directories(paralox3d PUBLIC native/include)
target_compile_definitions(paralox3d PRIVATE P3D_BUILD)

if(WIN32)
    target_link_libraries(paralox3d PRIVATE opengl32 user32 gdi32)
endif()

if(MSVC)
    target_compile_options(paralox3d PRIVATE /O2)
else()
    target_compile_options(paralox3d PRIVATE -O2)
endif()
