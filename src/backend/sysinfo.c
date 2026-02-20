#include "include/sysinfo.h"
#include <sys/sysinfo.h>
#include <sys/utsname.h>
#include <string.h>

int sysinfo_get_data(SysInfoData* info){
    //luam uptime-ul(de cand ii aprins pc-ul)
    struct sysinfo s_info;
    if (sysinfo(&s_info) == 0){
        info->uptime_seconds = s_info.uptime;
    }else{
        info->uptime_seconds = 0;
    }

    //luam informatiile despre kernel
    struct utsname u_name;
    if (uname(&u_name) == 0){
        strncpy(info->os_name, u_name.sysname, STR_LEN - 1);
        info->os_name[STR_LEN - 1] = '\0';

        strncpy(info->kernel_version, u_name.release, STR_LEN - 1);
        info->kernel_version[STR_LEN - 1] = '\0';
    }else{
        strncpy(info->os_name, "Unknown", STR_LEN - 1);
        strncpy(info->kernel_version, "Unknown", STR_LEN - 1);
    }

    return 1;
}