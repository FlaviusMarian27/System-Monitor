#include "include/core.h"
#include <stdio.h>
#include <string.h>

static CpuRawData prev_total = {0};
static CpuRawData prev_cores[MAX_CORES] = {0};
static int is_first_run = 1;

void get_system_metrics(SystemMetrics *metrics){
    //preluam datele
    if (cpu_get_model_name(metrics->cpu_model,sizeof(metrics->cpu_model)) == 0){
        fprintf(stderr, "Could not get model name\n");
        strncpy(metrics->cpu_model, "Unknown CPU", sizeof(metrics->cpu_model) - 1);
        metrics->cpu_model[sizeof(metrics->cpu_model) - 1] = '\0';
    }
    metrics->core_count = cpu_get_core_count();
    metrics->cpu_freq_mhz = cpu_get_current_freq_mhz();

    //pregatim stucturile pentru noile citiri
    CpuRawData curr_total = {0};
    CpuRawData curr_cores[MAX_CORES] = {0};

    //citim datele acum
    cpu_get_raw_data(&curr_total, curr_cores,metrics->core_count);
    if (is_first_run){
        metrics->cpu_usage_percent = 0.0;
        for (int i = 0; i < metrics->core_count; i = i + 1){
            metrics->cpu_cores_usage[i] = 0.0;
        }
        is_first_run = 0;
    }else{
        metrics->cpu_usage_percent = cpu_calculate_usage(&prev_total,&curr_total);

        for (int i = 0; i < metrics->core_count; i = i + 1){
            metrics->cpu_cores_usage[i] = cpu_calculate_usage(&prev_cores[i],&curr_cores[i]);
        }
    }

    //salvam starea actuala pentru apelul de runda urmatoare
    prev_total = curr_total;
    for (int i = 0; i < metrics->core_count; i = i + 1){
        prev_cores[i] = curr_cores[i];
    }

    MemoryData ram_data = {0};
    if (memory_get_data(&ram_data)) {
        metrics->ram_total_gb = ram_data.total_gb;
        metrics->ram_used_gb = ram_data.used_gb;
        metrics->ram_usage_percent = ram_data.usage_percent;
    } else {
        metrics->ram_total_gb = 0.0;
        metrics->ram_used_gb = 0.0;
        metrics->ram_usage_percent = 0.0;
    }

    //pentru disk
    DiskData disk_data = {0};
    if (disk_get_data("/", &disk_data)) {
        metrics->disk_total_gb = disk_data.total_gb;
        metrics->disk_used_gb = disk_data.used_gb;
        metrics->disk_usage_percent = disk_data.usage_percent;
    } else {
        metrics->disk_total_gb = 0.0;
        metrics->disk_used_gb = 0.0;
        metrics->disk_usage_percent = 0.0;
    }

    // System Info
    SysInfoData sys_data = {0};
    if (sysinfo_get_data(&sys_data)) {
        metrics->uptime_seconds = sys_data.uptime_seconds;
        strncpy(metrics->os_name, sys_data.os_name, sizeof(metrics->os_name) - 1);
        metrics->os_name[sizeof(metrics->os_name) - 1] = '\0';

        strncpy(metrics->kernel_version, sys_data.kernel_version, sizeof(metrics->kernel_version) - 1);
        metrics->kernel_version[sizeof(metrics->kernel_version) - 1] = '\0';
    }
}