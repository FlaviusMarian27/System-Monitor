#define _DEFAULT_SOURCE
#include "include/processes.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <dirent.h>
#include <unistd.h>
#include <pwd.h>
#include <sys/stat.h>

/*
 * Citim procesele direct din /proc, fara ps.
 * CPU% e calculat la fel ca in ps: timp CPU total / timp de viata al procesului.
 * RAM% = RSS / MemTotal.
 */

static double read_uptime(void){
    double up = 0.0;
    FILE *f = fopen("/proc/uptime", "r");
    if (f){
        if (fscanf(f, "%lf", &up) != 1) up = 0.0;
        fclose(f);
    }
    return up;
}

static double read_mem_total_kb(void){
    char line[LINE_LEN];
    double total = 0.0;
    FILE *f = fopen("/proc/meminfo", "r");
    if (!f) return 0.0;
    while (fgets(line, sizeof(line), f)){
        if (sscanf(line, "MemTotal: %lf kB", &total) == 1) break;
    }
    fclose(f);
    return total;
}

static int cmp_cpu_desc(const void *a, const void *b){
    const ProcessData *pa = a, *pb = b;
    if (pa->cpu_percent < pb->cpu_percent) return 1;
    if (pa->cpu_percent > pb->cpu_percent) return -1;
    return 0;
}

int processes_get_top(ProcessData *procs, int max_count){
    DIR *dir = opendir("/proc");
    if (dir == NULL){
        perror("opendir /proc");
        return 0;
    }

    long hz = sysconf(_SC_CLK_TCK);
    long page_kb = sysconf(_SC_PAGESIZE) / 1024;
    double uptime = read_uptime();
    double mem_total_kb = read_mem_total_kb();

    int cap = 512, n = 0;
    ProcessData *all = malloc(cap * sizeof(ProcessData));
    if (all == NULL){
        closedir(dir);
        return 0;
    }

    struct dirent *ent;
    while ((ent = readdir(dir)) != NULL){
        if (!isdigit((unsigned char)ent->d_name[0])) continue;

        char path[300];
        snprintf(path, sizeof(path), "/proc/%s/stat", ent->d_name);
        FILE *f = fopen(path, "r");
        if (f == NULL) continue; // procesul s-a terminat intre timp

        char buf[1024];
        size_t len = fread(buf, 1, sizeof(buf) - 1, f);
        fclose(f);
        buf[len] = '\0';

        // format: pid (comm) state ppid ... ; comm poate contine spatii/paranteze
        char *open_p = strchr(buf, '(');
        char *close_p = strrchr(buf, ')');
        if (!open_p || !close_p || close_p < open_p) continue;

        unsigned long utime, stime, starttime;
        long rss;
        // dupa ')' : state(3) ... utime(14) stime(15) ... starttime(22) vsize(23) rss(24)
        if (sscanf(close_p + 2,
                   "%*c %*d %*d %*d %*d %*d %*u %*u %*u %*u %*u %lu %lu "
                   "%*d %*d %*d %*d %*d %*d %lu %*u %ld",
                   &utime, &stime, &starttime, &rss) != 4) continue;

        if (n == cap){
            cap *= 2;
            ProcessData *tmp = realloc(all, cap * sizeof(ProcessData));
            if (tmp == NULL) break;
            all = tmp;
        }
        ProcessData *p = &all[n];
        memset(p, 0, sizeof(*p));

        p->pid = atoi(ent->d_name);

        size_t name_len = (size_t)(close_p - open_p - 1);
        if (name_len >= STR_LEN) name_len = STR_LEN - 1;
        memcpy(p->name, open_p + 1, name_len);
        p->name[name_len] = '\0';

        double elapsed = uptime - (double)starttime / hz;
        double cpu_sec = (double)(utime + stime) / hz;
        p->cpu_percent = elapsed > 0 ? 100.0 * cpu_sec / elapsed : 0.0;

        p->ram_percent = mem_total_kb > 0 ? 100.0 * (rss * page_kb) / mem_total_kb : 0.0;

        // user = proprietarul directorului /proc/<pid>
        struct stat st;
        snprintf(path, sizeof(path), "/proc/%s", ent->d_name);
        if (stat(path, &st) == 0){
            struct passwd *pw = getpwuid(st.st_uid);
            if (pw) snprintf(p->user, STR_LEN, "%s", pw->pw_name);
            else    snprintf(p->user, STR_LEN, "%u", st.st_uid);
        } else {
            snprintf(p->user, STR_LEN, "?");
        }

        n++;
    }
    closedir(dir);

    qsort(all, n, sizeof(ProcessData), cmp_cpu_desc);

    int count = n < max_count ? n : max_count;
    memcpy(procs, all, count * sizeof(ProcessData));
    free(all);
    return count;
}