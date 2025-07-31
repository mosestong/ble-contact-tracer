import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
import seaborn as sns
from datetime import datetime, timedelta
import os
import glob

plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def load_raw_packet_data(uploads_dir='uploads'):
    """Aggregates all upload sessions for comprehensive packet analysis across time periods"""
    all_data = []
    upload_files = glob.glob(os.path.join(uploads_dir, 'upload_*.csv'))
    
    if not upload_files:
        print(f"No upload files found in {uploads_dir}/")
        return None
    
    print(f"Found {len(upload_files)} upload files")
    
    for file_path in upload_files:
        try:
            df = pd.read_csv(file_path)
            df['source_file'] = os.path.basename(file_path)
            
            # Extract upload session timestamp for temporal analysis
            filename = os.path.basename(file_path)
            if filename.startswith('upload_'):
                timestamp_str = filename[7:-4]
                try:
                    df['upload_timestamp'] = pd.to_datetime(timestamp_str, format='%Y%m%d_%H%M%S')
                except:
                    print(f"Error parsing timestamp: {timestamp_str}")
                
            all_data.append(df)
            print(f"Loaded {len(df)} packets from {os.path.basename(file_path)}")
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    
    if not all_data:
        return None
    
    combined_df = pd.concat(all_data, ignore_index=True)
    # Convert ESP32 millisecond timestamps to datetime for analysis
    combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'], unit='ms', origin='unix')
    
    print(f"Total packets loaded: {len(combined_df)}")
    return combined_df

def calculate_packet_delivery_metrics(df):
    """Measures packet reception reliability and timing consistency per device to identify signal quality issues"""
    if df is None or df.empty:
        return None
    
    device_stats = []
    
    for device, group in df.groupby('manufacturer_data'):
        total_packets = len(group)
        time_span = (group['timestamp'].max() - group['timestamp'].min()).total_seconds()
        
        # Calculating packet delivery rate over time
        packet_rate = total_packets / time_span if time_span > 0 else 0
        avg_rssi = group['rssi'].mean()
        
        # Packet  delivery intervals
        group_sorted = group.sort_values('timestamp')
        intervals = []
        for i in range(1, len(group_sorted)):
            interval = (group_sorted.iloc[i]['timestamp'] - group_sorted.iloc[i-1]['timestamp']).total_seconds()
            intervals.append(interval)
        
        avg_interval = np.mean(intervals) if intervals else 0
        std_interval = np.std(intervals) if intervals else 0
        
        device_stats.append({
            'manufacturer_data': device,
            'device_name': group['device_name'].iloc[0] if 'device_name' in group.columns else 'Unknown',
            'total_packets': total_packets,
            'time_span_seconds': time_span,
            'packet_rate_pps': packet_rate,
            'avg_rssi': avg_rssi,
            'avg_interval_seconds': avg_interval,
            'std_interval_seconds': std_interval,
            'first_seen': group['timestamp'].min(),
            'last_seen': group['timestamp'].max()
        })
    
    return pd.DataFrame(device_stats)

def calculate_overall_delivery_rate(df):
    """Compares actual vs expected packet reception to quantify system performance against theoretical maximum"""
    if df is None or df.empty:
        return None
    
    # Based on ESP32's 10-second scan interval - this is the theoretical maximum reception rate
    expected_interval = 10  # seconds
    
    total_devices = df['manufacturer_data'].nunique()
    total_time_span = (df['timestamp'].max() - df['timestamp'].min()).total_seconds()
    
    # Theoretical maximum assumes no packet loss every scan cycle
    expected_packets_per_device = total_time_span / expected_interval
    total_expected_packets = expected_packets_per_device * total_devices
    total_actual_packets = len(df)
    
    delivery_rate = total_actual_packets / total_expected_packets if total_expected_packets > 0 else 0
    
    return {
        'total_expected_packets': total_expected_packets,
        'total_actual_packets': total_actual_packets,
        'delivery_rate': delivery_rate,
        'total_devices': total_devices,
        'total_time_span_hours': total_time_span / 3600
    }

def plot_packet_delivery_histogram(device_stats, save_path='plots/packet_delivery_histogram.png'):
    """Plot histogram of packet delivery rates per device"""
    plt.figure(figsize=(10, 6))
    
    plt.hist(device_stats['packet_rate_pps'], bins=20, alpha=0.7, edgecolor='black')
    plt.axvline(device_stats['packet_rate_pps'].mean(), color='red', linestyle='--', 
                label=f'Mean: {device_stats["packet_rate_pps"].mean():.3f} pps')
    plt.axvline(device_stats['packet_rate_pps'].median(), color='green', linestyle='--', 
                label=f'Median: {device_stats["packet_rate_pps"].median():.3f} pps')
    
    plt.xlabel('Packet Rate (packets per second)')
    plt.ylabel('Number of Devices')
    plt.title('Distribution of Packet Delivery Rates per Device')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()

def plot_rssi_vs_packet_rate(device_stats, save_path='plots/rssi_vs_packet_rate.png'):
    """Plot RSSI vs packet delivery rate"""
    plt.figure(figsize=(10, 6))
    
    plt.scatter(device_stats['avg_rssi'], device_stats['packet_rate_pps'], alpha=0.6)
    
    # Add trend line
    z = np.polyfit(device_stats['avg_rssi'], device_stats['packet_rate_pps'], 1)
    p = np.poly1d(z)
    plt.plot(device_stats['avg_rssi'], p(device_stats['avg_rssi']), 
             "r--", alpha=0.8, label=f'Trend line')
    
    # Correlation coefficient quantifies the strength of the relationship
    correlation = device_stats['avg_rssi'].corr(device_stats['packet_rate_pps'])
    plt.text(0.05, 0.95, f'Correlation: {correlation:.3f}', transform=plt.gca().transAxes, 
             bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
    
    plt.xlabel('Average RSSI (dBm)')
    plt.ylabel('Packet Rate (packets per second)')
    plt.title('RSSI vs Packet Delivery Rate')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()

def plot_packet_intervals(device_stats, save_path='plots/packet_intervals.png'):
    """Identifies timing consistency issues"""
    plt.figure(figsize=(10, 6))
    
    plt.hist(device_stats['avg_interval_seconds'], bins=20, alpha=0.7, edgecolor='black')
    plt.axvline(device_stats['avg_interval_seconds'].mean(), color='red', linestyle='--', 
                label=f'Mean: {device_stats["avg_interval_seconds"].mean():.2f} s')
    plt.axvline(10, color='blue', linestyle='--', label='Expected: 10 s')
    
    plt.xlabel('Average Packet Interval (seconds)')
    plt.ylabel('Number of Devices')
    plt.title('Distribution of Packet Intervals')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()

def plot_packet_rate_over_time(df, save_path='plots/packet_rate_over_time.png'):
    """Tracks system performance over time to identify degradation or improvement patterns"""
    # Hourly aggregation reveals temporal patterns in reception quality
    df_hourly = df.set_index('timestamp').resample('1H').size().reset_index()
    df_hourly.columns = ['timestamp', 'packet_count']
    df_hourly['packet_rate_pps'] = df_hourly['packet_count'] / 3600
    
    plt.figure(figsize=(12, 6))
    
    plt.plot(df_hourly['timestamp'], df_hourly['packet_rate_pps'], marker='o', linewidth=2, markersize=4)
    plt.axhline(y=df_hourly['packet_rate_pps'].mean(), color='red', linestyle='--', 
                label=f'Average: {df_hourly["packet_rate_pps"].mean():.3f} pps')
    
    plt.xlabel('Time')
    plt.ylabel('Packet Rate (packets per second)')
    plt.title('Packet Rate Over Time (Hourly)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()

def print_packet_statistics(device_stats, overall_metrics):
    """Provides actionable insights for system optimization and troubleshooting"""
    print("=" * 60)
    print("BLE PACKET DELIVERY ANALYSIS")
    print("=" * 60)
    
    if overall_metrics:
        print("\nOVERALL PACKET METRICS:")
        print(f"Total time span: {overall_metrics['total_time_span_hours']:.2f} hours")
        print(f"Total devices detected: {overall_metrics['total_devices']}")
        print(f"Expected packets: {overall_metrics['total_expected_packets']:.0f}")
        print(f"Actual packets received: {overall_metrics['total_actual_packets']}")
        print(f"Overall delivery rate: {overall_metrics['delivery_rate']:.3f} ({overall_metrics['delivery_rate']*100:.1f}%)")
    
    if device_stats is not None and not device_stats.empty:
        print("\nDEVICE-LEVEL PERFORMANCE:")
        print(f"Number of devices: {len(device_stats)}")
        print(f"Mean packet rate: {device_stats['packet_rate_pps'].mean():.3f} packets/sec")
        print(f"Median packet rate: {device_stats['packet_rate_pps'].median():.3f} packets/sec")
        print(f"Standard deviation: {device_stats['packet_rate_pps'].std():.3f} packets/sec")
        
        print(f"\nSignal Quality Metrics:")
        print(f"Mean RSSI: {device_stats['avg_rssi'].mean():.2f} dBm")
        print(f"Mean packet interval: {device_stats['avg_interval_seconds'].mean():.2f} seconds")
        
        print("\nPERCENTILES (Packet Rate):")
        percentiles = [25, 50, 75, 90, 95, 99]
        for p in percentiles:
            value = np.percentile(device_stats['packet_rate_pps'], p)
            print(f"{p}th percentile: {value:.3f} packets/sec")

def main():
    """Analyzes BLE packet reception performance to optimize contact tracing system reliability"""
    print("Starting BLE Packet Delivery Analysis...")
    
    # Load raw packet data
    df = load_raw_packet_data()
    if df is None:
        print("No data to analyze. Please ensure upload files exist in the 'uploads' directory.")
        return
    
    # Calculate packet delivery metrics
    print("\nCalculating packet delivery metrics...")
    device_stats = calculate_packet_delivery_metrics(df)
    overall_metrics = calculate_overall_delivery_rate(df)
    
    print_packet_statistics(device_stats, overall_metrics)
    
    os.makedirs('plots', exist_ok=True)
    
    print("\nGenerating plots...")
    
    if device_stats is not None and not device_stats.empty:
        plot_packet_delivery_histogram(device_stats)
        plot_rssi_vs_packet_rate(device_stats)
        plot_packet_intervals(device_stats)
    
    plot_packet_rate_over_time(df)
    
    if device_stats is not None:
        device_stats.to_csv('plots/packet_analysis_results.csv', index=False)
        print("\nDetailed packet analysis saved to: plots/packet_analysis_results.csv")
    
    print("\nPacket analysis complete! All plots saved to the 'plots' directory.")

if __name__ == "__main__":
    main() 