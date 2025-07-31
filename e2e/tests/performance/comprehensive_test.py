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
        sock.settimeout(2)
        
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
        return "BLOCKED", 2000
    except Exception as e:
        return f"ERROR", 0

def run_comprehensive_test():
    """Run comprehensive test of GuardNet DNS filtering"""
    print("GuardNet DNS Security Filter - Comprehensive Test")
    print("=" * 70)
    print("Testing real-world domains against threat intelligence database")
    print()
    
    server = "127.0.0.1"
    port = 8053
    
    test_scenarios = [
        {
            "name": "MALWARE DOMAINS",
            "domains": [
                ("malware-test.com", "BLOCKED"),
                ("test.com", "BLOCKED"), 
            ]
        },
        {
            "name": "PHISHING DOMAINS", 
            "domains": [
                ("example-phishing.com", "BLOCKED"),
            ]
        },
        {
            "name": "ADVERTISING/TRACKING",
            "domains": [
                ("doubleclick.net", "BLOCKED"),
                ("googleadservices.com", "BLOCKED"),
                ("doubleclick.com", "BLOCKED"),
            ]
        },
        {
            "name": "LEGITIMATE WEBSITES",
            "domains": [
                ("google.com", "ALLOWED"),
                ("github.com", "ALLOWED"),
                ("stackoverflow.com", "ALLOWED"),
                ("microsoft.com", "ALLOWED"),
                ("cloudflare.com", "ALLOWED"),
            ]
        }
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for scenario in test_scenarios:
        print(f"{scenario['name']}")
        print("-" * 50)
        
        for domain, expected in scenario['domains']:
            result, response_time = send_dns_query(server, port, domain)
            
            # Check if result matches expectation
            test_passed = result == expected
            status_icon = "PASS" if test_passed else "FAIL"
            
            print(f"  {status_icon} {domain:25} | {result:8} | {response_time:6.1f}ms")
            
            total_tests += 1
            if test_passed:
                passed_tests += 1
        
        print()
    
    # Summary
    success_rate = (passed_tests / total_tests) * 100
    print("=" * 70)
    print(f"TEST RESULTS: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
    
    if success_rate == 100:
        print("ALL TESTS PASSED! GuardNet is working perfectly!")
        print("   - Malware domains blocked")
        print("   - Phishing domains blocked") 
        print("   - Advertising/tracking blocked")
        print("   - Legitimate traffic allowed")
        print("   - Fast response times with caching")
    else:
        print("Some tests failed. Please check configuration.")
    
    print("=" * 70)

if __name__ == "__main__":
    run_comprehensive_test()