#ifndef DISK_H
#define DISK_H

typedef struct {
    double total_gb;
    double used_gb;
    double free_gb;
    double usage_percent;
} DiskData;

int disk_get_data(const char *path, DiskData *disk);

#endif