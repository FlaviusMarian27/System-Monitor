#ifndef GPU_H
#define GPU_H

#define STR_LEN 256
#define BUFFER_SIZE 512

typedef struct{
    char name[STR_LEN];
    double usage_percent;
    double memory_total_mb;
    double memory_used_mb;
}GpuData;

int gpu_get_data(GpuData* gpu);

#endif