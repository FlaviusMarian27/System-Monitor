#include "include/gpu.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

int gpu_get_data(GpuData* gpu){
    strncpy(gpu->name, "Unknown GPU", STR_LEN - 1);
    gpu->usage_percent = 0.0;
    gpu->memory_total_mb = 0.0;
    gpu->memory_used_mb = 0.0;

    FILE *fin = popen("nvidia-smi --query-gpu=name,utilization.gpu,memory.total,memory.used --format=csv,noheader,nounits", "r");
    if (fin == NULL){
        return 0;
    }

    char buffer[BUFFER_SIZE];
    if (fgets(buffer, BUFFER_SIZE, fin) != NULL){
        //extragen numele
        char *token = strtok(buffer, ",");
        if (token){
            strncpy(gpu->name, token, STR_LEN - 1);
            gpu->name[STR_LEN - 1] = '\0';
        }

        //extragem utilizarea
        token = strtok(NULL, ",");
        if (token){
            gpu->usage_percent = atof(token);
        }

        //extragem memoria total
        token = strtok(NULL, ",");
        if (token){
            gpu->memory_total_mb = atof(token);
        }

        //extragem memoria folosita
        token = strtok(NULL, ",");
        if (token){
            gpu->memory_used_mb = atof(token);
        }

        if (pclose(fin) != 0){
            return 0;
        }
        return 1;
    }

    if (pclose(fin) != 0){
        return 0;
    }
    return 0;
}