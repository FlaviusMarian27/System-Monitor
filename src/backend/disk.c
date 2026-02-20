#include "include/disk.h"
#include <sys/statvfs.h>
#include <stdio.h>

int disk_get_data(const char *path, DiskData *disk){
    struct statvfs stat;

    if (statvfs(path, &stat) != 0) {
        fprintf(stderr, "Could not get stats for path: %s\n", path);
        return 0;
    }

    double total_bytes = (double)stat.f_blocks * stat.f_frsize;
    double free_bytes = (double)stat.f_bfree * stat.f_frsize;
    double used_bytes = total_bytes - free_bytes;

    disk->total_gb = total_bytes / (1024.0 * 1024.0 * 1024.0);
    disk->free_gb = free_bytes / (1024.0 * 1024.0 * 1024.0);
    disk->used_gb = used_bytes / (1024.0 * 1024.0 * 1024.0);

    if (total_bytes > 0) {
        disk->usage_percent = (used_bytes / total_bytes) * 100.0;
    } else {
        disk->usage_percent = 0.0;
    }

    return 1;
}