#ifndef CORE_H
#define CORE_H

#include "cpu.h"
#include "memory.h"

typedef struct{
    char cpu_model[LEN_LINE];
    int core_count;
    double cpu_freq_mhz;
    double cpu_usage_percent;
    double cpu_cores_usage[MAX_CORES];

    //memoria RAM
    double ram_total_gb;
    double ram_used_gb;
    double ram_usage_percent;
}SystemMetrics;

void get_system_metrics(SystemMetrics *metrics);

#endif