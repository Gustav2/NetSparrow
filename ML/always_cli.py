import os
import sys
import time
import struct
import argparse
import numpy as np
import pandas as pd
import tensorflow as tf
from collections import deque
from typing import NamedTuple
from datetime import datetime
from sklearn.preprocessing import StandardScaler, OneHotEncoder
import signal
import errno

PIPE_NAME = "/tmp/packet_pipe"
BATCH_SIZE = 100
MAX_WAIT_TIME = 30  # Maximum time to wait for pipe in seconds
RECONNECT_DELAY = 0.1  # Reduced from 1.0 to 0.1 seconds
ERROR_CHECK_INTERVAL = 0.01  # How often to check for errors
MAX_EMPTY_READS = 50  # Number of empty reads before considering connection lost

class PacketData(NamedTuple):
    timestamp: int
    source_ip: bytes
    dest_ip: bytes
    packet_size: int
    protocol: int
    data: bytes

def cleanup():
    """Cleanup function to handle pipe removal."""
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

def read_packet(pipe_fd):
    """Read a single packet from the named pipe."""
    fmt = "=L4s4sHB1500s"
    packet_size = struct.calcsize(fmt)

    try:
        raw_data = os.read(pipe_fd, packet_size)
        if not raw_data:
            return None

        unpacked = struct.unpack(fmt, raw_data)
        return PacketData(
            timestamp=unpacked[0],
            source_ip=unpacked[1],
            dest_ip=unpacked[2],
            packet_size=unpacked[3],
            protocol=unpacked[4],
            data=unpacked[5]
        )
    except BlockingIOError:
        return None
    except OSError as e:
        if e.errno in (errno.EINTR, errno.EAGAIN):
            return None
        raise
    except Exception as e:
        print(f"Error reading packet: {e}")
        return None

def connect_to_pipe():
    """Attempt to connect to the named pipe."""
    start_time = time.time()

    while True:
        try:
            if not os.path.exists(PIPE_NAME):
                if time.time() - start_time > MAX_WAIT_TIME:
                    print(f"\nFeeder did not create pipe within {MAX_WAIT_TIME} seconds.")
                    return None
                print("\rWaiting for feeder to create pipe...", end="", flush=True)
                time.sleep(RECONNECT_DELAY)
                continue

            return os.open(PIPE_NAME, os.O_RDONLY | os.O_NONBLOCK)

        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"\nError connecting to pipe: {e}")
            return None

def packet_to_dataframe(packets):
    """Convert a list of PacketData objects to DataFrame format matching training data."""
    rows = []
    for packet in packets:
        # Convert binary IP addresses to string format
        src_ip = '.'.join(str(b) for b in packet.source_ip)
        dst_ip = '.'.join(str(b) for b in packet.dest_ip)

        # Create a row matching the training data format
        row = [
            packet.timestamp,                    # timestamp
            None,                               # flow_id (if needed)
            src_ip,                             # source_ip
            None,                               # source_port
            dst_ip,                             # dest_ip
            None,                               # dest_port
            packet.protocol,                    # protocol
            None,                               # timestamp_start
            packet.packet_size,                 # bytes
            packet.packet_size,                 # total_bytes
            len(packet.data),                   # payload_bytes
            "UNKNOWN",                          # connection_state
            None,                               # missed_bytes
            None,                               # missed_packets
            packet.packet_size / 1500.0,        # packet_size_avg
            None,                               # payload_size_avg
            packet.packet_size,                 # packet_size_std
            packet.packet_size                  # payload_size_std
        ]
        rows.append(row)

    return pd.DataFrame(rows)

def preprocess_data(data):
    """Preprocess the packet data for the model."""
    categorical_columns = [6, 11]  # protocol and connection state
    numerical_columns = [8, 9, 10, 14, 16, 17]  # duration, bytes, etc.

    # Ensure numerical columns are clean
    data.iloc[:, numerical_columns] = (
        data.iloc[:, numerical_columns]
        .replace(['-', '(empty)'], 0)
        .apply(pd.to_numeric, errors='coerce')
        .fillna(0)
    )

    # Handle categorical columns
    data.iloc[:, categorical_columns] = data.iloc[:, categorical_columns].replace(
        ['-', '(empty)'], 'unknown'
    )

    # Scale numeric data
    scaler = StandardScaler()
    scaled_numeric = scaler.fit_transform(data.iloc[:, numerical_columns])

    # Encode categorical data
    encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
    encoded_categorical = encoder.fit_transform(data.iloc[:, categorical_columns])

    # Combine processed data
    processed_data = pd.concat(
        [
            pd.DataFrame(scaled_numeric, index=data.index),
            pd.DataFrame(encoded_categorical, index=data.index)
        ],
        axis=1
    )

    # Ensure the final shape matches the model's expected input
    required_features = 20
    current_features = processed_data.shape[1]

    if current_features < required_features:
        padding = pd.DataFrame(
            0,
            index=processed_data.index,
            columns=range(required_features - current_features)
        )
        processed_data = pd.concat([processed_data, padding], axis=1)
    elif current_features > required_features:
        processed_data = processed_data.iloc[:, :required_features]

    return processed_data

def load_model(model_path):
    """Load the trained Keras model."""
    return tf.keras.models.load_model(model_path)

def analyze_packets_stream(model, output_file):
    """Analyze packets in real-time from the named pipe."""
    print("Initializing packet analysis...")

    # Initialize packet buffer
    packet_buffer = deque(maxlen=BATCH_SIZE)
    packets_processed = 0
    empty_reads = 0
    last_packet_time = time.time()

    while True:  # Main loop for continuous operation
        print("\nWaiting for packet stream...")
        pipe_fd = connect_to_pipe()

        if pipe_fd is None:
            time.sleep(RECONNECT_DELAY)
            continue

        print("Connected to pipe. Starting analysis...")
        empty_reads = 0
        last_packet_time = time.time()

        try:
            while True:  # Packet processing loop
                packet = read_packet(pipe_fd)

                if packet is None:
                    empty_reads += 1

                    # Check if we've lost connection
                    if empty_reads >= MAX_EMPTY_READS and time.time() - last_packet_time > 0.5:
                        print("\nFeeder disconnected. Waiting for new connection...")
                        break

                    time.sleep(ERROR_CHECK_INTERVAL)
                    continue

                # Reset counters on successful packet read
                empty_reads = 0
                last_packet_time = time.time()

                packet_buffer.append(packet)

                if len(packet_buffer) >= BATCH_SIZE:
                    # Process batch
                    data = packet_to_dataframe(packet_buffer)
                    preprocessed_data = preprocess_data(data)
                    predictions = model.predict(preprocessed_data, verbose=0)
                    confidences = predictions.squeeze()

                    # Create and save output
                    output_data = pd.DataFrame({
                        "timestamp": [p.timestamp for p in packet_buffer],
                        "src_ip": ['.'.join(str(b) for b in p.source_ip) for p in packet_buffer],
                        "dest_ip": ['.'.join(str(b) for b in p.dest_ip) for p in packet_buffer],
                        "confidence": confidences
                    })

                    output_data.to_csv(
                        output_file,
                        mode='a',
                        header=not os.path.exists(output_file),
                        index=False
                    )

                    packets_processed += len(packet_buffer)
                    print(f"\rProcessed {packets_processed} packets", end="", flush=True)
                    packet_buffer.clear()

        except KeyboardInterrupt:
            print("\nShutting down...")
            break
        except Exception as e:
            print(f"\nError in packet processing: {e}")
        finally:
            try:
                os.close(pipe_fd)
            except:
                pass
            cleanup()

def main():
    parser = argparse.ArgumentParser(
        description="Analyze network packets in real-time using a pre-trained Keras model."
    )
    parser.add_argument(
        "model",
        type=str,
        help="Path to the trained Keras model file."
    )
    parser.add_argument(
        "output",
        type=str,
        help="Path to save the output CSV file."
    )

    args = parser.parse_args()

    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)

    # Cleanup any existing pipes at startup
    cleanup()

    print("Loading model...")
    model = load_model(args.model)

    print(f"Starting packet analysis... Results will be saved to {args.output}")
    analyze_packets_stream(model, args.output)

if __name__ == "__main__":
    main()