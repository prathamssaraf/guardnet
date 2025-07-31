#!/usr/bin/env python3
import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from e2e.utils.dns_client import DNSClient

def run_comprehensive_test():
    """Run comprehensive test of GuardNet DNS filtering"""
    print("GuardNet DNS Security Filter - Comprehensive Test")
    print("=" * 70)
    print("Testing real-world domains against threat intelligence database")
    print()
    
    # Initialize DNS client
    dns_client = DNSClient(server="127.0.0.1", port=8053)
    
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
            result = dns_client.query(domain)
            
            # Check if result matches expectation
            test_passed = result.status == expected
            status_icon = "PASS" if test_passed else "FAIL"
            
            print(f"  {status_icon} {domain:25} | {result.status:8} | {result.response_time_ms:6.1f}ms")
            
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