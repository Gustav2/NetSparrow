/*
 * sniffer.c
 */

#include <netinet/in.h>
#include <netinet/ip_icmp.h>
#include <netinet/tcp.h>
#include <netinet/udp.h>
#include <pcap/pcap.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

int link_hdr_length = 0;
FILE *output_file;

void call_me(u_char *user, const struct pcap_pkthdr *pkthdr,
             const u_char *packetd_ptr) {
  // Move the pointer forward to skip the link layer header
  packetd_ptr += link_hdr_length;
  struct ip *ip_hdr = (struct ip *)packetd_ptr;
  
  // Extract source and destination IP addresses
  char packet_srcip[INET_ADDRSTRLEN]; 
  char packet_dstip[INET_ADDRSTRLEN];           
  strcpy(packet_srcip, inet_ntoa(ip_hdr->ip_src));
  strcpy(packet_dstip, inet_ntoa(ip_hdr->ip_dst));
  
  int packet_id = ntohs(ip_hdr->ip_id),
      packet_ttl = ip_hdr->ip_ttl,
      packet_tos = ip_hdr->ip_tos,
      packet_size = pkthdr->len,
      packet_hlen = ip_hdr->ip_hl;

  // Print basic packet information
  printf("************************************"
         "**************************************\n");
  printf("ID: %d | SRC: %s | DST: %s | TOS: 0x%x | TTL: %d\n", packet_id,
         packet_srcip, packet_dstip, packet_tos, packet_ttl);

  // Extract timestamp
  struct tm *timestamp = localtime(&pkthdr->ts.tv_sec);
  char timestamp_str[64];
  strftime(timestamp_str, sizeof(timestamp_str), "%Y-%m-%d %H:%M:%S", timestamp);

  // Process transport layer protocol
  packetd_ptr += (4 * packet_hlen);
  int protocol_type = ip_hdr->ip_p;

  struct tcphdr *tcp_header;
  struct udphdr *udp_header;
  struct icmp *icmp_header;
  int src_port = 0, dst_port = 0;
  char protocol[8] = "";  // Extended length for "UNKNOWN"
  char flags[6] = "-/-/-"; // Placeholder for TCP flags

  switch (protocol_type) {
    case IPPROTO_TCP:
      strcpy(protocol, "TCP");
      tcp_header = (struct tcphdr *)packetd_ptr;
      src_port = ntohs(tcp_header->th_sport);
      dst_port = ntohs(tcp_header->th_dport);
      snprintf(flags, sizeof(flags), "%c/%c/%c",
               (tcp_header->th_flags & TH_SYN ? 'S' : '-'),
               (tcp_header->th_flags & TH_ACK ? 'A' : '-'),
               (tcp_header->th_flags & TH_URG ? 'U' : '-'));
      printf("PROTO: TCP | FLAGS: %s | SPORT: %d | DPORT: %d |\n", flags, src_port, dst_port);
      break;

    case IPPROTO_UDP:
      strcpy(protocol, "UDP");
      udp_header = (struct udphdr *)packetd_ptr;
      src_port = ntohs(udp_header->uh_sport);
      dst_port = ntohs(udp_header->uh_dport);
      printf("PROTO: UDP | SPORT: %d | DPORT: %d |\n", src_port, dst_port);
      break;

    case IPPROTO_ICMP:
      strcpy(protocol, "ICMP");
      icmp_header = (struct icmp *)packetd_ptr;
      int icmp_type = icmp_header->icmp_type;
      int icmp_code = icmp_header->icmp_code;
      printf("PROTO: ICMP | TYPE: %d | CODE: %d |\n", icmp_type, icmp_code);
      break;

    default:
      // Handle any unrecognized protocol
      strcpy(protocol, "UNKNOWN");
      printf("PROTO: UNKNOWN (protocol number %d)\n", protocol_type);
      break;
  }

  // Print timestamp and packet size
  printf("Timestamp: %s.%06ld\n", timestamp_str, pkthdr->ts.tv_usec);
  printf("Packet Size: %d bytes\n", packet_size);

  // Save information to CSV file
  if (output_file) {
    fprintf(output_file, "%s.%06ld,%d,%s,%s,%s,%d,%d,%d,%s,%d,%d,%s\n",
            timestamp_str, pkthdr->ts.tv_usec, packet_id, packet_srcip, packet_dstip, 
            protocol, packet_tos, packet_ttl, packet_size, flags, src_port, dst_port, protocol);
    fflush(output_file); // Ensure data is written immediately
  }
}

int main(int argc, char const *argv[]) {
  // Set the device for packet capture
  char *device = "wlo1";
  char error_buffer[PCAP_ERRBUF_SIZE];
  int packets_count = 10; // Limit to 10 packets

  // Open the CSV output file
  output_file = fopen("packet_capture.csv", "w");
  if (output_file == NULL) {
    perror("Error opening output file");
    exit(1);
  }

  // Write CSV headers
  fprintf(output_file, "Timestamp,Packet ID,Source IP,Destination IP,Protocol,"
                       "Type of Service,TTL,Packet Size,Flags,Source Port,Destination Port,Protocol\n");

  // Open the device for packet capture
  pcap_t *capdev = pcap_open_live(device, BUFSIZ, 0, 10, error_buffer);
  if (capdev == NULL) {
    printf("ERR: pcap_open_live() %s\n", error_buffer);
    fclose(output_file);
    exit(1);
  }

  // Determine the link layer header length
  int link_hdr_type = pcap_datalink(capdev);
  switch (link_hdr_type) {
    case DLT_NULL:
      link_hdr_length = 4;
      break;
    case DLT_EN10MB:
      link_hdr_length = 14;
      break;
    default:
      link_hdr_length = 0;
  }

  // Start packet capture loop with a limit of 10 packets
  if (pcap_loop(capdev, packets_count, call_me, (u_char *)NULL)) {
    printf("ERR: pcap_loop() failed!\n");
    fclose(output_file);
    exit(1);
  }

  // Close the output file and pcap handle
  fclose(output_file);
  pcap_close(capdev);

  return 0;
}
