#!/usr/bin/env python3
import os
import sys
import time
import struct
import signal
import errno

PIPE_NAME = "/tmp/analysis_pipe"
RECORD_SIZE = 8  # 4 bytes for src_ip + 4 bytes for dst_ip
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
    """Read and display IP pairs from the pipe."""
    records_read = 0
    
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
                        continue
                    
                    if len(data) != RECORD_SIZE:
                        print(f"Warning: Incomplete record received ({len(data)} bytes)")
                        continue

                    # Unpack the binary data
                    src_ip, dst_ip = struct.unpack("=4s4s", data)
                    
                    # Convert to readable format
                    src_ip_str = ip_bytes_to_str(src_ip)
                    dst_ip_str = ip_bytes_to_str(dst_ip)
                    
                    # Print the pair
                    print(f"{src_ip_str},{dst_ip_str}")
                    records_read += 1

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

    print("Starting IP pair reader...")
    print("Format: source_ip,destination_ip")
    print("-" * 40)
    
    try:
        read_ip_pairs()
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        print("\nShutting down...")

if __name__ == "__main__":
    main()