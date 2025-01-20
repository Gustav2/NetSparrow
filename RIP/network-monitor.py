#!/usr/bin/env python3
import subprocess
import time
import paramiko
import csv
from datetime import datetime

class NetworkMonitor:
    def __init__(self, pi_host, pi_username, pi_password, iperf_server, test_duration=30):
        self.pi_host = pi_host
        self.pi_username = pi_username
        self.pi_password = pi_password
        self.iperf_server = iperf_server
        self.test_duration = test_duration
        self.ssh = None
        self.results_file = f"network_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    def connect_to_pi(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(self.pi_host, username=self.pi_username, password=self.pi_password)

    def get_pi_resources(self):
        # Get CPU usage using mpstat for better accuracy
        cpu_cmd = "which mpstat >/dev/null 2>&1 && mpstat 1 1 | awk '$12 ~ /[0-9.]+/ { print 100 - $12 }' || (vmstat 1 2 | tail -1 | awk '{print 100 - $15}')"
        stdin, stdout, stderr = self.ssh.exec_command(cpu_cmd)
        try:
            cpu_usage = float(stdout.readline().strip())
        except (ValueError, IndexError):
            print("Error reading CPU usage, falling back to basic method")
            stdin, stdout, stderr = self.ssh.exec_command("top -bn1 | grep 'Cpu(s)' | awk '{print $2}'")
            cpu_usage = float(stdout.readline().strip())

        ram_cmd = "free | grep '^Mem:' | awk '{printf \"%.2f\", ($2-$7)/$2*100}'"
        stdin, stdout, stderr = self.ssh.exec_command(ram_cmd)
        try:
            ram_usage = float(stdout.readline().strip())
        except (ValueError, IndexError):
            print("Error reading RAM usage, falling back to basic method")
            stdin, stdout, stderr = self.ssh.exec_command("free | grep '^Mem:' | awk '{print $3/$2*100}'")
            ram_usage = float(stdout.readline().strip())

        return cpu_usage, ram_usage

    def measure_latency(self):
        try:
            ping = subprocess.run(['ping', '-c', '3', self.iperf_server],
                                  capture_output=True, text=True)
            if ping.returncode == 0:
                for line in ping.stdout.split('\n'):
                    if 'avg' in line:
                        return float(line.split('/')[4])
        except Exception as e:
            print(f"Error measuring latency: {e}")
        return None

    def run_iperf_test(self):
        try:
            print(f"Starting iperf3 test to {self.iperf_server}...")
            iperf = subprocess.run([
                'iperf3', '-c', self.iperf_server,
                '-t', str(self.test_duration),
                '-J',  # JSON output
                '-i', '1'  # Output every second
            ], capture_output=True, text=True)

            if iperf.returncode == 0:
                print("iperf3 test completed successfully")
                return iperf.stdout
            else:
                print(f"iperf3 error (return code {iperf.returncode}):")
                print(f"stderr: {iperf.stderr}")
                return None
        except Exception as e:
            print(f"Error running iperf3: {e}")
            return None

    def monitor_network(self, duration=300, interval=5):
        with open(self.results_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Timestamp', 'Bandwidth (Mbps)', 'Latency (ms)',
                             'Pi CPU Usage (%)', 'Pi RAM Usage (%)'])

        start_time = time.time()
        while time.time() - start_time < duration:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            #cpu_usage, ram_usage = self.get_pi_resources()

            cpu_usage, ram_usage = 0, 0

            latency = self.measure_latency()

            iperf_result = self.run_iperf_test()
            bandwidth = None

            if iperf_result:
                try:
                    import json
                    result_json = json.loads(iperf_result)

                    end_stats = result_json['end']

                    bandwidth = end_stats['sum_sent']['bits_per_second'] / 1_000_000

                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Error parsing iperf3 output: {e}")
                    print(f"Raw output: {iperf_result}")

            print(f"\n=== Measurements at {timestamp} ===")
            print(f"Pi CPU Usage: {cpu_usage:.1f}% (real usage excluding I/O wait)")
            print(f"Pi RAM Usage: {ram_usage:.1f}% (excluding cache/buffers)")
            print(f"Latency: {latency:.1f}ms" if latency else "Latency: N/A")
            print(f"Bandwidth: {bandwidth:.1f} Mbps" if bandwidth else "Bandwidth: N/A")
            print("=" * 40)

            with open(self.results_file, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([timestamp, bandwidth, latency,
                                 cpu_usage, ram_usage])

            time.sleep(interval)

    def cleanup(self):
        if self.ssh:
            self.ssh.close()

    def calculate_averages(self):
        import pandas as pd

        try:
            df = pd.read_csv(self.results_file)

            averages = {
                'Bandwidth': df['Bandwidth (Mbps)'].mean(),
                'Latency': df['Latency (ms)'].mean(),
                'CPU Usage': df['Pi CPU Usage (%)'].mean(),
                'RAM Usage': df['Pi RAM Usage (%)'].mean()
            }

            print("\n=== Test Summary ===")
            print(f"Average Bandwidth: {averages['Bandwidth']:.2f} Mbps")
            print(f"Average Latency: {averages['Latency']:.2f} ms")
            print(f"Average CPU Usage: {averages['CPU Usage']:.2f}%")
            print(f"Average RAM Usage: {averages['RAM Usage']:.2f}%")
            print("=" * 40)

        except Exception as e:
            print(f"Error calculating averages: {e}")

def main():
    PI_HOST = "192.168.0.114"
    PI_USERNAME = "pi"
    PI_PASSWORD = "pi1234"
    IPERF_SERVER = "169.254.215.17"

    monitor = NetworkMonitor(PI_HOST, PI_USERNAME, PI_PASSWORD, IPERF_SERVER)

    try:
        #monitor.connect_to_pi()

        print(f"Starting network monitoring. Results will be saved to {monitor.results_file}")
        monitor.monitor_network(duration=600, interval=20)
        monitor.calculate_averages()

    except Exception as e:
        print(f"Error during monitoring: {e}")

    finally:
        monitor.cleanup()
        print("Monitoring completed. Check the CSV file for detailed results.")

if __name__ == "__main__":
    main()