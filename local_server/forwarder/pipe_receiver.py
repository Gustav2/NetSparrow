import os

PIPE_PATH = '/tmp/packet_pipe'

def receive_packets():
    # Create the pipe if it doesn't exist
    if not os.path.exists(PIPE_PATH):
        os.mkfifo(PIPE_PATH)
    
    print(f"Opening pipe: {PIPE_PATH}")
    
    try:
        with open(PIPE_PATH, 'r') as pipe:
            print("Pipe opened. Waiting for packets...")
            
            while True:
                packet_data = pipe.readline().strip()
                if packet_data:
                    print(f"Received: {packet_data}")
    
    except KeyboardInterrupt:
        print("\nPacket reception stopped.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        print("Pipe reading terminated.")

if __name__ == "__main__":
    receive_packets()