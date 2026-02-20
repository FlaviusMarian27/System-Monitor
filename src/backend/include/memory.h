#ifndef MEMORY_H
#define MEMORY_H

#include <stdint.h>

#define SIZE 256

typedef struct{
    double total_gb;
    double used_gb;
    double usage_percent;
}MemoryData;

int memory_get_data(MemoryData *mem);

#endif