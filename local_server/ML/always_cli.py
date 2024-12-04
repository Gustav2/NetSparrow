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

INPUT_PIPE_NAME = "/shared/packet_log_pipe"
OUTPUT_PIPE_NAME = "/shared/analysis_pipe"
BATCH_SIZE = 100
MAX_WAIT_TIME = 30
RECONNECT_DELAY = 0.1
ERROR_CHECK_INTERVAL = 0.01
MAX_EMPTY_READS = 500
CONNECTION_TIMEOUT = 5.0
CONFIDENCE_THRESHOLD = 0.9

# Binary format for output: src_ip (4 bytes) + dest_ip (4 bytes) + confidence (4 bytes float)
OUTPUT_FORMAT = "=4s4sf"

class PacketData(NamedTuple):
    timestamp: int
    source_ip: bytes
    dest_ip: bytes
    packet_size: int
    protocol: int
    data: bytes

def cleanup():
    try:
        for pipe in [INPUT_PIPE_NAME, OUTPUT_PIPE_NAME]:
            if os.path.exists(pipe):
                os.unlink(pipe)
    except Exception as e:
        print(f"Cleanup error: {e}")

def signal_handler(sig, frame):
    print("\nCleaning up...")
    cleanup()
    sys.exit(0)

def read_packet(pipe_fd):
    fmt = "=L4s4sHB1500s"
    packet_size = struct.calcsize(fmt)

    try:
        raw_data = os.read(pipe_fd, packet_size)
        if not raw_data:
            return None

        unpacked = struct.unpack(fmt, raw_data)

        hex_data = ' '.join(f"{b:02x}" for b in raw_data)
        print(f"""
            Received packet: {hex_data}
            Src IP: {'.'.join(str(b) for b in unpacked[1])}
            Dest IP: {'.'.join(str(b) for b in unpacked[2])}
            Packet size: {unpacked[3]}
            Protocol: {unpacked[4]}
            Timestamp: {datetime.fromtimestamp(unpacked[0])}
            Timestamp (raw): {unpacked[0]}
            """)



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

def wait_for_pipe(pipe_name, timeout=MAX_WAIT_TIME):
    start_time = time.time()
    while not os.path.exists(pipe_name):
        if time.time() - start_time > timeout:
            return False
        time.sleep(RECONNECT_DELAY)
    return True

def connect_to_pipe(pipe_name, mode, retries=3):
    for attempt in range(retries):
        try:
            if not wait_for_pipe(pipe_name):
                print(f"Timeout waiting for {pipe_name}")
                return None
            
            fd = os.open(pipe_name, mode)
            return fd
        except Exception as e:
            print(f"Connection attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(RECONNECT_DELAY)
            continue
    return None

def create_output_pipe():
    try:
        if not os.path.exists(OUTPUT_PIPE_NAME):
            os.mkfifo(OUTPUT_PIPE_NAME)
        return True
    except Exception as e:
        print(f"Error creating output pipe: {e}")
        return False

def write_packet_data(output_fd, source_ip, dest_ip, confidence):
    try:
        # Pack the IPs and confidence into binary format
        binary_data = struct.pack(OUTPUT_FORMAT, source_ip, dest_ip, float(confidence))
        bytes_written = os.write(output_fd, binary_data)
        return bytes_written > 0
    except BlockingIOError:
        time.sleep(ERROR_CHECK_INTERVAL)
        return False
    except OSError as e:
        if e.errno in (errno.EINTR, errno.EAGAIN):
            time.sleep(ERROR_CHECK_INTERVAL)
            return False
        raise
    except Exception as e:
        print(f"Error writing to output pipe: {e}")
        return False

def packet_to_dataframe(packets):
    rows = []
    for packet in packets:
        src_ip = '.'.join(str(b) for b in packet.source_ip)
        dst_ip = '.'.join(str(b) for b in packet.dest_ip)
        
        row = [
            packet.timestamp,
            None,
            src_ip,
            None,
            dst_ip,
            None,
            packet.protocol,
            None,
            packet.packet_size,
            packet.packet_size,
            len(packet.data),
            "UNKNOWN",
            None,
            None,
            packet.packet_size / 1500.0,
            None,
            packet.packet_size,
            packet.packet_size
        ]
        rows.append(row)

    return pd.DataFrame(rows)

def preprocess_data(data):
    categorical_columns = [6, 11]
    numerical_columns = [8, 9, 10, 14, 16, 17]

    data.iloc[:, numerical_columns] = (
        data.iloc[:, numerical_columns]
        .replace(['-', '(empty)'], 0)
        .apply(pd.to_numeric, errors='coerce')
        .fillna(0)
    )

    data.iloc[:, categorical_columns] = data.iloc[:, categorical_columns].replace(
        ['-', '(empty)'], 'unknown'
    )

    scaler = StandardScaler()
    scaled_numeric = scaler.fit_transform(data.iloc[:, numerical_columns])

    encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
    encoded_categorical = encoder.fit_transform(data.iloc[:, categorical_columns])

    processed_data = pd.concat(
        [
            pd.DataFrame(scaled_numeric, index=data.index),
            pd.DataFrame(encoded_categorical, index=data.index)
        ],
        axis=1
    )

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
    return tf.keras.models.load_model(model_path)

def process_batch(model, packet_buffer, output_fd):
    try:
        data = packet_to_dataframe(packet_buffer)
        preprocessed_data = preprocess_data(data)
        predictions = model.predict(preprocessed_data, verbose=0)
        confidences = predictions.squeeze()

        # Write each packet's IPs to the output pipe in binary format
        for i, packet in enumerate(packet_buffer):
            # Only output if confidence is below threshold
            if not write_packet_data(output_fd, packet.source_ip, packet.dest_ip, confidences[i]):
                return False
        return True
    except Exception as e:
        print(f"Error processing batch: {e}")
        return False

def analyze_packets_stream(model):
    print("Initializing packet analysis...")

    if not create_output_pipe():
        return

    packet_buffer = deque(maxlen=BATCH_SIZE)
    packets_processed = 0
    running = True

    while running:
        try:
            print("\nConnecting to pipes...")
            input_fd = connect_to_pipe(INPUT_PIPE_NAME, os.O_RDONLY | os.O_NONBLOCK)
            if input_fd is None:
                print("Failed to connect to input pipe. Retrying...")
                time.sleep(RECONNECT_DELAY)
                continue

            output_fd = connect_to_pipe(OUTPUT_PIPE_NAME, os.O_WRONLY | os.O_NONBLOCK)
            if output_fd is None:
                os.close(input_fd)
                print("Failed to connect to output pipe. Retrying...")
                time.sleep(RECONNECT_DELAY)
                continue

            print("Connected to pipes. Processing packets...")
            empty_reads = 0
            last_packet_time = time.time()

            while True:
                packet = read_packet(input_fd)

                if packet is None:
                    empty_reads += 1
                    current_time = time.time()
                    
                    if empty_reads >= MAX_EMPTY_READS and (current_time - last_packet_time) > CONNECTION_TIMEOUT:
                        print("\nNo packets received for too long. Reconnecting...")
                        break

                    if empty_reads >= MAX_EMPTY_READS and packet_buffer:
                        if process_batch(model, packet_buffer, output_fd):
                            packets_processed += len(packet_buffer)
                            print(f"\rProcessed {packets_processed} packets", end="", flush=True)
                        packet_buffer.clear()
                    
                    time.sleep(ERROR_CHECK_INTERVAL)
                    continue

                empty_reads = 0
                last_packet_time = time.time()
                packet_buffer.append(packet)

                if len(packet_buffer) >= BATCH_SIZE:
                    if process_batch(model, packet_buffer, output_fd):
                        packets_processed += len(packet_buffer)
                        print(f"\rProcessed {packets_processed} packets", end="", flush=True)
                    packet_buffer.clear()

        except KeyboardInterrupt:
            print("\nShutting down gracefully...")
            running = False
        except Exception as e:
            print(f"\nError in main processing loop: {e}")
            time.sleep(RECONNECT_DELAY)
        finally:
            try:
                if 'input_fd' in locals():
                    os.close(input_fd)
                if 'output_fd' in locals():
                    os.close(output_fd)
            except:
                pass

def main():
    parser = argparse.ArgumentParser(
        description="Analyze network packets in real-time using a pre-trained Keras model."
    )
    parser.add_argument(
        "model",
        type=str,
        help="Path to the trained Keras model file."
    )

    args = parser.parse_args()

    signal.signal(signal.SIGINT, signal_handler)
    #cleanup()

    print("Loading model...")
    model = load_model(args.model)

    print("Starting packet analysis...")
    analyze_packets_stream(model)

if __name__ == "__main__":
    main()
