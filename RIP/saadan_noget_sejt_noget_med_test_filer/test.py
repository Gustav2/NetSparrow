import os
import struct
import time
from datetime import datetime
import ipaddress

class PacketData:
    def __init__(self):
        self.timestamp = 0
        self.source_ip = None
        self.dest_ip = None
        self.packet_size = 0
        self.protocol = 0
        self.data = bytes()

    @classmethod
    def from_bytes(cls, data):
        packet = cls()
        
        # Unpack the fixed-length fields
        # unsigned long (8 bytes), 8 bytes for IPs, unsigned short (2 bytes), unsigned char (1 byte)
        header_format = "=Q4B4BHB"
        header_size = struct.calcsize(header_format)
        
        header_data = struct.unpack(header_format, data[:header_size])
        
        packet.timestamp = header_data[0]
        packet.source_ip = ipaddress.IPv4Address(bytes(header_data[1:5]))
        packet.dest_ip = ipaddress.IPv4Address(bytes(header_data[5:9]))
        packet.packet_size = header_data[9]
        packet.protocol = header_data[10]
        
        # Get the variable length data portion
        packet.data = data[header_size:header_size + packet.packet_size]
        
        return packet

def read_packets(pipe_path="/tmp/packet_pipe"):
    # Create the pipe if it doesn't exist
    if not os.path.exists(pipe_path):
        os.mkfifo(pipe_path)
    
    print(f"Opening pipe for reading: {pipe_path}")
    
    try:
        while True:
            # Open the pipe for reading
            with open(pipe_path, "rb") as pipe:
                print("Pipe opened, waiting for data...")
                
                while True:
                    # Read the entire packet structure
                    # Size is 8 + 4 + 4 + 2 + 1 + 1500 = 1519 bytes
                    raw_data = pipe.read(1519)
                    
                    if not raw_data:
                        break
                    
                    # Parse the packet
                    packet = PacketData.from_bytes(raw_data)
                    
                    # Print packet information
                    print("\nPacket received:")
                    print(f"Timestamp: {datetime.fromtimestamp(packet.timestamp)}")
                    print(f"Source IP: {packet.source_ip}")
                    print(f"Destination IP: {packet.dest_ip}")
                    print(f"Packet Size: {packet.packet_size} bytes")
                    print(f"Protocol: {packet.protocol}")
                    
                    # Print first few bytes of data if available
                    if packet.data:
                        print("Data preview (first 16 bytes):", 
                              ' '.join(f'{b:02x}' for b in packet.data[:16]))
                    
    except KeyboardInterrupt:
        print("\nReader stopped by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Closing reader")

if __name__ == "__main__":
    read_packets()