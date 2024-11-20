#include <pcap.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <unistd.h>
#include <sched.h>
#include <arpa/inet.h>
#include <netinet/ip.h>
#include <signal.h>
#include <netinet/tcp.h>
#include <linux/if_packet.h>
#include <sys/mman.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <sys/stat.h>
#include <time.h>

#define SNAP_LEN 1518
#define ERRBUF_SIZE 256
#define BLACKLIST_MAX 2048
#define IP_STR_LEN 16
#define BATCH_SIZE 32

typedef struct {
    pcap_t *source_handle;
    pcap_t *dest_handle;
    int mtu;
} forwarder_args_t;

typedef struct {
    char filename[256];
    time_t last_modified;
} file_monitor_t;

char blacklist[BLACKLIST_MAX][IP_STR_LEN];
int blacklist_count = 0;
volatile int keep_running = 1;

FILE *log_file; // Global log file pointer

// Mutex for the blacklist
pthread_mutex_t blacklist_mutex = PTHREAD_MUTEX_INITIALIZER;
file_monitor_t blacklist_monitor;

// Function to calculate checksum
unsigned short checksum(void *b, int len) {
    unsigned short *buf = b;
    unsigned int sum = 0;
    for (sum = 0; len > 1; len -= 2) {
        sum += *buf++;
    }
    if (len == 1) {
        sum += *(unsigned char *)buf;
    }
    sum = (sum >> 16) + (sum & 0xFFFF);
    sum += (sum >> 16);
    return ~sum;
}

// Send RST to terminate original connection
void send_tcp_reset(const u_char *packet, int packet_len) {
    struct ip *ip_hdr = (struct ip *)(packet + 14);
    struct tcphdr *tcp_hdr = (struct tcphdr *)(packet + 14 + (ip_hdr->ip_hl * 4));

    int sockfd = socket(AF_INET, SOCK_RAW, IPPROTO_RAW);
    if (sockfd < 0) {
        perror("Socket error");
        return;
    }

    char buffer[4096];
    memset(buffer, 0, sizeof(buffer));

    struct ip *rst_ip_hdr = (struct ip *)buffer;
    struct tcphdr *rst_tcp_hdr = (struct tcphdr *)(buffer + sizeof(struct ip));

    // Build IP header for RST
    rst_ip_hdr->ip_hl = 5;
    rst_ip_hdr->ip_v = 4;
    rst_ip_hdr->ip_tos = 0;
    rst_ip_hdr->ip_len = htons(sizeof(struct ip) + sizeof(struct tcphdr));
    rst_ip_hdr->ip_id = htons(54321);
    rst_ip_hdr->ip_off = 0;
    rst_ip_hdr->ip_ttl = 64;
    rst_ip_hdr->ip_p = IPPROTO_TCP;
    rst_ip_hdr->ip_src = ip_hdr->ip_dst;
    rst_ip_hdr->ip_dst = ip_hdr->ip_src;

    rst_ip_hdr->ip_sum = checksum(rst_ip_hdr, sizeof(struct ip));

    // Build TCP header for RST
    rst_tcp_hdr->source = tcp_hdr->dest;
    rst_tcp_hdr->dest = tcp_hdr->source;
    rst_tcp_hdr->seq = htonl(ntohl(tcp_hdr->ack_seq));
    rst_tcp_hdr->ack_seq = 0;
    rst_tcp_hdr->doff = 5;
    rst_tcp_hdr->rst = 1;
    rst_tcp_hdr->window = htons(0);
    rst_tcp_hdr->check = 0; // Calculate checksum below

    // Compute TCP checksum
    struct {
        struct in_addr src;
        struct in_addr dst;
        uint8_t zero;
        uint8_t protocol;
        uint16_t tcp_len;
    } pseudo_hdr;

    pseudo_hdr.src = ip_hdr->ip_dst;
    pseudo_hdr.dst = ip_hdr->ip_src;
    pseudo_hdr.zero = 0;
    pseudo_hdr.protocol = IPPROTO_TCP;
    pseudo_hdr.tcp_len = htons(sizeof(struct tcphdr));

    char pseudo_packet[sizeof(pseudo_hdr) + sizeof(struct tcphdr)];
    memcpy(pseudo_packet, &pseudo_hdr, sizeof(pseudo_hdr));
    memcpy(pseudo_packet + sizeof(pseudo_hdr), rst_tcp_hdr, sizeof(struct tcphdr));

    rst_tcp_hdr->check = checksum(pseudo_packet, sizeof(pseudo_packet));

    // Destination address
    struct sockaddr_in dest;
    dest.sin_family = AF_INET;
    dest.sin_addr = rst_ip_hdr->ip_dst;

    // Send the packet
    if (sendto(sockfd, buffer, sizeof(struct ip) + sizeof(struct tcphdr), 0, (struct sockaddr *)&dest, sizeof(dest)) < 0) {
        perror("Sendto error");
    }

    close(sockfd);
}

// Signal handler for graceful termination
void handle_signal(int signal) {
    keep_running = 0;
}

// Get file modification time
time_t get_file_mtime(const char *filename) {
    struct stat st;
    if (stat(filename, &st) != 0) {
        return 0;
    }
    return st.st_mtime;
}

// Check if file has been modified
int file_has_changed(file_monitor_t *monitor) {
    time_t current_mtime = get_file_mtime(monitor->filename);
    if (current_mtime > monitor->last_modified) {
        monitor->last_modified = current_mtime;
        return 1;
    }
    return 0;
}

// Function to load blacklist entries from file
void load_blacklist_entries(FILE *file) {
    char ip[IP_STR_LEN];
    blacklist_count = 0;  // Reset count

    while (fgets(ip, sizeof(ip), file) && blacklist_count < BLACKLIST_MAX) {
        ip[strcspn(ip, "\n")] = '\0'; // Remove trailing newline
        strncpy(blacklist[blacklist_count++], ip, IP_STR_LEN);
    }

    fprintf(log_file, "Loaded %d IPs into blacklist\n", blacklist_count);
    fflush(log_file);
}

// Initial load of blacklist file
void load_blacklist(const char *filename) {
    FILE *file = fopen(filename, "r");
    if (!file) {
        perror("Error opening blacklist file");
        exit(EXIT_FAILURE);
    }

    pthread_mutex_lock(&blacklist_mutex);
    load_blacklist_entries(file);
    pthread_mutex_unlock(&blacklist_mutex);

    fclose(file);
}

// Check and reload blacklist if modified
void check_and_reload_blacklist() {
    if (file_has_changed(&blacklist_monitor)) {
        FILE *file = fopen(blacklist_monitor.filename, "r");
        if (file) {
            pthread_mutex_lock(&blacklist_mutex);
            load_blacklist_entries(file);
            pthread_mutex_unlock(&blacklist_mutex);
            fclose(file);
        }
    }
}

// Monitor thread function
void *monitor_blacklist(void *arg) {
    while (keep_running) {
        check_and_reload_blacklist();
        sleep(1); // Check every second
    }
    return NULL;
}

// Check if an IP is blacklisted
int is_blacklisted(const char *ip) {
    int result = 0;
    pthread_mutex_lock(&blacklist_mutex);
    for (int i = 0; i < blacklist_count; i++) {
        if (strcmp(ip, blacklist[i]) == 0) {
            result = 1;
            break;
        }
    }
    pthread_mutex_unlock(&blacklist_mutex);
    return result;
}

// Forward packets between interfaces with blacklist filtering
void *forward_packets(void *args) {
    forwarder_args_t *forward_args = (forwarder_args_t *)args;
    pcap_t *source_handle = forward_args->source_handle;
    pcap_t *dest_handle = forward_args->dest_handle;

    struct pcap_pkthdr header;
    const u_char *packet;

    while (keep_running) {
        packet = pcap_next(source_handle, &header);
        if (packet == NULL) {
            continue; // Handle packet read error or timeout
        }

        // Parse IP header
        struct ip *ip_hdr = (struct ip *)(packet + 14); // Skip Ethernet header
        char src_ip[IP_STR_LEN], dst_ip[IP_STR_LEN];
        inet_ntop(AF_INET, &(ip_hdr->ip_src), src_ip, IP_STR_LEN);
        inet_ntop(AF_INET, &(ip_hdr->ip_dst), dst_ip, IP_STR_LEN);

        // Check blacklist
        if (is_blacklisted(src_ip) || is_blacklisted(dst_ip)) {
            if (ip_hdr->ip_p == IPPROTO_TCP) {
                send_tcp_reset(packet, header.len); // Terminate original connection
            }
            fprintf(log_file, "Blocked packet: SRC=%s DST=%s\n", src_ip, dst_ip);
            fflush(log_file);
            //continue; // Skip forwarding
        }

        // Forward the packet
        if (pcap_sendpacket(dest_handle, packet, header.len) != 0) {
            fprintf(log_file, "Error sending packet: %s\n", pcap_geterr(dest_handle));
            fflush(log_file);
        }
    }

    return NULL;
}

// Get the MTU of an interface
int get_interface_mtu(const char *interface_name) {
    struct ifreq ifr;
    int sockfd = socket(AF_INET, SOCK_DGRAM, 0);
    if (sockfd == -1) {
        fprintf(log_file, "Socket error\n");
        fflush(log_file);
        return -1;
    }

    strncpy(ifr.ifr_name, interface_name, IFNAMSIZ - 1);
    if (ioctl(sockfd, SIOCGIFMTU, &ifr) == -1) {
        fprintf(log_file, "IOCTL error\n");
        fflush(log_file);
        close(sockfd);
        return -1;
    }

    close(sockfd);
    return ifr.ifr_mtu;
}

// Optimize interface settings
void optimize_interface(const char *interface_name) {
    fprintf(log_file, "Optimizing interface %s\n", interface_name);
    fflush(log_file);
    char command[256];
    snprintf(command, sizeof(command), "sudo ethtool -K %s gro off", interface_name);
    system(command);
    snprintf(command, sizeof(command), "sudo ethtool -K %s lro off", interface_name);
    system(command);
    snprintf(command, sizeof(command), "sudo ethtool -C %s rx-usecs 0", interface_name);
    system(command);
}

int main(int argc, char *argv[]) {
    if (argc != 4) {
        fprintf(stderr, "Usage: %s <interface1> <interface2> <blacklist_file>\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    char *interface1 = argv[1];
    char *interface2 = argv[2];
    char *blacklist_file = argv[3];
    char errbuf[ERRBUF_SIZE];

    // Open log file
    log_file = fopen("forwarder.log", "a");
    if (!log_file) {
        perror("Error opening log file");
        exit(EXIT_FAILURE);
    }

    // Load the blacklist
    load_blacklist(blacklist_file);

    // Set up signal handling
    signal(SIGINT, handle_signal);
    signal(SIGTERM, handle_signal);

    // Optimize interfaces
    optimize_interface(interface1);
    optimize_interface(interface2);

    nice(-20); // Set process to high priority

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

    fprintf(log_file, "Forwarding packets between %s and %s...\n", interface1, interface2);
    fflush(log_file);

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

    // Close the log file
    fclose(log_file);

    return 0;
}
