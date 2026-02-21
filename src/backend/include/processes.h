#ifndef PROCESSES_H
#define PROCESSES_H

#define MAX_PROCESSES 30
#define STR_LEN 256
#define LINE_LEN 512

typedef struct{
    int pid;
    char name[STR_LEN];
    double cpu_percent;
    double ram_percent;
    char user[STR_LEN];
}ProcessData;

int processes_get_top(ProcessData *procs, int max_count);

#endif