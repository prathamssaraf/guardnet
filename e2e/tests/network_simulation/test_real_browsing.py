#!/usr/bin/env python3
import socket
import struct
import time
import subprocess
import platform

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
            return "RESOLVED", response_time
        elif rcode == 3:
            return "BLOCKED", response_time
        else:
            return f"ERROR_{rcode}", response_time
            
    except socket.timeout:
        return "TIMEOUT", 3000
    except Exception as e:
        return f"ERROR", 0

def compare_dns_servers():
    """Compare browsing experience with and without GuardNet"""
    print("GuardNet Ad Blocker - Real Browsing Comparison")
    print("=" * 60)
    print("Comparing DNS resolution with and without ad blocking")
    print()
    
    # Test domains that would be encountered during real browsing
    test_domains = [
        # Content domains (should always resolve)
        ("google.com", "search engine"),
        ("youtube.com", "video content"),
        ("amazon.com", "e-commerce"),
        ("cnn.com", "news content"),
        ("github.com", "code repository"),
        
        # Ad/tracking domains (should be blocked by GuardNet)
        ("googlesyndication.com", "Google ads"),
        ("doubleclick.net", "DoubleClick ads"),
        ("facebook.com", "social tracking"),
        ("googletagmanager.com", "tracking"),
        ("amazon-adsystem.com", "Amazon ads"),
        ("scorecardresearch.com", "analytics"),
    ]
    
    servers = [
        ("Without GuardNet", "8.8.8.8", 53),
        ("With GuardNet", "127.0.0.1", 8053),
    ]
    
    results = {}
    
    for server_name, server_ip, port in servers:
        print(f"{server_name} ({server_ip}:{port})")
        print("-" * 40)
        
        total_time = 0
        blocked_count = 0
        resolved_count = 0
        
        for domain, description in test_domains:
            result, response_time = send_dns_query(server_ip, port, domain)
            total_time += response_time
            
            if result == "BLOCKED":
                blocked_count += 1
                status = "[BLOCKED]"
            elif result == "RESOLVED":
                resolved_count += 1
                status = "[LOADED] "
            else:
                status = f"[{result}]"
            
            print(f"  {status} {domain:25} ({description:15}) {response_time:6.1f}ms")
        
        results[server_name] = {
            'total_time': total_time,
            'blocked': blocked_count,
            'resolved': resolved_count,
            'total_domains': len(test_domains)
        }
        
        print(f"  Total time: {total_time:.1f}ms | Blocked: {blocked_count} | Resolved: {resolved_count}")
        print()
    
    # Analysis
    print("=" * 60)
    print("BROWSING EXPERIENCE COMPARISON")
    print("=" * 60)
    
    without = results["Without GuardNet"]
    with_guard = results["With GuardNet"]
    
    print(f"Without GuardNet:")
    print(f"  - All requests resolved: {without['resolved']}/{without['total_domains']}")
    print(f"  - Total DNS time: {without['total_time']:.1f}ms")
    print(f"  - Ads loaded: ALL (slower browsing, tracking, bandwidth usage)")
    print()
    
    print(f"With GuardNet:")
    print(f"  - Content resolved: {with_guard['resolved']}/{with_guard['total_domains']}")
    print(f"  - Ads blocked: {with_guard['blocked']}/{with_guard['total_domains']}")
    print(f"  - Total DNS time: {with_guard['total_time']:.1f}ms")
    
    time_saved = without['total_time'] - with_guard['total_time']
    if time_saved > 0:
        print(f"  - Time saved: {time_saved:.1f}ms per page load")
    
    print()
    print("REAL-WORLD IMPACT:")
    print("=" * 30)
    print("🚀 Faster page loading (ads don't load)")
    print("📱 Reduced mobile data usage")
    print("🔒 Enhanced privacy (tracking blocked)")
    print("🛡️  Malware protection")
    print("🔋 Better battery life (less processing)")
    print()
    print("✨ GuardNet works with ALL browsers and applications!")
    print("   Chrome, Firefox, Safari, Edge, mobile apps, games, etc.")

def show_setup_instructions():
    """Show how to set up GuardNet as system DNS"""
    print("\n" + "=" * 60)
    print("HOW TO SET UP GUARDNET AS YOUR SYSTEM AD BLOCKER")
    print("=" * 60)
    print()
    print("STEP 1: Start GuardNet")
    print("  cd D:\\gaurdnet")
    print("  docker-compose up -d")
    print()
    print("STEP 2: Configure Your System DNS")
    print()
    
    if platform.system() == "Windows":
        print("Windows (Easy Method):")
        print("  1. Run PowerShell as Administrator")
        print("  2. .\\setup_windows_dns.ps1 -Enable")
        print()
        print("Windows (Manual Method):")
        print("  1. Settings → Network & Internet → Wi-Fi")
        print("  2. Change adapter options")
        print("  3. Right-click connection → Properties")
        print("  4. Internet Protocol Version 4 → Properties")
        print("  5. Use these DNS servers:")
        print("     Primary: 127.0.0.1")
        print("     Secondary: 8.8.8.8")
    
    print()
    print("STEP 3: Test Your Setup")
    print("  Open any browser and visit websites")
    print("  Ads should be blocked automatically!")
    print()
    print("STEP 4: Monitor Activity")
    print("  docker-compose logs dns-filter --follow")
    print("  (Watch real-time ad blocking)")

if __name__ == "__main__":
    compare_dns_servers()
    show_setup_instructions()