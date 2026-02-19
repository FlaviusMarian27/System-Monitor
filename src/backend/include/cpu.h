#ifndef CPU_H
#define CPU_H

#include <stdint.h>
#include <stddef.h>

#define MAX_CORES 64
#define LEN_LINE 512

typedef struct{
    uint64_t user;
    uint64_t nice;
    uint64_t system;
    uint64_t idle;
    uint64_t iowait;
    uint64_t irq;
    uint64_t softirq;
    uint64_t steal;
}CpuRawData;

//functii pentru informatii staticii
int cpu_get_model_name(char *buffer, size_t size);
int cpu_get_core_count(void);
double cpu_get_current_freq_mhz(void);

//functia pentru citirea si calcularea utilizatrii
int cpu_get_raw_data(CpuRawData *total_data, CpuRawData *cores_data, int num_cores);

//functia pentru procentaj
double cpu_calculate_usage(CpuRawData *prev, CpuRawData *curr);

#endif