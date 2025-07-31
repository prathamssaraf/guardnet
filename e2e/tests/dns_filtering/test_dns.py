#!/usr/bin/env python3
import socket
import struct
import sys

def create_dns_query(domain, query_type=1):
    """Create a DNS query packet"""
    # DNS header
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
        
        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)
        
        # Send query
        sock.sendto(query, (server, port))
        
        # Receive response
        response, addr = sock.recvfrom(512)
        sock.close()
        
        # Parse response header
        header = struct.unpack('!HHHHHH', response[:12])
        transaction_id, flags, questions, answers, authority, additional = header
        
        # Check response code
        rcode = flags & 0x000F
        
        if rcode == 0:
            return "RESOLVED"
        elif rcode == 3:
            return "NXDOMAIN"
        else:
            return f"ERROR_CODE_{rcode}"
            
    except socket.timeout:
        return "TIMEOUT"
    except Exception as e:
        return f"ERROR: {str(e)}"

def test_domains():
    """Test various domains against our DNS filter"""
    server = "127.0.0.1"
    port = 8053
    
    test_cases = [
        # Should be blocked (in our threat database)
        ("malware-test.com", "BLOCKED"),
        ("test.com", "BLOCKED"),
        ("example-phishing.com", "BLOCKED"),
        
        # Should be allowed (legitimate domains)
        ("google.com", "RESOLVED"),
        ("github.com", "RESOLVED"),
        ("stackoverflow.com", "RESOLVED"),
    ]
    
    print(f"Testing DNS filter at {server}:{port}")
    print("-" * 60)
    
    for domain, expected in test_cases:
        result = send_dns_query(server, port, domain)
        status = "PASS" if (expected == "BLOCKED" and result in ["NXDOMAIN", "TIMEOUT"]) or (expected == "RESOLVED" and result == "RESOLVED") else "FAIL"
        print(f"{status} {domain:25} -> {result:15} (expected: {expected})")
    
    print("-" * 60)

if __name__ == "__main__":
    test_domains()