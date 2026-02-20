#include "include/memory.h"
#include <stdio.h>
#include <string.h>

int memory_get_data(MemoryData *mem){
    FILE *fin = fopen("/proc/meminfo", "r");
    if (fin == NULL){
        fprintf(stderr,"Unable to open /proc/meminfo\n");
        return 0;
    }

    char line[SIZE];
    uint64_t mem_total = 0;
    uint64_t mem_available = 0;
    while (fgets(line, sizeof(line), fin) != NULL){
        if (strncmp(line, "MemTotal:", 9) == 0){
            sscanf(line, "MemTotal: %lu kB", &mem_total);
        }else if (strncmp(line, "MemAvailable:", 13) == 0){
            sscanf(line, "MemAvailable: %lu kB", &mem_available);
        }

        if (mem_total > 0 && mem_available > 0){
            break;
        }
    }

    if (fclose(fin) != 0){
        fprintf(stderr,"Unable to close /proc/meminfo\n");
        return 0;
    }

    if (mem_total > 0){
        uint64_t mem_used = mem_total - mem_available;

        //transformam kilo in giga
        mem->total_gb = (double)mem_total/(1024.0 * 1024.0);
        mem->used_gb = (double)mem_used/(1024.0 * 1024.0);
        mem->usage_percent = ((double)mem_used/mem_total) * 100.0;
        return 1;
    }

    return 0;
}