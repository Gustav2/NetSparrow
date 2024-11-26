# Use a base image with development tools
FROM debian:bullseye

# Install necessary packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libpcap-dev \
    ethtool \
    iproute2 \
    nano \
    sudo

# Set the working directory
WORKDIR /app

# Copy the source code
COPY . /app


# Compile the application
RUN gcc -o packet_forwarder test.c -lpcap -pthread

# Entry point
CMD ["./packet_forwarder", "eth1", "eth2", "/shared/blacklist.txt"]
