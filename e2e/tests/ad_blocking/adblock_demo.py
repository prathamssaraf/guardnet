#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from e2e.utils.dns_client import DNSClient

def demo_scenario():
    """Demonstrate a typical web browsing scenario with and without ad blocking"""
    print("GuardNet Ad Blocker - Real-World Browsing Simulation")
    print("=" * 70)
    print("Simulating a user visiting popular websites...")
    print()
    
    # Initialize DNS client
    dns_client = DNSClient(server="127.0.0.1", port=8053)
    
    # Simulate a typical browsing session
    browsing_session = [
        ("Visiting news website", [
            ("cnn.com", "news content"),
            ("googlesyndication.com", "ads"),
            ("doubleclick.net", "tracking"),
            ("scorecardresearch.com", "analytics"),
        ]),
        ("Shopping on e-commerce site", [
            ("amazon.com", "shopping"),
            ("amazon-adsystem.com", "ads"),
            ("googletagmanager.com", "tracking"),
            ("facebook.com", "social tracking"),
        ]),
        ("Watching video content", [
            ("youtube.com", "video content"),
            ("googlesyndication.com", "video ads"),
            ("doubleclick.com", "tracking"),
        ]),
        ("Social media browsing", [
            ("twitter.com", "social content"),
            ("facebook.com", "social tracking"),
            ("tiktok.com", "social content"),
        ]),
    ]
    
    total_requests = 0
    blocked_requests = 0
    allowed_requests = 0
    total_time_saved = 0
    
    for scenario, requests in browsing_session:
        print(f"{scenario}:")
        print("-" * 40)
        
        for domain, content_type in requests:
            result = dns_client.query(domain)
            total_requests += 1
            
            if result.status == "BLOCKED":
                blocked_requests += 1
                status_icon = "[X]"
                status_text = "BLOCKED"
                # Assume blocked ads would take 500ms to load
                total_time_saved += 500
            elif result.status == "ALLOWED":
                allowed_requests += 1
                status_icon = "[OK]"
                status_text = "LOADED"
            else:
                status_icon = "[?]"
                status_text = result.status
            
            print(f"  {status_icon} {domain:25} ({content_type:15}) - {status_text:8} ({result.response_time_ms:5.1f}ms)")
        
        print()
    
    # Calculate statistics
    block_rate = (blocked_requests / total_requests) * 100
    bandwidth_saved = blocked_requests * 2.5  # Assume 2.5MB per blocked ad/tracker
    
    print("=" * 70)
    print("BROWSING SESSION SUMMARY")
    print("=" * 70)
    print(f"Total DNS Requests:       {total_requests}")
    print(f"Ads/Trackers Blocked:     {blocked_requests} ({block_rate:.1f}%)")
    print(f"Content Allowed:          {allowed_requests}")
    print(f"Estimated Time Saved:     {total_time_saved/1000:.1f} seconds")
    print(f"Estimated Bandwidth Saved: {bandwidth_saved:.1f} MB")
    print(f"Privacy Protection:       Enhanced (tracking blocked)")
    print()
    
    print("BENEFITS OF GUARDNET AD BLOCKING:")
    print("- Faster page load times (ads blocked at DNS level)")
    print("- Reduced data usage and bandwidth costs")
    print("- Enhanced privacy (tracking prevention)")
    print("- Malware and phishing protection")
    print("- Cleaner, distraction-free browsing experience")
    print("- Family-safe internet filtering")
    print("=" * 70)

if __name__ == "__main__":
    demo_scenario()