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
#include <sys/types.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/inotify.h>   
#include <glib.h> // For hash table
#include <arpa/inet.h> // For inet_pton

#define SNAP_LEN 1518
#define ERRBUF_SIZE 256
#define BLACKLIST_MAX 2048
#define IP_STR_LEN 16
#define BATCH_SIZE 32
#define PIPE_PATH "/shared/packet_log_pipe" // Define the pipe path
#define BUFFER_SIZE 256

typedef struct __attribute__((packed)) {
    uint32_t timestamp;      // Network byte order
    uint8_t src_ip[4];      // Raw IP bytes
    uint8_t dst_ip[4];      // Raw IP bytes
    uint16_t packet_size;    // Network byte order
    uint8_t protocol;       // Protocol number
    uint8_t data[1500];     // Raw packet data
} binary_packet_t;

typedef struct {
    pcap_t *source_handle;
    pcap_t *dest_handle;
    int mtu;
} forwarder_args_t;

GHashTable *blacklist_set; 
char *blacklist_file_path;
char *settings_file_path;
pthread_mutex_t blacklist_mutex = PTHREAD_MUTEX_INITIALIZER;
time_t last_blacklist_modified_time = 0;
time_t last_settings_modified_time = 0;
int mlPercentage = 100;

char blacklist[BLACKLIST_MAX][IP_STR_LEN];
int blacklist_count = 0;
volatile int keep_running = 1;

FILE *log_file; // Global log file pointer
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

int is_valid_ip(const char *ip) {
    struct sockaddr_in sa;
    return inet_pton(AF_INET, ip, &(sa.sin_addr)) == 1;
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

// Function to get file modification time
time_t get_file_modification_time(const char *filename) {
    struct stat file_stat;
    if (stat(filename, &file_stat) == 0) {
        return file_stat.st_mtime;
    }
    return 0;
}

// Load blacklist file into memory
/*
void load_blacklist(const char *filename) {
    FILE *file = fopen(filename, "r");
    if (!file) {
        fprintf(log_file, "Error opening blacklist file: %s\n", filename);
        fflush(log_file);
        return;
    }

    // Create temporary array for new IPs
    char temp_blacklist[BLACKLIST_MAX][IP_STR_LEN];
    int temp_count = 0;

    char ip[IP_STR_LEN];
    while (fgets(ip, sizeof(ip), file) && temp_count < BLACKLIST_MAX) {
        ip[strcspn(ip, "\n")] = '\0'; // Remove trailing newline
        strncpy(temp_blacklist[temp_count++], ip, IP_STR_LEN);
    }

    fclose(file);

    // Lock mutex before updating the blacklist
    pthread_mutex_lock(&blacklist_mutex);

    // Update the blacklist
    blacklist_count = temp_count;
    memcpy(blacklist, temp_blacklist, sizeof(temp_blacklist));

    pthread_mutex_unlock(&blacklist_mutex);

    fprintf(log_file, "Reloaded blacklist with %d IPs\n", blacklist_count);
    fflush(log_file);
}
*/

void load_blacklist_to_hash(const char *filename) {
    FILE *file = fopen(filename, "r");
    if (!file) {
        fprintf(log_file, "Error opening blacklist file: %s\n", filename);
        fflush(log_file);
        return;
    }

    GHashTable *new_blacklist_set = g_hash_table_new(g_str_hash, g_str_equal);

    char ip[IP_STR_LEN];
    while (fgets(ip, sizeof(ip), file)) {
        ip[strcspn(ip, "\n")] = '\0'; // Remove trailing newline
        if (is_valid_ip(ip)) {
            g_hash_table_add(new_blacklist_set, g_strdup(ip));
        }
    }

    fclose(file);

    pthread_mutex_lock(&blacklist_mutex);
    if (blacklist_set) {
        g_hash_table_destroy(blacklist_set);
    }
    blacklist_set = new_blacklist_set;
    pthread_mutex_unlock(&blacklist_mutex);

    fprintf(log_file, "Reloaded blacklist with %d IPs\n", g_hash_table_size(blacklist_set));
    fflush(log_file);
}

// for loading settings
void load_settings(const char *filename) {
    FILE *file = fopen(filename, "r");
    if (!file) {
        fprintf(log_file, "Error opening settings file: %s\n", filename);
        fflush(log_file);
        return;
    }

    char line[256];
    char key[256];
    int value;

    while (fgets(line, sizeof(line), file)) {
        if (sscanf(line, "%[^=]=%d", key, &value) == 2) {
            key[strcspn(key, " \t\n")] = 0;

            if (strcmp(key, "mlPercentage") == 0) {
                if (value >= 0 && value <= 100) {
                    mlPercentage = value;
                    fprintf(log_file, "Settings: mlPercentage updated to: %d\n", value);
                }
                else {
                    fprintf(log_file, "Settings: Invalid mlPercentage %d\n", value);
                }
            }
            // more settings can be added here following the above example
        }
    }
    fclose(file);
    fflush(log_file);
}

// Check if an IP is blacklisted
/*
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
*/

int is_blacklisted(const char *ip) {
    int result = 0;

    pthread_mutex_lock(&blacklist_mutex);
    if (blacklist_set && g_hash_table_contains(blacklist_set, ip)) {
        result = 1;
    }
    pthread_mutex_unlock(&blacklist_mutex);

    return result;
}

/*
void *monitor_blacklist(void *arg) {
    while (keep_running) {
        time_t current_mod_time = get_file_modification_time(blacklist_file_path);
        if (current_mod_time > last_blacklist_modified_time) {
            fprintf(log_file, "Blacklist file changed, reloading...\n");
            fflush(log_file);
            load_blacklist(blacklist_file_path);
            last_blacklist_modified_time = current_mod_time;
        }

        time_t current_settings_time = get_file_modification_time(settings_file_path);
        if (current_settings_time > last_settings_modified_time) {
            fprintf(log_file, "Settings file changed, reloading...\n");
            fflush(log_file);
            load_settings(settings_file_path);
            last_settings_modified_time = current_settings_time;
        }
        sleep(1); // Check every second
    }
    return NULL;
}
*/  

void *monitor_blacklist(void *arg) {
    while (keep_running) {
        // Monitor blacklist file
        time_t current_mod_time = get_file_modification_time(blacklist_file_path);
        if (current_mod_time == -1) {
            fprintf(log_file, "Blacklist file not found or inaccessible: %s\n", blacklist_file_path);
            fflush(log_file);
        } else if (current_mod_time > last_blacklist_modified_time) {
            // Debounce: Reload only if at least 5 second has passed since the last reload
            if (current_mod_time - last_blacklist_modified_time > 5) {
                fprintf(log_file, "Blacklist file changed, reloading...\n");
                fflush(log_file);
                load_blacklist_to_hash(blacklist_file_path);
                last_blacklist_modified_time = current_mod_time;
            }
        }

        // Monitor settings file (similar logic as blacklist monitoring)
        time_t current_settings_time = get_file_modification_time(settings_file_path);
        if (current_settings_time == -1) {
            fprintf(log_file, "Settings file not found or inaccessible: %s\n", settings_file_path);
            fflush(log_file);
        } else if (current_settings_time > last_settings_modified_time) {
            if (current_settings_time - last_settings_modified_time > 1) {
                fprintf(log_file, "Settings file changed, reloading...\n");
                fflush(log_file);
                load_settings(settings_file_path);
                last_settings_modified_time = current_settings_time;
            }
        }

        sleep(1); // Check every second
    }
    return NULL;
}



// Add function to send packet data through pipe
void packet_to_pipe(const u_char *packet, int packet_len) {
    struct ip *ip_hdr = (struct ip *)(packet + 14); // Skip Ethernet header
    binary_packet_t binary_packet;

    // Zero out the structure
    memset(&binary_packet, 0, sizeof(binary_packet_t));

    // Fill structure with network byte order
    binary_packet.timestamp = htonl((uint32_t)time(NULL));
    memcpy(binary_packet.src_ip, &(ip_hdr->ip_src), 4);
    memcpy(binary_packet.dst_ip, &(ip_hdr->ip_dst), 4);
    binary_packet.packet_size = htons((uint16_t)packet_len);
    binary_packet.protocol = ip_hdr->ip_p;

    // Copy packet data (limited to 1500 bytes)
    size_t data_len = packet_len > sizeof(binary_packet.data) ?
                      sizeof(binary_packet.data) : packet_len;
    memcpy(binary_packet.data, packet, data_len);

    // Write to pipe with error handling
    if (pipe_fd != -1) {
        ssize_t written = write(pipe_fd, &binary_packet, sizeof(binary_packet_t));
        if (written != sizeof(binary_packet_t)) {
            char timestamp[64];
            time_t now = time(NULL);
            struct tm *tm_info = localtime(&now);

            // Format the timestamp as YYYY-MM-DD HH:MM:SS
            strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", tm_info);

            // Log the error with the timestamp
            // fprintf(log_file, "[%s] Pipe write error: %s\n", timestamp, strerror(errno));
            fflush(log_file);
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
            continue; // Skip forwarding
        }

        // Log packet data to the ML system via stdout
        double random_value = (double)rand() / RAND_MAX * 100;
        if (random_value < mlPercentage) {
            // Send the packet to the ML system
            packet_to_pipe(packet, header.len);

            // fprintf(log_file, "Package sent to ML system at a percentage of: %i\n", mlPercentage);
            fflush(log_file);
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
    if (argc != 5) {
        fprintf(stderr, "Usage: %s <interface1> <interface2> <blacklist_file> <settings_file>\n", argv[0]);
        exit(EXIT_FAILURE);
    }
    printf("Test");
    fprintf(stderr, "hej");
    char *interface1 = argv[1];
    char *interface2 = argv[2];
    char *blacklist_file_path = argv[3];
    settings_file_path = argv[4];
    char errbuf[ERRBUF_SIZE];
    int fd; // Declare globally without initialization
    int wd; // Declare globally without initialization

    fd = inotify_init();
    if (fd < 0) {
        perror("inotify_init");
        return NULL; // Or handle the error as needed
    }

    wd = inotify_add_watch(fd, blacklist_file_path, IN_MODIFY | IN_CREATE | IN_DELETE);
    if (wd < 0) {
        perror("inotify_add_watch");
        close(fd);
        return NULL; // Or handle the error as needed
    }

    // Open log file
    log_file = fopen("/shared/forwarder_logs/forwarder.log", "a");
    if (!log_file) {
        perror("Error opening log file");
        exit(EXIT_FAILURE);
    }

     // Create the named pipe and handle potential errors
    if (mkfifo(PIPE_PATH, 0666) == -1) {
        if (errno != EEXIST) {
            fprintf(stderr, "Error creating named pipe '%s': %s\n", PIPE_PATH, strerror(errno));
            exit(EXIT_FAILURE);
        } else {
            fprintf(log_file, "Named pipe '%s' already exists, proceeding...\n", PIPE_PATH);
            fflush(log_file);
        }
    }
    FILE *pipe_file = fopen(PIPE_PATH, "w");
    if (pipe_file == NULL) {
        perror("Error opening pipe");
        return 1;
    }

    // Open the pipe for writing in non-blocking mode
    pipe_fd = open(PIPE_PATH, O_WRONLY | O_NONBLOCK);
    if (pipe_fd == -1) {
        fprintf(stderr, "Error opening named pipe '%s': %s\n", PIPE_PATH, strerror(errno));
        fclose(log_file);  // Clean up
        exit(EXIT_FAILURE);
    }

    // Get initial modification time
    last_blacklist_modified_time = get_file_modification_time(blacklist_file_path);
    last_settings_modified_time = get_file_modification_time(settings_file_path);

    // Load the blacklist
    load_blacklist_to_hash(blacklist_file_path);

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

    // Create monitoring thread
    pthread_t monitor_thread;
    if (pthread_create(&monitor_thread, NULL, monitor_blacklist, NULL) != 0) {
        fprintf(stderr, "Error creating monitoring thread\n");
        exit(EXIT_FAILURE);
    }

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
    pthread_join(monitor_thread, NULL);
    pthread_mutex_destroy(&blacklist_mutex);

    pcap_close(handle1);
    pcap_close(handle2);

    // Close the pipe before exiting
    close(pipe_fd);
    unlink(PIPE_PATH);

    // Close the log file
    fclose(log_file);

    return 0;
}