#ifndef CORE_H
#define CORE_H

#include "cpu.h"
#include "memory.h"
#include "disk.h"
#include "sysinfo.h"
#include "gpu.h"
#include "processes.h"
#include "network.h"

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

    //pentru disk
    double disk_total_gb;
    double disk_used_gb;
    double disk_usage_percent;

    //detalii OS
    long uptime_seconds;
    char os_name[LEN_LINE];
    char kernel_version[LEN_LINE];

    // GPU
    char gpu_name[LEN_LINE];
    double gpu_usage_percent;
    double gpu_memory_total_gb;
    double gpu_memory_used_gb;

    // Procese
    int process_count;
    ProcessData processes[MAX_PROCESSES];

    // Retea
    double net_rx_kbps;
    double net_tx_kbps;
}SystemMetrics;

void get_system_metrics(SystemMetrics *metrics);

#endif