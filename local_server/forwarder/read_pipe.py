import os

PIPE_PATH = "/tmp/packet_log_pipe"  # Same as in the C program

def main():
    # Ensure the pipe exists
    if not os.path.exists(PIPE_PATH):
        print(f"Error: Pipe {PIPE_PATH} does not exist.")
        return

    print(f"Listening for data on {PIPE_PATH}...")
    try:
        # Open the pipe for reading
        with open(PIPE_PATH, 'r') as pipe:
            while True:
                # Read line by line from the pipe
                line = pipe.readline()
                if line:
                    print(f"Received: {line.strip()}")
                else:
                    # If no data, the writer might have closed the pipe; wait and retry
                    pass
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
