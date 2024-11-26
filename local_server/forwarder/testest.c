#include <pcap.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <netinet/ip.h>
#include <signal.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>

#define SNAP_LEN 1518
#define ERRBUF_SIZE 256
#define BLACKLIST_MAX 2048
#define IP_STR_LEN 16
#define PIPE_PATH "/tmp/packet_log_pipe"

typedef struct {
    pcap_t *source_handle;
    pcap_t *dest_handle;
    int mtu;
} forwarder_args_t;

// Global variables
char *blacklist_file_path;
pthread_mutex_t blacklist_mutex = PTHREAD_MUTEX_INITIALIZER;
time_t last_modified_time = 0;

char blacklist[BLACKLIST_MAX][IP_STR_LEN];
int blacklist_count = 0;
volatile int keep_running = 1;

FILE *log_file; // Log file pointer
int pipe_fd = -1; // Named pipe file descriptor

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

// Signal handler for graceful termination
void handle_signal(int signal) {
    keep_running = 0;
}

// Get file modification time
time_t get_file_modification_time(const char *filename) {
    struct stat file_stat;
    if (stat(filename, &file_stat) == 0) {
        return file_stat.st_mtime;
    }
    return 0;
}

// Load blacklist file into memory
void load_blacklist(const char *filename) {
    FILE *file = fopen(filename, "r");
    if (!file) {
        fprintf(log_file, "Error opening blacklist file: %s\n", filename);
        fflush(log_file);
        return;
    }

    char temp_blacklist[BLACKLIST_MAX][IP_STR_LEN];
    int temp_count = 0;

    char ip[IP_STR_LEN];
    while (fgets(ip, sizeof(ip), file) && temp_count < BLACKLIST_MAX) {
        ip[strcspn(ip, "\n")] = '\0'; // Remove trailing newline
        strncpy(temp_blacklist[temp_count++], ip, IP_STR_LEN);
    }

    fclose(file);

    pthread_mutex_lock(&blacklist_mutex);
    blacklist_count = temp_count;
    memcpy(blacklist, temp_blacklist, sizeof(temp_blacklist));
    pthread_mutex_unlock(&blacklist_mutex);

    fprintf(log_file, "Reloaded blacklist with %d IPs\n", blacklist_count);
    fflush(log_file);
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

void *monitor_blacklist(void *arg) {
    while (keep_running) {
        time_t current_mod_time = get_file_modification_time(blacklist_file_path);

        if (current_mod_time > last_modified_time) {
            fprintf(log_file, "Blacklist file changed, reloading...\n");
            fflush(log_file);
            load_blacklist(blacklist_file_path);
            last_modified_time = current_mod_time;
        }

        sleep(1);
    }
    return NULL;
}

// Log packet details to the named pipe
void packet_to_pipe(const u_char *packet, int packet_len) {
    struct ip *ip_hdr = (struct ip *)(packet + 14); // Skip Ethernet header

    char src_ip[IP_STR_LEN], dst_ip[IP_STR_LEN];
    inet_ntop(AF_INET, &(ip_hdr->ip_src), src_ip, IP_STR_LEN);
    inet_ntop(AF_INET, &(ip_hdr->ip_dst), dst_ip, IP_STR_LEN);

    const char *protocol = (ip_hdr->ip_p == IPPROTO_TCP) ? "TCP" :
                           (ip_hdr->ip_p == IPPROTO_UDP) ? "UDP" :
                           (ip_hdr->ip_p == IPPROTO_ICMP) ? "ICMP" : "Other";

    char data[256];
    int bytes_written = snprintf(data, sizeof(data),
                                 "Source IP: %s, Destination IP: %s, Protocol: %s, Packet Length: %d\n",
                                 src_ip, dst_ip, protocol, packet_len);

    if (pipe_fd != -1) {
        if (write(pipe_fd, data, bytes_written) == -1) {
            if (errno != EAGAIN) {
                fprintf(log_file, "Error writing to pipe: %s\n", strerror(errno));
                fflush(log_file);
            }
        }
    }
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
            continue;
        }

        struct ip *ip_hdr = (struct ip *)(packet + 14); // Skip Ethernet header
        char src_ip[IP_STR_LEN], dst_ip[IP_STR_LEN];
        inet_ntop(AF_INET, &(ip_hdr->ip_src), src_ip, IP_STR_LEN);
        inet_ntop(AF_INET, &(ip_hdr->ip_dst), dst_ip, IP_STR_LEN);

        if (is_blacklisted(src_ip) || is_blacklisted(dst_ip)) {
            fprintf(log_file, "Blocked packet: SRC=%s DST=%s\n", src_ip, dst_ip);
            fflush(log_file);
            continue; // Skip forwarding
        }

        packet_to_pipe(packet, header.len);

        if (pcap_sendpacket(dest_handle, packet, header.len) != 0) {
            fprintf(log_file, "Error sending packet: %s\n", pcap_geterr(dest_handle));
            fflush(log_file);
        }
    }

    return NULL;
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

    blacklist_file_path = argv[3];
    log_file = fopen("forwarder.log", "a");
    if (!log_file) {
        perror("Error opening log file");
        exit(EXIT_FAILURE);
    }

    // Create named pipe
    if (mkfifo(PIPE_PATH, 0666) == -1 && errno != EEXIST) {
        perror("Error creating pipe");
        exit(EXIT_FAILURE);
    }

    // Open pipe for writing
    pipe_fd = open(PIPE_PATH, O_WRONLY | O_NONBLOCK);
    if (pipe_fd == -1) {
        fprintf(stderr, "Error opening pipe: %s\n", strerror(errno));
        exit(EXIT_FAILURE);
    }

    last_modified_time = get_file_modification_time(blacklist_file_path);
    load_blacklist(blacklist_file_path);

    signal(SIGINT, handle_signal);
    signal(SIGTERM, handle_signal);

    pcap_t *handle1 = pcap_create(interface1, errbuf);
    pcap_t *handle2 = pcap_create(interface2, errbuf);

    if (!handle1 || !handle2) {
        fprintf(stderr, "Error creating capture handles: %s\n", errbuf);
        exit(EXIT_FAILURE);
    }

    pcap_t *handles[] = {handle1, handle2};
    for (size_t i = 0; i < 2; i++) {
        pcap_set_snaplen(handles[i], SNAP_LEN);
        pcap_set_promisc(handles[i], 1);
        pcap_set_timeout(handles[i], 10);
        pcap_set_buffer_size(handles[i], 1024 * 1024 * 64);
        pcap_set_immediate_mode(handles[i], 1);

        if (pcap_activate(handles[i]) != 0) {
            fprintf(stderr, "Error activating capture: %s\n", pcap_geterr(handles[i]));
            exit(EXIT_FAILURE);
        }
    }

    pthread_t thread1, thread2, monitor_thread;
    forwarder_args_t args1 = {handle1, handle2, 1500};
    forwarder_args_t args2 = {handle2, handle1, 1500};

    pthread_create(&thread1, NULL, forward_packets, &args1);
    pthread_create(&thread2, NULL, forward_packets, &args2);
    pthread_create(&monitor_thread, NULL, monitor_blacklist, NULL);

    pthread_join(thread1, NULL);
    pthread_join(thread2, NULL);
    pthread_join(monitor_thread, NULL);

    pcap_close(handle1);
    pcap_close(handle2);
    fclose(log_file);
    close(pipe_fd);
    unlink(PIPE_PATH);

    return 0;
}
