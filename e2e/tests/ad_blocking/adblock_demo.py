#!/usr/bin/env python3
import socket
import struct
import time

def create_dns_query(domain, query_type=1):
    """Create a DNS query packet"""
    transaction_id = 0x1234
    flags = 0x0100
    questions = 1
    answer_rrs = 0
    authority_rrs = 0 
    additional_rrs = 0
    
    header = struct.pack('!HHHHHH', transaction_id, flags, questions,
                        answer_rrs, authority_rrs, additional_rrs)
    
    question = b''
    for part in domain.split('.'):
        question += bytes([len(part)]) + part.encode()
    question += b'\x00'
    question += struct.pack('!HH', query_type, 1)
    
    return header + question

def send_dns_query(server, port, domain):
    """Send DNS query and return response"""
    try:
        query = create_dns_query(domain)
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3)
        
        start_time = time.time()
        sock.sendto(query, (server, port))
        response, addr = sock.recvfrom(512)
        end_time = time.time()
        sock.close()
        
        response_time = round((end_time - start_time) * 1000, 2)
        
        header = struct.unpack('!HHHHHH', response[:12])
        transaction_id, flags, questions, answers, authority, additional = header
        
        rcode = flags & 0x000F
        
        if rcode == 0:
            return "ALLOWED", response_time
        elif rcode == 3:
            return "BLOCKED", response_time
        else:
            return f"ERROR_{rcode}", response_time
            
    except socket.timeout:
        return "TIMEOUT", 3000
    except Exception as e:
        return f"ERROR", 0

def demo_scenario():
    """Demonstrate a typical web browsing scenario with and without ad blocking"""
    print("GuardNet Ad Blocker - Real-World Browsing Simulation")
    print("=" * 70)
    print("Simulating a user visiting popular websites...")
    print()
    
    server = "127.0.0.1"
    port = 8053
    
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
            result, response_time = send_dns_query(server, port, domain)
            total_requests += 1
            
            if result == "BLOCKED":
                blocked_requests += 1
                status_icon = "[X]"
                status_text = "BLOCKED"
                # Assume blocked ads would take 500ms to load
                total_time_saved += 500
            elif result == "ALLOWED":
                allowed_requests += 1
                status_icon = "[OK]"
                status_text = "LOADED"
            else:
                status_icon = "[?]"
                status_text = result
            
            print(f"  {status_icon} {domain:25} ({content_type:15}) - {status_text:8} ({response_time:5.1f}ms)")
        
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