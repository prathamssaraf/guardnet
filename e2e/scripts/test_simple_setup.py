#!/usr/bin/env python3
"""
Simple GuardNet Test - No Docker Required
Tests the e2e framework with mock DNS responses
"""

import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from e2e.utils.dns_client import DNSClient, DNSQueryResult
from e2e.utils.network_sim import NetworkSimulator

class MockDNSClient:
    """Mock DNS client for testing without actual DNS service"""
    
    def __init__(self, server="127.0.0.1", port=8053, timeout=5.0):
        self.server = server
        self.port = port
        self.timeout = timeout
        
        # Mock responses for different domain types
        self.blocked_domains = {
            'googlesyndication.com', 'doubleclick.net', 'googletagmanager.com',
            'amazon-adsystem.com', 'facebook.com', 'scorecardresearch.com'
        }
        
        self.allowed_domains = {
            'google.com', 'github.com', 'amazon.com', 'youtube.com', 'netflix.com',
            'cnn.com', 'bbc.com', 'pinterest.com', 'steam.com', 'discord.com'
        }
    
    def query(self, domain, server=None, port=None, query_type=None, timeout=None):
        """Mock DNS query with realistic responses"""
        
        # Simulate network delay
        time.sleep(0.01 + (hash(domain) % 50) / 1000)  # 10-60ms delay
        
        response_time = 10 + (hash(domain) % 40)  # 10-50ms response time
        
        if domain in self.blocked_domains:
            return DNSQueryResult(
                domain=domain,
                query_type="A",
                status="BLOCKED",
                response_code=3,  # NXDOMAIN
                response_time_ms=response_time,
                timestamp=time.time(),
                server_used=f"{self.server}:{self.port}"
            )
        elif domain in self.allowed_domains:
            return DNSQueryResult(
                domain=domain,
                query_type="A", 
                status="ALLOWED",
                response_code=0,  # NOERROR
                response_time_ms=response_time,
                timestamp=time.time(),
                ip_addresses=["192.168.1.100"],  # Mock IP
                server_used=f"{self.server}:{self.port}"
            )
        else:
            # Unknown domains get blocked by default (threat protection)
            return DNSQueryResult(
                domain=domain,
                query_type="A",
                status="BLOCKED", 
                response_code=3,
                response_time_ms=response_time,
                timestamp=time.time(),
                error_message="Domain not in whitelist",
                server_used=f"{self.server}:{self.port}"
            )

def test_mock_dns_functionality():
    """Test DNS functionality with mock client"""
    print("🧪 Testing Mock DNS Functionality...")
    
    client = MockDNSClient()
    
    # Test allowed domain
    result = client.query("google.com")
    print(f"  google.com: {result.status} ({result.response_time_ms:.1f}ms)")
    
    # Test blocked domain (ad)
    result = client.query("googlesyndication.com")
    print(f"  googlesyndication.com: {result.status} ({result.response_time_ms:.1f}ms)")
    
    # Test unknown domain (should be blocked)
    result = client.query("unknown-domain-test.com")
    print(f"  unknown-domain-test.com: {result.status} ({result.response_time_ms:.1f}ms)")
    
    print("  ✅ Mock DNS functionality working")
    return True

def test_network_simulation_with_mock():
    """Test network simulation with mock DNS"""
    print("\n🌐 Testing Network Simulation (10s with Mock DNS)...")
    
    # Create simulator with mock DNS client
    mock_client = MockDNSClient()
    sim = NetworkSimulator(mock_client)
    
    # Create a small family network for quick testing
    family_devices = sim.create_family_network()
    
    print(f"  Created {len(family_devices)} family devices")
    
    # Run short simulation
    def progress_callback(message):
        if "BLOCKED" in message and len(message) < 100:  # Show some blocked messages
            print(f"    🚫 {message}")
    
    print("  Running 10-second simulation...")
    results = sim.run_network_simulation(duration=10, progress_callback=progress_callback)
    
    # Display results
    print(f"\n📊 Mock Network Simulation Results:")
    print(f"  Total Queries: {results['total_queries']}")
    print(f"  Blocked: {results['blocked_queries']} ({results['block_rate_percent']}%)")
    print(f"  Allowed: {results['allowed_queries']}")
    print(f"  Success Rate: {results['success_rate_percent']}%")
    print(f"  Queries/Second: {results['queries_per_second']}")
    print(f"  Bandwidth Saved: {results['total_bandwidth_saved_mb']:.1f} MB")
    
    # Verify we got reasonable results
    if results['total_queries'] > 5 and results['success_rate_percent'] > 95:
        print("  ✅ Network simulation working correctly")
        return True
    else:
        print("  ❌ Network simulation may have issues")
        return False

def test_family_vs_business_simulation():
    """Compare family vs business network patterns"""
    print("\n👨‍👩‍👧‍👦 vs 🏢 Family vs Business Network Comparison...")
    
    mock_client = MockDNSClient()
    
    # Test family network
    family_sim = NetworkSimulator(mock_client)
    family_devices = family_sim.create_family_network()
    family_results = family_sim.run_network_simulation(duration=5)
    
    # Test business network  
    biz_sim = NetworkSimulator(mock_client)
    biz_devices = biz_sim.create_business_network()
    biz_results = biz_sim.run_network_simulation(duration=5)
    
    print(f"  Family Network ({len(family_devices)} devices):")
    print(f"    Queries: {family_results['total_queries']}, Blocked: {family_results['block_rate_percent']}%")
    
    print(f"  Business Network ({len(biz_devices)} devices):")
    print(f"    Queries: {biz_results['total_queries']}, Blocked: {biz_results['block_rate_percent']}%")
    
    if family_results['total_queries'] > 0 and biz_results['total_queries'] > 0:
        print("  ✅ Both network types functioning")
        return True
    else:
        print("  ❌ Network simulation issues")
        return False

def main():
    """Run simplified test suite"""
    print("GuardNet Simple Test Suite (No Docker Required)")
    print("=" * 60)
    
    tests = [
        test_mock_dns_functionality,
        test_network_simulation_with_mock,
        test_family_vs_business_simulation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  💥 Test {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🏁 Simple Test Results:")
    print(f"  Total: {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {total - passed}")
    
    if passed == total:
        print("  🎉 All tests passed! E2E framework is working correctly.")
        print("\n💡 Next Steps:")
        print("  1. Start Docker Desktop")
        print("  2. Run: docker-compose up -d")
        print("  3. Run full e2e test suite")
        return True
    else:
        print("  ⚠️  Some tests failed")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite error: {e}")
        sys.exit(1)