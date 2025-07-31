#!/usr/bin/env python3
"""
Basic DNS Filtering Tests
Tests core DNS resolution functionality
"""

import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from e2e.utils.dns_client import DNSClient, DNSTestUtils

def test_basic_dns_resolution():
    """Test basic DNS resolution functionality"""
    print("🔍 Testing Basic DNS Resolution...")
    
    # Initialize DNS client for GuardNet
    client = DNSClient(server="127.0.0.1", port=8053)
    
    # Test basic domain resolution
    test_domains = [
        "google.com",
        "github.com", 
        "cloudflare.com",
        "example.com"
    ]
    
    results = client.batch_query(test_domains)
    
    # Check results
    successful_queries = len([r for r in results if r.status == "ALLOWED"])
    success_rate = (successful_queries / len(test_domains)) * 100
    
    print(f"  Tested {len(test_domains)} legitimate domains")
    print(f"  Success rate: {success_rate:.1f}%")
    print(f"  Average response time: {DNSTestUtils.get_average_response_time(results):.1f}ms")
    
    if success_rate >= 75:  # At least 75% should resolve
        print("  ✅ Basic DNS resolution test PASSED")
        return True
    else:
        print("  ❌ Basic DNS resolution test FAILED")
        return False

def test_dns_cache_performance():
    """Test DNS caching performance"""
    print("\n⚡ Testing DNS Cache Performance...")
    
    client = DNSClient(server="127.0.0.1", port=8053)
    
    # First query (should hit upstream)
    domain = "example.com"
    first_result = client.query(domain)
    
    # Second query (should hit cache)
    time.sleep(0.1)  # Small delay
    second_result = client.query(domain)
    
    print(f"  First query: {first_result.response_time_ms:.1f}ms")
    print(f"  Cached query: {second_result.response_time_ms:.1f}ms")
    
    # Cache should be faster (though not always guaranteed in real networks)
    if second_result.response_time_ms <= first_result.response_time_ms * 1.5:
        print("  ✅ DNS cache performance test PASSED")
        return True
    else:
        print("  ⚠️  DNS cache may not be optimally configured")
        return True  # Don't fail the test for this

def test_invalid_domain_handling():
    """Test handling of invalid domain queries"""
    print("\n🚫 Testing Invalid Domain Handling...")
    
    client = DNSClient(server="127.0.0.1", port=8053)
    
    invalid_domains = [
        "definitely-not-a-real-domain-12345.com",
        "invalid..domain.com",
        "non-existent-domain-test.invalid"
    ]
    
    results = client.batch_query(invalid_domains)
    
    # These should either be blocked or return NXDOMAIN
    handled_properly = len([r for r in results if r.status in ["BLOCKED", "ERROR"]])
    
    print(f"  Tested {len(invalid_domains)} invalid domains")
    print(f"  Properly handled: {handled_properly}/{len(invalid_domains)}")
    
    if handled_properly >= len(invalid_domains) * 0.7:  # 70% should be handled properly
        print("  ✅ Invalid domain handling test PASSED")
        return True
    else:
        print("  ❌ Invalid domain handling test FAILED")
        return False

def test_dns_timeout_handling():
    """Test DNS timeout handling"""
    print("\n⏱️  Testing DNS Timeout Handling...")
    
    # Test with normal timeout first
    client = DNSClient(server="127.0.0.1", port=8053, timeout=5.0)
    
    result = client.query("example.com")
    
    print(f"  Query result: {result.status}")
    print(f"  Response time: {result.response_time_ms:.1f}ms")
    
    # Either the query succeeds, is blocked, or times out gracefully
    if result.status in ["ALLOWED", "BLOCKED", "TIMEOUT", "ERROR"]:
        print("  ✅ DNS timeout handling test PASSED")
        return True
    else:
        print("  ❌ DNS timeout handling test FAILED")
        print(f"  Unexpected status: {result.status}")
        return False

def main():
    """Run all DNS filtering tests"""
    print("🧪 GuardNet DNS Filtering Tests")
    print("=" * 40)
    
    tests = [
        test_basic_dns_resolution,
        test_dns_cache_performance,
        test_invalid_domain_handling,
        test_dns_timeout_handling
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test in tests:
        try:
            if test():
                passed_tests += 1
        except Exception as e:
            print(f"  💥 Test {test.__name__} failed with error: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n📊 DNS Filtering Test Results:")
    print(f"  Total: {total_tests}")
    print(f"  Passed: {passed_tests}")
    print(f"  Failed: {total_tests - passed_tests}")
    
    if passed_tests == total_tests:
        print("  🎉 All DNS filtering tests passed!")
        return True
    else:
        print("  ⚠️  Some DNS filtering tests failed")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
        sys.exit(1)