# Use a base image with development tools
FROM debian:bullseye

# Install necessary packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libpcap-dev \
    ethtool \
    iproute2 \
    nano \
    sudo \
    libglib2.0-dev \
    pkg-config

# Set the working directory
WORKDIR /app

# Copy the source code
COPY . /app

# Compile the application
RUN gcc -o packet_forwarder passthrough_test.c -lpcap -pthread `pkg-config --cflags --libs glib-2.0`

# Entry point
CMD ["./packet_forwarder", "eth1", "eth2", "/shared/blacklist.txt", "/shared/settings.txt"]