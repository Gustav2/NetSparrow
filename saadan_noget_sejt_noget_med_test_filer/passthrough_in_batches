#include <pcap.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <unistd.h>
#include <poll.h>
#include <sched.h>

#define SNAP_LEN 1518
#define ERRBUF_SIZE 256
#define BATCH_SIZE 32

typedef struct {
    pcap_t *source_handle;
    pcap_t *dest_handle;
    int mtu;
} forwarder_args_t;

void *forward_packets(void *args) {
    forwarder_args_t *forward_args = (forwarder_args_t *)args;
    pcap_t *source_handle = forward_args->source_handle;
    pcap_t *dest_handle = forward_args->dest_handle;

    struct pcap_pkthdr header;
    const u_char *packet;
    
    while (1) {
        packet = pcap_next(source_handle, &header);
        if (packet == NULL) {
            continue;  // Handle packet read error or timeout
        }

        if (pcap_sendpacket(dest_handle, packet, header.len) != 0) {
            fprintf(stderr, "Error sending packet: %s\n", pcap_geterr(dest_handle));
        }
    }
    return NULL;
}

int get_interface_mtu(const char *interface_name) {
    struct ifreq ifr;
    int sockfd = socket(AF_INET, SOCK_DGRAM, 0);
    if (sockfd == -1) {
        perror("Socket error");
        return -1;
    }

    strncpy(ifr.ifr_name, interface_name, IFNAMSIZ - 1);
    if (ioctl(sockfd, SIOCGIFMTU, &ifr) == -1) {
        perror("IOCTL error");
        close(sockfd);
        return -1;
    }

    close(sockfd);
    return ifr.ifr_mtu;
}

void optimize_interface(const char *interface_name) {
    printf("Optimizing interface %s\n", interface_name);
    char command[256];
    snprintf(command, sizeof(command), "sudo ethtool -K %s gro off", interface_name);
    system(command);
    snprintf(command, sizeof(command), "sudo ethtool -K %s lro off", interface_name);
    system(command);
    snprintf(command, sizeof(command), "sudo ethtool -C %s rx-usecs 0", interface_name);
    system(command);
}

int main(int argc, char *argv[]) {
    if (argc != 3) {
        fprintf(stderr, "Usage: %s <interface1> <interface2>\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    char *interface1 = argv[1];
    char *interface2 = argv[2];
    char errbuf[ERRBUF_SIZE];

    optimize_interface(interface1);
    optimize_interface(interface2);

    nice(-20);  // Set process to high priority

    int mtu1 = get_interface_mtu(interface1);
    int mtu2 = get_interface_mtu(interface2);

    if (mtu1 == -1 || mtu2 == -1) {
        fprintf(stderr, "Error getting MTU for interfaces\n");
        exit(EXIT_FAILURE);
    }

    // Create pcap handles for both interfaces
    pcap_t *handle1 = pcap_create(interface1, errbuf);
    pcap_t *handle2 = pcap_create(interface2, errbuf);
    if (!handle1 || !handle2) {
        fprintf(stderr, "Error creating capture handles: %s\n", errbuf);
        exit(EXIT_FAILURE);
    }

    // Configure capture settings for high performance
    pcap_t *handles[] = {handle1, handle2};
    for (size_t i = 0; i < 2; i++) {
        pcap_set_snaplen(handles[i], SNAP_LEN);
        pcap_set_promisc(handles[i], 1);
        pcap_set_timeout(handles[i], 10); // Increase timeout to 10ms
        pcap_set_buffer_size(handles[i], 1024 * 1024 * 64); // 64MB buffer
        pcap_set_immediate_mode(handles[i], 1);

        if (pcap_activate(handles[i]) != 0) {
            fprintf(stderr, "Error activating capture: %s\n", pcap_geterr(handles[i]));
            exit(EXIT_FAILURE);
        }
    }

    printf("Forwarding packets between %s and %s...\n", interface1, interface2);

    pthread_t thread1, thread2;
    forwarder_args_t forward1 = {handle1, handle2, mtu2};
    forwarder_args_t forward2 = {handle2, handle1, mtu1};

    // Set high priority for threads
    pthread_attr_t attr;
    struct sched_param param;
    pthread_attr_init(&attr);
    pthread_attr_setschedpolicy(&attr, SCHED_FIFO);
    param.sched_priority = 50;
    pthread_attr_setschedparam(&attr, &param);

    if (pthread_create(&thread1, &attr, forward_packets, &forward1) != 0) {
        fprintf(stderr, "Error creating thread for %s -> %s\n", interface1, interface2);
        exit(EXIT_FAILURE);
    }

    if (pthread_create(&thread2, &attr, forward_packets, &forward2) != 0) {
        fprintf(stderr, "Error creating thread for %s -> %s\n", interface2, interface1);
        exit(EXIT_FAILURE);
    }

    pthread_join(thread1, NULL);
    pthread_join(thread2, NULL);

    pcap_close(handle1);
    pcap_close(handle2);

    return 0;
}
