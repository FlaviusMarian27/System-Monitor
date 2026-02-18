cmake_minimum_required(VERSION 4.1)
project(System_Monitor C)

set(CMAKE_C_STANDARD 11)

add_executable(System_Monitor src/frontend/main.c
        src/backend/include/cpu.h
        src/backend/include/disk.h
        src/backend/include/gpu.h
        src/backend/include/memory.h
        src/backend/core.c
        src/backend/cpu.c
        src/backend/disk.c
        src/backend/gpu.c
        src/backend/memory.c)
