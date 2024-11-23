#!/usr/bin/env python3
import os
import sys
import time
import struct
import signal
import errno

PIPE_NAME = "/tmp/analysis_pipe"
RECORD_SIZE = 12  # 4 bytes src_ip + 4 bytes dst_ip + 4 bytes float confidence
RECONNECT_DELAY = 0.1
READ_TIMEOUT = 0.01

def cleanup():
    """Cleanup function."""
    try:
        if os.path.exists(PIPE_NAME):
            os.unlink(PIPE_NAME)
    except Exception as e:
        print(f"Cleanup error: {e}")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\nExiting...")
    sys.exit(0)

def ip_bytes_to_str(ip_bytes):
    """Convert IP address from bytes to string."""
    return '.'.join(str(b) for b in ip_bytes)

def connect_to_pipe():
    """Connect to the named pipe."""
    try:
        if not os.path.exists(PIPE_NAME):
            print(f"Waiting for pipe {PIPE_NAME} to be created...")
            while not os.path.exists(PIPE_NAME):
                time.sleep(RECONNECT_DELAY)
        
        return os.open(PIPE_NAME, os.O_RDONLY | os.O_NONBLOCK)
    except Exception as e:
        print(f"Error connecting to pipe: {e}")
        return None

def read_ip_pairs():
    """Read and display low-confidence IP pairs from the pipe."""
    records_read = 0
    detections_count = 0
    last_detection_time = time.time()
    
    while True:
        pipe_fd = connect_to_pipe()
        if pipe_fd is None:
            time.sleep(RECONNECT_DELAY)
            continue

        try:
            while True:
                try:
                    # Try to read exactly one record
                    data = os.read(pipe_fd, RECORD_SIZE)
                    
                    if not data:
                        # No data available, wait a bit
                        time.sleep(READ_TIMEOUT)
                        
                        # Print periodic status if we've seen detections
                        if detections_count > 0 and time.time() - last_detection_time > 5:
                            print(f"\rProcessed {records_read} packets, found {detections_count} low-confidence packets", 
                                  end="", flush=True)
                        continue
                    
                    if len(data) != RECORD_SIZE:
                        print(f"Warning: Incomplete record received ({len(data)} bytes)")
                        continue

                    # Unpack the binary data
                    src_ip, dst_ip, confidence = struct.unpack("=4s4sf", data)
                    
                    # Convert to readable format
                    src_ip_str = ip_bytes_to_str(src_ip)
                    dst_ip_str = ip_bytes_to_str(dst_ip)
                    
                    # Print the record with confidence score
                    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
                    print(f"[{current_time}] {src_ip_str},{dst_ip_str},{confidence:.4f}")
                    
                    records_read += 1
                    detections_count += 1
                    last_detection_time = time.time()

                except BlockingIOError:
                    # No data available, wait a bit
                    time.sleep(READ_TIMEOUT)
                except OSError as e:
                    if e.errno in (errno.EINTR, errno.EAGAIN):
                        time.sleep(READ_TIMEOUT)
                        continue
                    raise

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\nError reading from pipe: {e}")
            try:
                os.close(pipe_fd)
            except:
                pass
            time.sleep(RECONNECT_DELAY)
        finally:
            try:
                os.close(pipe_fd)
            except:
                pass

def main():
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)

    print("Starting low-confidence packet monitor...")
    print("Monitoring for packets with confidence < 0.95")
    print("Format: [timestamp] source_ip,destination_ip,confidence")
    print("-" * 70)
    
    try:
        read_ip_pairs()
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        print("\nShutting down...")
        if 'detections_count' in locals():
            print(f"Total low-confidence packets detected: {detections_count}")

if __name__ == "__main__":
    main()