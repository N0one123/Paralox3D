cmake_minimum_required(VERSION 3.16)
project(Vertex3D LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

add_library(vertex3d SHARED
    native/src/vertex3d.cpp
)

target_include_directories(vertex3d
    PUBLIC
        native/include
)

target_compile_definitions(vertex3d PRIVATE V3D_BUILD)

if(MSVC)
    target_compile_options(vertex3d PRIVATE /O2)
else()
    target_compile_options(vertex3d PRIVATE -O2)
endif()
