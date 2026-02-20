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
}