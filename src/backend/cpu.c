#include "include/cpu.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h> // Pentru sysconf()

//pentru numarul de coruri logice
int cpu_get_core_count(void){
    long core = sysconf(_SC_NPROCESSORS_ONLN);//Numarul de procese disponibile
    if (core < 1){
        return 1;
    }

    if (core > MAX_CORES){
        return MAX_CORES;
    }

    return (int)core;
}

//obtine medelul procesorului
int cpu_get_model_name(char *buffer, size_t size){
    FILE *fin = fopen("/proc/cpuinfo", "r");
    if (fin == NULL){
        fprintf(stderr, "Could not open /proc/cpuinfo\n");
        return 0;
    }

    char line[LEN_LINE];
    int found = 0;

    while (fgets(line, LEN_LINE, fin) != NULL){
        if (strncmp(line, "model name",10) == 0){
            char *colon = strchr(line, ':');
            if (colon){
                colon = colon + 2; // pentru a sari peste :
                char *newline = strchr(colon, '\n');
                if (newline){
                    *newline = '\0';
                }

                strncpy(buffer, colon, size - 1);
                buffer[size - 1] = '\0';
                found = 1;
                break;
            }
        }
    }

    if (fclose(fin) != 0){
        fprintf(stderr, "Could not close /proc/cpuinfo\n");
        return 0;
    }

    return found;
}

//optine freceventa curenta a primului nucleu in MHz
double cpu_get_current_freq_mhz(void){
    FILE *fin = fopen("/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq", "r");
    if (fin == NULL){
        fprintf(stderr, "Could not open /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq\n");
        return 0.0;
    }

    long freq_khz = 0;
    if (fscanf(fin,"%ld",&freq_khz) == 1){
        if (fclose(fin) != 0){
            fprintf(stderr,"Could not close /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freqss\n");
            return 0.0;
        }

        return (double)freq_khz / 1000.0;
    }

    if (fclose(fin) != 0){
        fprintf(stderr,"Could not close /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freqss\n");
        return 0.0;
    }

    return 0.0;
}

//citirea datelor brute pentru total și per-nucleu
int cpu_get_raw_data(CpuRawData *total_data, CpuRawData *cores_data, int num_cores){
    FILE *fin = fopen("/proc/stat", "r");
    if (fin == NULL){
        fprintf(stderr, "Could not open /proc/stat\n");
        return 0;
    }

    char buffer[LEN_LINE];
    int core_index = 0;
    while (fgets(buffer, LEN_LINE, fin) != NULL){
        //citim CPU ul total
        if (strncmp(buffer, "cpu ", 4) == 0){
            sscanf(buffer, "cpu  %lu %lu %lu %lu %lu %lu %lu %lu",
                &total_data->user, &total_data->nice,
                &total_data->system,&total_data->idle,
                &total_data->iowait, &total_data->irq,
                &total_data->softirq, &total_data->steal);
        }else if (strncmp(buffer, "cpu", 3) == 0 && buffer[3] >= '0' && buffer[3] <= '9' ){//citim per nucleu
            if (core_index < num_cores){
                sscanf(buffer, "cpu%*d %lu %lu %lu %lu %lu %lu %lu %lu",
                    &cores_data[core_index].user, &cores_data[core_index].nice,
                    &cores_data[core_index].system,&cores_data[core_index].idle,
                    &cores_data[core_index].iowait,&cores_data[core_index].irq,
                    &cores_data[core_index].softirq,&cores_data[core_index].steal);
            }
            core_index = core_index + 1;
        }
    }

    if (fclose(fin) != 0){
        fprintf(stderr, "Could not close /proc/stat\n");
        return 0;
    }

    return 1;
}

//calculam procentajul
double cpu_calculate_usage(CpuRawData *prev, CpuRawData *curr){
    uint64_t prev_idle = prev->idle + prev->iowait;
    uint64_t curr_idle = curr->idle + curr->iowait;

    uint64_t prev_non_idle = prev->user + prev->nice + prev->system + prev->irq + prev->softirq + prev->steal;
    uint64_t curr_non_idle = curr->user + curr->nice + curr->system + curr->irq + curr->softirq + curr->steal;

    uint64_t prev_total = prev_idle + prev_non_idle;
    uint64_t curr_total = curr_idle + curr_non_idle;

    uint64_t total_diff = curr_total - prev_total;
    uint64_t idle_diff = curr_idle - prev_idle;

    if (total_diff == 0){
        return 0.0;
    }

    return (double)(total_diff - idle_diff) / total_diff * 100.0;
}