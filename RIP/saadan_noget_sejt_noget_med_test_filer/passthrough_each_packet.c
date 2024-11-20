#include <pcap.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <unistd.h>

#define SNAP_LEN 1518  // Maximum bytes to capture
#define ERRBUF_SIZE 256

typedef struct {
    pcap_t *source_handle;
    pcap_t *dest_handle;
    int mtu;  // Maximum Transmission Unit of the destination interface
} forwarder_args_t;

void *forward_packets(void *args) {
    forwarder_args_t *forwarder = (forwarder_args_t *)args;
    struct pcap_pkthdr *header;
    const u_char *packet;
    int ret;

    while (1) {
        ret = pcap_next_ex(forwarder->source_handle, &header, &packet);
        if (ret == 1) { // Packet captured
            int packet_len = header->len;

            // Truncate packet if it exceeds MTU
            if (packet_len > forwarder->mtu) {
                packet_len = forwarder->mtu;
                fprintf(stderr, "Warning: Truncated packet from %d to %d bytes\n", header->len, packet_len);
            }

            if (pcap_inject(forwarder->dest_handle, packet, packet_len) == -1) {
                fprintf(stderr, "Error sending packet: %s\n", pcap_geterr(forwarder->dest_handle));
            }
        } else if (ret == 0) {
            // Timeout expired, no packet captured
            continue;
        } else {
            fprintf(stderr, "Error capturing packet: %s\n", pcap_geterr(forwarder->source_handle));
            break;
        }
    }
    return NULL;
}

int get_interface_mtu(const char *interface_name) {
    struct ifreq ifr;
    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) {
        perror("socket");
        exit(EXIT_FAILURE);
    }

    strncpy(ifr.ifr_name, interface_name, IFNAMSIZ - 1);
    if (ioctl(sock, SIOCGIFMTU, &ifr) < 0) {
        perror("ioctl");
        close(sock);
        exit(EXIT_FAILURE);
    }

    close(sock);
    return ifr.ifr_mtu;
}

int main(int argc, char *argv[]) {
    if (argc != 3) {
        fprintf(stderr, "Usage: %s <interface1> <interface2>\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    char *interface1 = argv[1];
    char *interface2 = argv[2];
    char errbuf[ERRBUF_SIZE];

    // Get MTUs of the interfaces
    int mtu1 = get_interface_mtu(interface1);
    int mtu2 = get_interface_mtu(interface2);

    printf("MTU of %s: %d\n", interface1, mtu1);
    printf("MTU of %s: %d\n", interface2, mtu2);

    // Open both interfaces
    pcap_t *handle1 = pcap_open_live(interface1, SNAP_LEN, 1, 1000, errbuf);
    if (handle1 == NULL) {
        fprintf(stderr, "Error opening interface %s: %s\n", interface1, errbuf);
        exit(EXIT_FAILURE);
    }

    pcap_t *handle2 = pcap_open_live(interface2, SNAP_LEN, 1, 1000, errbuf);
    if (handle2 == NULL) {
        fprintf(stderr, "Error opening interface %s: %s\n", interface2, errbuf);
        pcap_close(handle1);
        exit(EXIT_FAILURE);
    }

    printf("Forwarding packets between %s and %s...\n", interface1, interface2);

    // Create threads for bidirectional packet forwarding
    pthread_t thread1, thread2;

    forwarder_args_t forward1 = {handle1, handle2, mtu2};
    forwarder_args_t forward2 = {handle2, handle1, mtu1};

    if (pthread_create(&thread1, NULL, forward_packets, &forward1) != 0) {
        fprintf(stderr, "Error creating thread for %s -> %s\n", interface1, interface2);
        pcap_close(handle1);
        pcap_close(handle2);
        exit(EXIT_FAILURE);
    }

    if (pthread_create(&thread2, NULL, forward_packets, &forward2) != 0) {
        fprintf(stderr, "Error creating thread for %s -> %s\n", interface2, interface1);
        pcap_close(handle1);
        pcap_close(handle2);
        pthread_cancel(thread1);
        exit(EXIT_FAILURE);
    }

    // Wait for threads to complete (they won't, unless an error occurs)
    pthread_join(thread1, NULL);
    pthread_join(thread2, NULL);

    // Clean up
    pcap_close(handle1);
    pcap_close(handle2);

    return 0;
}
