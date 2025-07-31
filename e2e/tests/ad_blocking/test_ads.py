#!/usr/bin/env python3
import socket
import struct

def create_dns_query(domain, query_type=1):
    """Create a DNS query packet"""
    transaction_id = 0x1234
    flags = 0x0100  # Standard query
    questions = 1
    answer_rrs = 0
    authority_rrs = 0
    additional_rrs = 0
    
    header = struct.pack('!HHHHHH', transaction_id, flags, questions, 
                        answer_rrs, authority_rrs, additional_rrs)
    
    # DNS question
    question = b''
    for part in domain.split('.'):
        question += bytes([len(part)]) + part.encode()
    question += b'\x00'  # End of domain name
    question += struct.pack('!HH', query_type, 1)  # Type A, Class IN
    
    return header + question

def send_dns_query(server, port, domain):
    """Send DNS query and return response"""
    try:
        query = create_dns_query(domain)
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3)
        
        sock.sendto(query, (server, port))
        response, addr = sock.recvfrom(512)
        sock.close()
        
        header = struct.unpack('!HHHHHH', response[:12])
        transaction_id, flags, questions, answers, authority, additional = header
        
        rcode = flags & 0x000F
        
        if rcode == 0:
            return "RESOLVED"
        elif rcode == 3:
            return "BLOCKED"
        else:
            return f"ERROR_{rcode}"
            
    except socket.timeout:
        return "TIMEOUT"
    except Exception as e:
        return f"ERROR: {str(e)}"

def test_real_world_domains():
    """Test real-world domains including ads, malware, and legitimate sites"""
    server = "127.0.0.1"
    port = 8053
    
    print("Testing GuardNet DNS Filter against real-world domains")
    print("=" * 70)
    
    # Test categories
    categories = {
        "MALICIOUS (should be blocked)": [
            "malware-test.com",
            "test.com", 
            "example-phishing.com",
        ],
        "ADVERTISING (should be blocked)": [
            "doubleclick.net",
            "googleadservices.com", 
            "doubleclick.com",
        ],
        "LEGITIMATE (should be allowed)": [
            "google.com",
            "github.com", 
            "stackoverflow.com",
            "microsoft.com",
            "amazon.com",
            "cloudflare.com"
        ]
    }
    
    for category, domains in categories.items():
        print(f"\n{category}:")
        print("-" * 50)
        
        for domain in domains:
            result = send_dns_query(server, port, domain)
            
            # Determine if result matches expectation
            expected_blocked = "should be blocked" in category
            is_blocked = result in ["BLOCKED", "TIMEOUT"]
            
            if expected_blocked and is_blocked:
                status = "PASS (blocked as expected)"
            elif not expected_blocked and result == "RESOLVED":
                status = "PASS (allowed as expected)"
            else:
                status = "FAIL (unexpected result)"
            
            print(f"  {domain:25} -> {result:10} | {status}")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    test_real_world_domains()