import sys

def main():
    print("Python script is now reading from the pipe. Press Ctrl+C to terminate.")
    try:
        for line in sys.stdin:
            # Strip any extra whitespace or newlines
            data = line.strip()
            
            # Print the data received from the pipe to the terminal
            print(f"Received from pipe: {data}")
    except KeyboardInterrupt:
        print("\nTerminating script...")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
