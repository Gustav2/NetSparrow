#!/usr/bin/env python3
import os
import time
import struct
import argparse
import pandas as pd
from ipaddress import ip_address
import signal
import sys

PIPE_NAME = "/tmp/packet_pipe"
MAX_WAIT_TIME = 30  # Maximum time to wait for analyzer in seconds

def ip_string_to_bytes(ip_str):
    """Convert an IP address string to 4 bytes."""
    try:
        return bytes(map(int, ip_str.split('.')))
    except:
        return bytes([0, 0, 0, 0])  # Return placeholder IP if conversion fails

def create_binary_packet(row):
    """Convert a row from the CSV into binary packet format."""
    try:
        timestamp = int(time.time())
        src_ip = ip_string_to_bytes(str(row[2]))
        dst_ip = ip_string_to_bytes(str(row[4]))

        try:
            packet_size = min(int(float(str(row[8]).replace('-', '0'))), 1500)
        except:
            packet_size = 64

        try:
            protocol = int(str(row[6]).replace('-', '0'))
        except:
            protocol = 0

        data = bytes([0] * 1500)

        packet = struct.pack('=L4s4sHB1500s',
                             timestamp,
                             src_ip,
                             dst_ip,
                             packet_size,
                             protocol,
                             data)

        return packet
    except Exception as e:
        print(f"Error creating packet: {e}")
        return None

def cleanup():
    """Clean up pipes."""
    try:
        if os.path.exists(PIPE_NAME):
            os.unlink(PIPE_NAME)
    except Exception as e:
        print(f"Cleanup error: {e}")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\nCleaning up...")
    cleanup()
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="Feed test data through named pipe for packet analysis testing.")
    parser.add_argument("input_file", help="Path to input CSV file containing packet data")
    parser.add_argument("--delay", type=float, default=0.1, help="Delay between packets in seconds (default: 0.1)")
    parser.add_argument("--loop", action="store_true", help="Continuously loop through the input file")
    args = parser.parse_args()

    signal.signal(signal.SIGINT, signal_handler)

    # Clean up any existing pipes
    cleanup()

    # Create the pipe
    try:
        os.mkfifo(PIPE_NAME)
        print(f"Created pipe: {PIPE_NAME}")
    except FileExistsError:
        print(f"Pipe already exists: {PIPE_NAME}")

    print("Starting data feed...")
    time.sleep(1)  # Give the analyzer a moment to prepare

    try:
        start_time = time.time()
        while True:
            try:
                print("Opening pipe for writing...")
                with open(PIPE_NAME, 'wb') as pipe:
                    print(f"Reading data from {args.input_file}...")

                    for chunk in pd.read_csv(args.input_file, header=None, chunksize=1000):
                        for _, row in chunk.iterrows():
                            packet = create_binary_packet(row)
                            if packet:
                                try:
                                    pipe.write(packet)
                                    pipe.flush()
                                    time.sleep(args.delay)
                                except BrokenPipeError:
                                    print("\nAnalyzer process has closed the pipe. Exiting...")
                                    return
                                except IOError as e:
                                    print(f"\nPipe error: {e}")
                                    return

                    if not args.loop:
                        break
                    print("Reached end of file. Restarting...")

            except FileNotFoundError:
                if time.time() - start_time > MAX_WAIT_TIME:
                    print(f"Analyzer did not connect within {MAX_WAIT_TIME} seconds. Exiting...")
                    return
                print("Waiting for analyzer to connect...")
                time.sleep(1)
                continue

    finally:
        cleanup()

if __name__ == "__main__":
    main()