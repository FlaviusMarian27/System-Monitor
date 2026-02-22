cmake_minimum_required(VERSION 4.1)
project(System_Monitor C)

add_compile_options(-Wall)

set(CMAKE_C_STANDARD 11)

include_directories(src/backend/include)

set(SOURCES
        src/backend/core.c
        src/backend/cpu.c
        src/backend/memory.c
        src/backend/disk.c
        src/backend/sysinfo.c
        src/backend/gpu.c
        src/backend/processes.c
)

add_library(monitor SHARED ${SOURCES})

set_target_properties(monitor PROPERTIES
        LIBRARY_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}/build"
)