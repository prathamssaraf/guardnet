#!/usr/bin/env python3
"""
GuardNet Router Simple Test
Tests basic router functionality without emoji encoding issues
"""

import socket
import struct
import time
import requests

def create_dns_query(domain):
    """Create DNS query packet"""
    transaction_id = 0x1234
    flags = 0x0100
    questions = 1
    
    header = struct.pack('!HHHHHH', transaction_id, flags, questions, 0, 0, 0)
    
    question = b''
    for part in domain.split('.'):
        question += bytes([len(part)]) + part.encode()
    question += b'\x00'
    question += struct.pack('!HH', 1, 1)
    
    return header + question

def test_dns_query(domain, expected_result="ALLOWED"):
    """Test DNS query to router"""
    try:
        query = create_dns_query(domain)
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3)
        
        start_time = time.time()
        sock.sendto(query, ("127.0.0.1", 8053))  # Use container port
        response, addr = sock.recvfrom(512)
        end_time = time.time()
        sock.close()
        
        response_time = (end_time - start_time) * 1000
        
        header = struct.unpack('!HHHHHH', response[:12])
        rcode = header[1] & 0x000F
        
        result = 'ALLOWED' if rcode == 0 else 'BLOCKED'
        status = 'PASS' if result == expected_result else 'FAIL'
        
        print(f"  {status} {domain:25} -> {result:8} ({response_time:5.1f}ms)")
        return result == expected_result
        
    except Exception as e:
        print(f"  ERROR {domain:25} -> {str(e)}")
        return False

def run_router_tests():
    """Run comprehensive router tests"""
    print("GuardNet Router Test Suite")
    print("=" * 50)
    
    print("\n1. Testing Content Domains (Should be ALLOWED):")
    content_tests = [
        "google.com",
        "github.com", 
        "stackoverflow.com",
        "amazon.com",
        "microsoft.com"
    ]
    
    content_passed = 0
    for domain in content_tests:
        if test_dns_query(domain, "ALLOWED"):
            content_passed += 1
    
    print(f"   Content Results: {content_passed}/{len(content_tests)} passed")
    
    print("\n2. Testing Ad Domains (Should be BLOCKED):")
    ad_tests = [
        "googlesyndication.com",
        "doubleclick.net", 
        "googletagmanager.com",
        "amazon-adsystem.com",
        "facebook.com",
        "scorecardresearch.com"
    ]
    
    ad_passed = 0
    for domain in ad_tests:
        if test_dns_query(domain, "BLOCKED"):
            ad_passed += 1
    
    print(f"   Ad Blocking Results: {ad_passed}/{len(ad_tests)} blocked")
    
    print("\n3. Testing Malware Domains (Should be BLOCKED):")
    malware_tests = [
        "malware-test.com",
        "example-phishing.com",
        "test.com"
    ]
    
    malware_passed = 0
    for domain in malware_tests:
        if test_dns_query(domain, "BLOCKED"):
            malware_passed += 1
    
    print(f"   Malware Protection: {malware_passed}/{len(malware_tests)} blocked")
    
    print("\n4. Testing Management API:")
    try:
        response = requests.get("http://127.0.0.1:8080/health", timeout=5)
        if response.status_code == 200:
            print("   PASS Management API -> Health check OK")
            api_passed = 1
        else:
            print(f"   FAIL Management API -> HTTP {response.status_code}")
            api_passed = 0
    except Exception as e:
        print(f"   ERROR Management API -> {str(e)}")
        api_passed = 0
    
    # Calculate overall results
    total_tests = len(content_tests) + len(ad_tests) + len(malware_tests) + 1
    total_passed = content_passed + ad_passed + malware_passed + api_passed
    success_rate = (total_passed / total_tests) * 100
    
    print("\n" + "=" * 50)
    print("ROUTER TEST SUMMARY")
    print("=" * 50) 
    print(f"Overall Success Rate: {total_passed}/{total_tests} ({success_rate:.1f}%)")
    print(f"Content Resolution: {content_passed}/{len(content_tests)} working")
    print(f"Ad Blocking: {ad_passed}/{len(ad_tests)} blocked")
    print(f"Malware Protection: {malware_passed}/{len(malware_tests)} blocked")
    print(f"Management API: {'Working' if api_passed else 'Failed'}")
    
    # Router service benefits
    print(f"\nROUTER SERVICE BENEFITS:")
    print(f"- Network-wide protection for ALL devices")
    print(f"- Zero client configuration required")
    print(f"- Ad blocking rate: {(ad_passed/len(ad_tests)*100):.1f}%")
    print(f"- Family-safe internet out of the box")
    print(f"- Enterprise threat intelligence")
    print(f"- Recurring revenue model ready")
    
    if success_rate >= 80:
        print(f"\nSTATUS: READY FOR ROUTER DEPLOYMENT!")
    else:
        print(f"\nSTATUS: Needs configuration review")
    
    return success_rate >= 80

if __name__ == "__main__":
    success = run_router_tests()
    print("=" * 50)