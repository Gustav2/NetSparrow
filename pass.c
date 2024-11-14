#include <pcap.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <unistd.h>
#include <errno.h>

#define SNAP_LEN 1518
#define ERRBUF_SIZE 256
#define BATCH_SIZE 32         // Process multiple packets per iteration
#define PCAP_TIMEOUT 1       // Timeout in ms for packet capture
#define PCAP_BUFFER_SIZE (32 * 1024 * 1024)  // 32MB buffer size

typedef struct {
    pcap_t *source_handle;
    pcap_t *dest_handle;
    int mtu;
    const char *source_name;
    const char *dest_name;
} forwarder_args_t;

// Ring buffer for packet batching
typedef struct {
    struct pcap_pkthdr **headers;
    const u_char **packets;
    int size;
    int capacity;
} packet_ring_t;

packet_ring_t *create_packet_ring(int capacity) {
    packet_ring_t *ring = malloc(sizeof(packet_ring_t));
    ring->headers = malloc(capacity * sizeof(struct pcap_pkthdr *));
    ring->packets = malloc(capacity * sizeof(u_char *));
    ring->size = 0;
    ring->capacity = capacity;
    return ring;
}

void destroy_packet_ring(packet_ring_t *ring) {
    free(ring->headers);
    free(ring->packets);
    free(ring);
}

void *forward_packets(void *args) {
    forwarder_args_t *forwarder = (forwarder_args_t *)args;
    packet_ring_t *ring = create_packet_ring(BATCH_SIZE);
    struct pcap_pkthdr *header;
    const u_char *packet;
    int ret;

    // Set thread affinity to improve cache usage
    cpu_set_t cpuset;
    CPU_ZERO(&cpuset);
    CPU_SET(0, &cpuset);  // Pin to CPU 0 (adjust as needed)
    pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &cpuset);

    while (1) {
        // Collect batch of packets
        while (ring->size < ring->capacity) {
            ret = pcap_next_ex(forwarder->source_handle, &header, &packet);
            if (ret == 1) {
                ring->headers[ring->size] = header;
                ring->packets[ring->size] = packet;
                ring->size++;
            } else if (ret == 0) {
                break;  // Timeout, process what we have
            } else {
                fprintf(stderr, "Error capturing packet on %s: %s\n",
                        forwarder->source_name, pcap_geterr(forwarder->source_handle));
                goto cleanup;
            }
        }

        // Process the batch
        if (ring->size > 0) {
            for (int i = 0; i < ring->size; i++) {
                int packet_len = ring->headers[i]->len;
                if (packet_len > forwarder->mtu) {
                    packet_len = forwarder->mtu;
                }
                
                if (pcap_inject(forwarder->dest_handle, ring->packets[i], packet_len) == -1) {
                    fprintf(stderr, "Error sending packet on %s: %s\n",
                            forwarder->dest_name, pcap_geterr(forwarder->dest_handle));
                }
            }
            ring->size = 0;  // Reset for next batch
        }
    }

cleanup:
    destroy_packet_ring(ring);
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

void optimize_pcap_handle(pcap_t *handle, const char *interface_name) {
    // Increase buffer size
    if (pcap_set_buffer_size(handle, PCAP_BUFFER_SIZE) != 0) {
        fprintf(stderr, "Warning: Could not set buffer size for %s\n", interface_name);
    }

    // Enable immediate mode to reduce latency
    if (pcap_set_immediate_mode(handle, 1) != 0) {
        fprintf(stderr, "Warning: Could not enable immediate mode for %s\n", interface_name);
    }
}

int main(int argc, char *argv[]) {
    if (argc != 3) {
        fprintf(stderr, "Usage: %s <interface1> <interface2>\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    char *interface1 = argv[1];
    char *interface2 = argv[2];
    char errbuf[ERRBUF_SIZE];

    // Get MTUs
    int mtu1 = get_interface_mtu(interface1);
    int mtu2 = get_interface_mtu(interface2);
    printf("MTU of %s: %d\n", interface1, mtu1);
    printf("MTU of %s: %d\n", interface2, mtu2);

    // Open and configure interfaces
    pcap_t *handle1 = pcap_create(interface1, errbuf);
    pcap_t *handle2 = pcap_create(interface2, errbuf);
    
    if (!handle1 || !handle2) {
        fprintf(stderr, "Error creating pcap handles\n");
        exit(EXIT_FAILURE);
    }

    // Optimize both handles
    optimize_pcap_handle(handle1, interface1);
    optimize_pcap_handle(handle2, interface2);

    // Activate the handles
    if (pcap_activate(handle1) != 0 || pcap_activate(handle2) != 0) {
        fprintf(stderr, "Error activating pcap handles\n");
        exit(EXIT_FAILURE);
    }

    printf("Forwarding packets between %s and %s...\n", interface1, interface2);

    // Create threads for bidirectional forwarding
    pthread_t thread1, thread2;
    forwarder_args_t forward1 = {handle1, handle2, mtu2, interface1, interface2};
    forwarder_args_t forward2 = {handle2, handle1, mtu1, interface2, interface1};

    if (pthread_create(&thread1, NULL, forward_packets, &forward1) != 0) {
        fprintf(stderr, "Error creating thread for %s -> %s\n", interface1, interface2);
        goto cleanup;
    }

    if (pthread_create(&thread2, NULL, forward_packets, &forward2) != 0) {
        fprintf(stderr, "Error creating thread for %s -> %s\n", interface2, interface1);
        pthread_cancel(thread1);
        goto cleanup;
    }

    // Wait for threads to complete
    pthread_join(thread1, NULL);
    pthread_join(thread2, NULL);

cleanup:
    pcap_close(handle1);
    pcap_close(handle2);
    return 0;
}