#ifndef NETWORK_H
#define NETWORK_H

typedef struct {
    double rx_speed_kbps; // Viteza de Download (KB/s)
    double tx_speed_kbps; // Viteza de Upload (KB/s)
} NetworkData;

int network_get_data(NetworkData *net);

#endif // NETWORK_H