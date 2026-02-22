#include "include/network.h"
#include <stdio.h>
#include <string.h>

static unsigned long long prev_rx = 0;
static unsigned long long prev_tx = 0;
static int is_first_run = 1;

int network_get_data(NetworkData *net) {
    FILE *fin = fopen("/proc/net/dev", "r");
    if (!fin) return 0;

    char line[512];
    unsigned long long total_rx = 0;
    unsigned long long total_tx = 0;

    fgets(line, sizeof(line), fin);
    fgets(line, sizeof(line), fin);

    while (fgets(line, sizeof(line), fin)) {
        char iface[32];
        unsigned long long rx_bytes, tx_bytes, dummy;

        char *colon = strchr(line, ':');
        if (colon) {
            *colon = ' ';
            if (sscanf(line, "%s %llu %llu %llu %llu %llu %llu %llu %llu %llu",iface, &rx_bytes, &dummy, &dummy, &dummy, &dummy, &dummy, &dummy, &dummy, &tx_bytes) >= 10) {
                if (strcmp(iface, "lo") != 0) {
                    total_rx += rx_bytes;
                    total_tx += tx_bytes;
                }
            }
        }
    }
    fclose(fin);

    if (is_first_run) {
        net->rx_speed_kbps = 0.0;
        net->tx_speed_kbps = 0.0;
        is_first_run = 0;
    } else {
        net->rx_speed_kbps = (double)(total_rx - prev_rx) / 1024.0;
        net->tx_speed_kbps = (double)(total_tx - prev_tx) / 1024.0;
    }

    prev_rx = total_rx;
    prev_tx = total_tx;

    return 1;
}