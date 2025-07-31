#!/usr/bin/env python3
"""
Network Simulation Utilities for E2E Testing
Simulates realistic network scenarios and device behaviors
"""

import time
import random
import threading
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from .dns_client import DNSClient, DNSQueryResult

class DeviceType(Enum):
    """Types of network devices"""
    SMARTPHONE = "smartphone"
    LAPTOP = "laptop"
    TABLET = "tablet"
    SMART_TV = "smart_tv"
    GAMING_CONSOLE = "gaming_console"
    IOT_DEVICE = "iot_device"
    DESKTOP = "desktop"

@dataclass
class NetworkDevice:
    """Represents a network device with browsing patterns"""
    name: str
    device_type: DeviceType
    mac_address: str
    ip_address: str
    user_agent: str
    browsing_domains: List[str]
    query_frequency: float = 2.0  # Average seconds between queries
    activity_hours: tuple = (6, 23)  # Active hours (6 AM to 11 PM)
    weekend_behavior: bool = True  # Different behavior on weekends
    parental_controls: bool = False  # Subject to parental filtering

@dataclass 
class NetworkSession:
    """Represents a browsing session"""
    device: NetworkDevice
    start_time: float
    end_time: Optional[float] = None
    queries_made: List[DNSQueryResult] = field(default_factory=list)
    bytes_saved: float = 0.0  # Estimated bandwidth saved from blocking
    time_saved: float = 0.0   # Estimated time saved from blocking

class NetworkSimulator:
    """Simulates realistic network traffic patterns"""
    
    def __init__(self, dns_client: DNSClient):
        self.dns_client = dns_client
        self.devices: List[NetworkDevice] = []
        self.active_sessions: List[NetworkSession] = []
        self.simulation_running = False
        self.total_stats = {
            'total_queries': 0,
            'blocked_queries': 0,
            'allowed_queries': 0,
            'error_queries': 0,
            'total_bandwidth_saved': 0.0,
            'total_time_saved': 0.0
        }
    
    def add_device(self, device: NetworkDevice):
        """Add a device to the network simulation"""
        self.devices.append(device)
    
    def create_family_network(self) -> List[NetworkDevice]:
        """Create a realistic family network with typical devices"""
        family_devices = [
            NetworkDevice(
                name="Dad's iPhone",
                device_type=DeviceType.SMARTPHONE,
                mac_address="02:00:00:00:01:01",
                ip_address="192.168.1.101",
                user_agent="iPhone13,1",
                browsing_domains=[
                    "cnn.com", "bbc.com", "reuters.com",  # News
                    "googlesyndication.com", "doubleclick.net",  # Ads
                    "amazon.com", "amazon-adsystem.com",  # Shopping
                    "linkedin.com", "salesforce.com",  # Work
                    "googletagmanager.com", "scorecardresearch.com"  # Tracking
                ],
                query_frequency=1.5
            ),
            NetworkDevice(
                name="Mom's Laptop",
                device_type=DeviceType.LAPTOP,
                mac_address="02:00:00:00:01:02", 
                ip_address="192.168.1.102",
                user_agent="Chrome/91.0",
                browsing_domains=[
                    "pinterest.com", "etsy.com", "target.com",  # Shopping
                    "facebook.com", "instagram.com",  # Social
                    "googlesyndication.com", "doubleclick.com",  # Ads
                    "healthline.com", "webmd.com",  # Health
                    "googletagmanager.com", "facebook.com"  # Tracking
                ],
                query_frequency=2.0
            ),
            NetworkDevice(
                name="Teen's Gaming PC",
                device_type=DeviceType.DESKTOP,
                mac_address="02:00:00:00:01:03",
                ip_address="192.168.1.103", 
                user_agent="Steam/Gaming",
                browsing_domains=[
                    "steam.com", "epicgames.com", "twitch.tv",  # Gaming
                    "youtube.com", "googlesyndication.com",  # Entertainment
                    "discord.com", "reddit.com",  # Social
                    "tiktok.com", "doubleclick.net",  # Social/Ads
                    "googletagmanager.com"  # Tracking
                ],
                query_frequency=1.0,
                activity_hours=(14, 24)  # 2 PM to midnight
            ),
            NetworkDevice(
                name="Kids' Tablet",
                device_type=DeviceType.TABLET,
                mac_address="02:00:00:00:01:04",
                ip_address="192.168.1.104",
                user_agent="iPad",
                browsing_domains=[
                    "pbskids.org", "disney.com", "roblox.com",  # Kids content
                    "youtube.com", "googlesyndication.com",  # Entertainment
                    "minecraft.net", "scratch.mit.edu",  # Educational games
                    "doubleclick.net", "googletagmanager.com"  # Ads/Tracking
                ],
                query_frequency=3.0,
                activity_hours=(7, 20),  # 7 AM to 8 PM
                parental_controls=True
            ),
            NetworkDevice(
                name="Smart TV",
                device_type=DeviceType.SMART_TV,
                mac_address="02:00:00:00:01:05",
                ip_address="192.168.1.105",
                user_agent="Samsung_TV",
                browsing_domains=[
                    "netflix.com", "hulu.com", "primevideo.com",  # Streaming
                    "youtube.com", "googlesyndication.com",  # Entertainment
                    "roku.com", "chromecast.com",  # Casting
                    "doubleclick.net", "googletagmanager.com"  # Ads/Tracking
                ],
                query_frequency=5.0  # Less frequent queries
            ),
            NetworkDevice(
                name="Smart Thermostat",
                device_type=DeviceType.IOT_DEVICE,
                mac_address="02:00:00:00:01:06",
                ip_address="192.168.1.106",
                user_agent="Nest/IoT",
                browsing_domains=[
                    "nest.com", "google.com",  # Service
                    "time.google.com", "pool.ntp.org",  # Time sync
                    "googletagmanager.com"  # Tracking (unfortunately)
                ],
                query_frequency=30.0  # Very infrequent
            )
        ]
        
        for device in family_devices:
            self.add_device(device)
        
        return family_devices
    
    def create_business_network(self) -> List[NetworkDevice]:
        """Create a realistic small business network"""
        business_devices = [
            NetworkDevice(
                name="Reception Laptop",
                device_type=DeviceType.LAPTOP,
                mac_address="02:00:00:00:02:01",
                ip_address="192.168.1.201",
                user_agent="Chrome/Business",
                browsing_domains=[
                    "office.com", "outlook.com", "microsoft.com",  # Productivity
                    "googlesyndication.com", "doubleclick.net",  # Ads (unfortunately)
                    "salesforce.com", "hubspot.com",  # CRM
                    "googletagmanager.com", "amazon-adsystem.com"  # Tracking
                ],
                query_frequency=1.5,
                activity_hours=(8, 18)  # Business hours
            ),
            NetworkDevice(
                name="Manager Phone",
                device_type=DeviceType.SMARTPHONE,
                mac_address="02:00:00:00:02:02",
                ip_address="192.168.1.202",
                user_agent="iPhone/Business",
                browsing_domains=[
                    "linkedin.com", "email.com", "zoom.us",  # Business
                    "googlesyndication.com", "facebook.com",  # Ads/Social
                    "news.com", "reuters.com",  # News
                    "doubleclick.com", "scorecard Research.com"  # Tracking
                ],
                query_frequency=2.0
            ),
            NetworkDevice(
                name="Conference Room TV",
                device_type=DeviceType.SMART_TV,
                mac_address="02:00:00:00:02:03",
                ip_address="192.168.1.203",
                user_agent="Business_Display",
                browsing_domains=[
                    "zoom.us", "teams.microsoft.com", "webex.com",  # Video conf
                    "googlesyndication.com", "doubleclick.net",  # Ads
                    "youtube.com",  # Presentations
                    "googletagmanager.com"  # Tracking
                ],
                query_frequency=10.0,
                activity_hours=(8, 18)
            )
        ]
        
        for device in business_devices:
            self.add_device(device)
        
        return business_devices
    
    def simulate_device_activity(self, device: NetworkDevice, duration: float, 
                                callback: Optional[Callable] = None) -> NetworkSession:
        """Simulate browsing activity for a single device"""
        session = NetworkSession(device=device, start_time=time.time())
        
        end_time = time.time() + duration
        
        while time.time() < end_time and self.simulation_running:
            # Check if device should be active based on time
            current_hour = time.localtime().tm_hour
            if not (device.activity_hours[0] <= current_hour <= device.activity_hours[1]):
                time.sleep(60)  # Sleep for a minute if outside active hours
                continue
            
            # Select a random domain from device's browsing pattern
            domain = random.choice(device.browsing_domains)
            
            # Perform DNS query
            result = self.dns_client.query(domain)
            session.queries_made.append(result)
            
            # Update statistics
            self.total_stats['total_queries'] += 1
            
            if result.status == "BLOCKED":
                self.total_stats['blocked_queries'] += 1
                # Estimate bandwidth and time savings
                session.bytes_saved += 2.5  # Estimate 2.5MB per blocked ad
                session.time_saved += 0.5   # Estimate 500ms per blocked ad
                
                if callback:
                    callback(f"[{device.name}] BLOCKED {domain} ({result.response_time_ms:.1f}ms)")
                    
            elif result.status == "ALLOWED":
                self.total_stats['allowed_queries'] += 1
                
            else:
                self.total_stats['error_queries'] += 1
            
            # Wait for next query based on device frequency
            sleep_time = random.expovariate(1.0 / device.query_frequency)
            time.sleep(min(sleep_time, 30))  # Cap at 30 seconds
        
        session.end_time = time.time()
        self.total_stats['total_bandwidth_saved'] += session.bytes_saved
        self.total_stats['total_time_saved'] += session.time_saved
        
        return session
    
    def run_network_simulation(self, duration: float = 120, 
                              progress_callback: Optional[Callable] = None) -> Dict:
        """Run a complete network simulation with all devices"""
        
        if not self.devices:
            raise ValueError("No devices added to simulation")
        
        self.simulation_running = True
        self.total_stats = {
            'total_queries': 0,
            'blocked_queries': 0, 
            'allowed_queries': 0,
            'error_queries': 0,
            'total_bandwidth_saved': 0.0,
            'total_time_saved': 0.0
        }
        
        if progress_callback:
            progress_callback(f"Starting network simulation with {len(self.devices)} devices for {duration} seconds")
        
        # Start simulation threads for each device
        threads = []
        sessions = []
        
        for device in self.devices:
            def device_simulation(dev=device):
                session = self.simulate_device_activity(dev, duration, progress_callback)
                sessions.append(session)
            
            thread = threading.Thread(target=device_simulation, daemon=True)
            thread.start()
            threads.append(thread)
            
            # Stagger device starts
            time.sleep(0.5)
        
        # Wait for all devices to complete
        for thread in threads:
            thread.join()
        
        self.simulation_running = False
        
        # Calculate final statistics
        total_queries = self.total_stats['total_queries']
        blocked_rate = (self.total_stats['blocked_queries'] / max(total_queries, 1)) * 100
        success_rate = ((self.total_stats['blocked_queries'] + self.total_stats['allowed_queries']) / max(total_queries, 1)) * 100
        
        return {
            'duration': duration,
            'devices_simulated': len(self.devices),
            'sessions': sessions,
            'total_queries': total_queries,
            'blocked_queries': self.total_stats['blocked_queries'],
            'allowed_queries': self.total_stats['allowed_queries'],
            'error_queries': self.total_stats['error_queries'],
            'block_rate_percent': round(blocked_rate, 1),
            'success_rate_percent': round(success_rate, 1),
            'total_bandwidth_saved_mb': round(self.total_stats['total_bandwidth_saved'], 1),
            'total_time_saved_seconds': round(self.total_stats['total_time_saved'], 1),
            'queries_per_second': round(total_queries / duration, 2) if duration > 0 else 0
        }
    
    def generate_report(self, simulation_results: Dict) -> str:
        """Generate a formatted report of simulation results"""
        report_lines = []
        
        report_lines.append("GuardNet Network Simulation Report")
        report_lines.append("=" * 50)
        report_lines.append(f"Duration: {simulation_results['duration']} seconds")
        report_lines.append(f"Devices: {simulation_results['devices_simulated']}")
        report_lines.append("")
        
        report_lines.append("DNS Query Statistics:")
        report_lines.append(f"  Total Queries: {simulation_results['total_queries']}")
        report_lines.append(f"  Blocked (Ads/Threats): {simulation_results['blocked_queries']}")
        report_lines.append(f"  Allowed (Content): {simulation_results['allowed_queries']}")
        report_lines.append(f"  Errors: {simulation_results['error_queries']}")
        report_lines.append(f"  Block Rate: {simulation_results['block_rate_percent']}%")
        report_lines.append(f"  Success Rate: {simulation_results['success_rate_percent']}%")
        report_lines.append(f"  Queries/Second: {simulation_results['queries_per_second']}")
        report_lines.append("")
        
        report_lines.append("User Benefits:")
        report_lines.append(f"  Bandwidth Saved: {simulation_results['total_bandwidth_saved_mb']} MB")
        report_lines.append(f"  Time Saved: {simulation_results['total_time_saved_seconds']} seconds")
        report_lines.append(f"  Privacy Enhanced: Tracking blocked")
        report_lines.append(f"  Family Protected: Threats blocked")
        report_lines.append("")
        
        report_lines.append("Network Performance:")
        avg_response_time = 0
        if simulation_results['sessions']:
            all_queries = []
            for session in simulation_results['sessions']:
                all_queries.extend(session.queries_made)
            
            if all_queries:
                successful_queries = [q for q in all_queries if q.status != "ERROR"]
                if successful_queries:
                    avg_response_time = sum(q.response_time_ms for q in successful_queries) / len(successful_queries)
        
        report_lines.append(f"  Average Response Time: {avg_response_time:.1f}ms")
        report_lines.append(f"  Network Stability: {'Excellent' if simulation_results['success_rate_percent'] > 95 else 'Good'}")
        report_lines.append("")
        
        report_lines.append("Device Breakdown:")
        for session in simulation_results['sessions']:
            device_blocked = len([q for q in session.queries_made if q.status == "BLOCKED"])
            device_total = len(session.queries_made)
            device_block_rate = (device_blocked / max(device_total, 1)) * 100
            
            report_lines.append(f"  {session.device.name}:")
            report_lines.append(f"    Queries: {device_total}")
            report_lines.append(f"    Blocked: {device_blocked} ({device_block_rate:.1f}%)")
            report_lines.append(f"    Data Saved: {session.bytes_saved:.1f} MB")
        
        return "\n".join(report_lines)