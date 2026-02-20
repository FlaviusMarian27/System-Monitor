#ifndef SYSINFO_H
#define SYSINFO_H

#define STR_LEN 256
typedef struct{
    long uptime_seconds;
    char os_name[STR_LEN];
    char kernel_version[STR_LEN];
}SysInfoData;

int sysinfo_get_data(SysInfoData* info);

#endif