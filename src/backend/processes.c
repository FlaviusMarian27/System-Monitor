#include "include/processes.h"
#include <stdio.h>
#include <string.h>

int processes_get_top(ProcessData *procs, int max_count){
    FILE *fin = popen("ps -eo pid,comm,%cpu,%mem,user --sort=-%cpu | head -n 31", "r");
    if (fin == NULL){
        return 0;
    }

    char line[LINE_LEN];
    int count = 0;
    int is_header = 1;
    while (fgets(line, LINE_LEN, fin) != NULL && count < max_count){
        if (is_header){
            is_header = 0;
            continue;
        }

        if (sscanf(line, "%d %255s %lf %lf %255s",
            &procs[count].pid, procs[count].name, &procs[count].cpu_percent,
            &procs[count].ram_percent, procs[count].user) == 5) {
            count++;
        }
    }

    if (pclose(fin) != 0){
        return 0;
    }
    return count;
}