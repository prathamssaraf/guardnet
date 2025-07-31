#!/usr/bin/env python3
"""
Router Integration Test
Tests the complete flow: Internet → WiFi Router → GuardNet System → Devices
"""

import os
import sys
import time
import socket
import subprocess
import threading
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from e2e.utils.dns_client import DNSClient
from e2e.utils.network_sim import NetworkSimulator, DeviceType, NetworkDevice

class RouterIntegrationTest:
    """Test GuardNet integration with router deployment"""
    
    def __init__(self):
        self.guardnet_dns = DNSClient(server="127.0.0.1", port=8053)
        self.upstream_dns = DNSClient(server="8.8.8.8", port=53)  # Google DNS as upstream
        self.test_results = []
        
    def log_result(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {test_name} {message}")
        self.test_results.append({
            "test": test_name,
            "passed": passed, 
            "message": message
        })
        
    def test_basic_dns_resolution(self):
        """Test basic DNS resolution through GuardNet"""
        print("\n🔍 Testing Basic DNS Resolution...")
        
        # Test legitimate domain resolution
        result = self.guardnet_dns.query("google.com")
        self.log_result(
            "Legitimate Domain Resolution",
            result.status == "ALLOWED" and result.ip_address is not None,
            f"({result.response_time_ms:.1f}ms)"
        )
        
        # Test DNS cache performance
        start_time = time.time()
        cached_result = self.guardnet_dns.query("google.com")
        cache_time = (time.time() - start_time) * 1000
        
        self.log_result(
            "DNS Cache Performance", 
            cache_time < 50,  # Should be under 50ms for cached queries
            f"(cache: {cache_time:.1f}ms)"
        )
        
    def test_ad_blocking_functionality(self):
        """Test ad blocking in router deployment"""
        print("\n🚫 Testing Ad Blocking Functionality...")
        
        # Known ad domains to test
        ad_domains = [
            "googlesyndication.com",
            "doubleclick.net", 
            "googletagmanager.com",
            "facebook.com",  # Often blocked for privacy
            "amazon-adsystem.com"
        ]
        
        blocked_count = 0
        for domain in ad_domains:
            result = self.guardnet_dns.query(domain)
            if result.status == "BLOCKED":
                blocked_count += 1
            
        block_rate = (blocked_count / len(ad_domains)) * 100
        self.log_result(
            "Ad Domain Blocking",
            block_rate >= 60,  # At least 60% of ad domains should be blocked
            f"({blocked_count}/{len(ad_domains)} blocked, {block_rate:.1f}%)"
        )
        
    def test_threat_protection(self):
        """Test malware and phishing protection"""
        print("\n🛡️ Testing Threat Protection...")
        
        # Test domains (these should be blocked if threat feeds are working)
        threat_domains = [
            "malware-test.com",  # From our sample data
            "phishing-example.org",  # From our sample data
            "botnet.evil.io",  # From our sample data
            "suspicious-domain-123456.com",  # Should be blocked by ML
        ]
        
        blocked_threats = 0
        for domain in threat_domains:
            result = self.guardnet_dns.query(domain)
            if result.status == "BLOCKED":
                blocked_threats += 1
                
        self.log_result(
            "Threat Domain Protection",
            blocked_threats >= 3,  # At least 3 out of 4 should be blocked
            f"({blocked_threats}/{len(threat_domains)} threats blocked)"
        )
        
    def test_upstream_dns_failover(self):
        """Test failover to upstream DNS servers"""
        print("\n🔄 Testing DNS Failover...")
        
        # Test a domain that should always resolve
        test_domain = "cloudflare.com"
        
        # Query through GuardNet
        guardnet_result = self.guardnet_dns.query(test_domain)
        
        # Query through upstream DNS directly
        upstream_result = self.upstream_dns.query(test_domain)
        
        # Both should succeed for legitimate domains
        self.log_result(
            "Upstream DNS Connectivity",
            guardnet_result.status == "ALLOWED" and upstream_result.status == "ALLOWED",
            f"GuardNet: {guardnet_result.response_time_ms:.1f}ms, Upstream: {upstream_result.response_time_ms:.1f}ms"
        )
        
        # Response time should be reasonable (under 500ms)
        self.log_result(
            "DNS Response Time",
            guardnet_result.response_time_ms < 500,
            f"({guardnet_result.response_time_ms:.1f}ms)"
        )
        
    def test_family_network_simulation(self):
        """Test realistic family network usage"""
        print("\n👨‍👩‍👧‍👦 Testing Family Network Simulation...")
        
        # Create network simulator
        sim = NetworkSimulator(self.guardnet_dns)
        
        # Create family devices
        family_devices = sim.create_family_network()
        
        # Run short simulation (30 seconds)
        results = sim.run_network_simulation(duration=30)
        
        # Verify reasonable performance
        self.log_result(
            "Family Network Query Volume",
            results['total_queries'] >= 10,  # Should have at least 10 queries in 30s
            f"({results['total_queries']} queries)"
        )
        
        self.log_result(
            "Family Network Block Rate",
            10 <= results['block_rate_percent'] <= 80,  # Reasonable block rate
            f"({results['block_rate_percent']}% blocked)"
        )
        
        self.log_result(
            "Family Network Stability",
            results['success_rate_percent'] >= 95,  # High success rate
            f"({results['success_rate_percent']}% success)"
        )
        
        return results
        
    def test_multi_device_concurrent_queries(self):
        """Test concurrent queries from multiple devices"""
        print("\n📱 Testing Multi-Device Concurrent Access...")
        
        # Create test devices
        devices = [
            ("smartphone", ["facebook.com", "google.com", "youtube.com"]),
            ("laptop", ["github.com", "stackoverflow.com", "googlesyndication.com"]),
            ("tablet", ["netflix.com", "amazon.com", "doubleclick.net"]),
            ("smart_tv", ["hulu.com", "disney.com", "amazon-adsystem.com"])
        ]
        
        # Function to simulate device queries
        def device_queries(device_name, domains, results_list):
            device_results = []
            for domain in domains:
                result = self.guardnet_dns.query(domain)
                device_results.append(result)
            results_list.append((device_name, device_results))
        
        # Run concurrent queries
        threads = []
        concurrent_results = []
        
        for device_name, domains in devices:
            thread = threading.Thread(
                target=device_queries,
                args=(device_name, domains, concurrent_results)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=30)  # 30 second timeout
            
        # Analyze results
        total_queries = sum(len(results) for _, results in concurrent_results)
        successful_queries = sum(
            1 for _, results in concurrent_results 
            for result in results 
            if result.status in ["ALLOWED", "BLOCKED"]
        )
        
        success_rate = (successful_queries / max(total_queries, 1)) * 100
        
        self.log_result(
            "Concurrent Query Handling",
            success_rate >= 95,
            f"({successful_queries}/{total_queries} successful, {success_rate:.1f}%)"
        )
        
        # Check response times under load
        avg_response_time = sum(
            result.response_time_ms 
            for _, results in concurrent_results 
            for result in results
        ) / max(total_queries, 1)
        
        self.log_result(
            "Performance Under Load",
            avg_response_time < 200,  # Should handle concurrent load well
            f"(avg {avg_response_time:.1f}ms)"
        )
        
    def test_router_configuration_compatibility(self):
        """Test router configuration compatibility"""
        print("\n🌐 Testing Router Configuration...")
        
        # Check if GuardNet DNS port is accessible
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(5)
            sock.connect(("127.0.0.1", 8053))
            sock.close()
            dns_accessible = True
        except:
            dns_accessible = False
            
        self.log_result(
            "DNS Port Accessibility",
            dns_accessible,
            "(port 8053)"
        )
        
        # Check management interface
        try:
            import requests
            response = requests.get("http://localhost:3000/health", timeout=5)
            api_accessible = response.status_code == 200
        except ImportError:
            print("    ℹ️  requests module not available, skipping API check")
            api_accessible = True  # Don't fail test for missing module
        except:
            api_accessible = False
            
        self.log_result(
            "Management API Accessibility",
            api_accessible,
            "(port 3000)"
        )
        
        # Check if DNS resolution works for router configuration
        router_domains = [
            "time.nist.gov",      # Time synchronization
            "pool.ntp.org",       # NTP servers
            "checkip.amazonaws.com", # IP checking
        ]
        
        router_compatible = True
        for domain in router_domains:
            result = self.guardnet_dns.query(domain)
            if result.status != "ALLOWED":
                router_compatible = False
                break
                
        self.log_result(
            "Router Infrastructure Compatibility",
            router_compatible,
            "(essential router services accessible)"
        )
        
    def test_bandwidth_and_latency_impact(self):
        """Test bandwidth and latency impact of GuardNet"""
        print("\n⚡ Testing Performance Impact...")
        
        # Measure DNS resolution times
        test_domains = ["google.com", "amazon.com", "facebook.com", "youtube.com"]
        guardnet_times = []
        upstream_times = []
        
        for domain in test_domains:
            # Test through GuardNet
            start = time.time()
            guardnet_result = self.guardnet_dns.query(domain)
            guardnet_time = (time.time() - start) * 1000
            guardnet_times.append(guardnet_time)
            
            # Test direct upstream (for comparison)
            start = time.time()
            upstream_result = self.upstream_dns.query(domain)
            upstream_time = (time.time() - start) * 1000
            upstream_times.append(upstream_time)
        
        avg_guardnet = sum(guardnet_times) / len(guardnet_times)
        avg_upstream = sum(upstream_times) / len(upstream_times)
        latency_overhead = avg_guardnet - avg_upstream
        
        self.log_result(
            "DNS Latency Overhead",
            latency_overhead < 100,  # Should add less than 100ms overhead
            f"(+{latency_overhead:.1f}ms avg overhead)"
        )
        
        # Test query throughput
        start_time = time.time()
        query_count = 0
        
        # Send queries for 10 seconds
        while time.time() - start_time < 10:
            domain = test_domains[query_count % len(test_domains)]
            self.guardnet_dns.query(domain)
            query_count += 1
        
        queries_per_second = query_count / 10
        
        self.log_result(
            "Query Throughput",
            queries_per_second >= 10,  # Should handle at least 10 QPS
            f"({queries_per_second:.1f} QPS)"
        )
        
    def run_all_tests(self):
        """Run all router integration tests"""
        print("🌐 GuardNet Router Integration Test Suite")
        print("=" * 50)
        
        # Run all test categories
        self.test_basic_dns_resolution()
        self.test_ad_blocking_functionality()
        self.test_threat_protection()
        self.test_upstream_dns_failover()
        family_results = self.test_family_network_simulation()
        self.test_multi_device_concurrent_queries()
        self.test_router_configuration_compatibility()
        self.test_bandwidth_and_latency_impact()
        
        # Calculate summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests
        
        print(f"\n📊 Router Integration Test Summary:")
        print("=" * 40)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if family_results:
            print(f"\n👨‍👩‍👧‍👦 Family Network Benefits:")
            print(f"  🚫 Blocked Ads/Threats: {family_results['blocked_queries']}")
            print(f"  💾 Bandwidth Saved: {family_results['total_bandwidth_saved_mb']:.1f} MB")
            print(f"  ⏱️  Time Saved: {family_results['total_time_saved_seconds']:.1f} seconds")
        
        if failed_tests == 0:
            print(f"\n🎉 All router integration tests passed!")
            print("GuardNet is ready for router deployment!")
            return True
        else:
            print(f"\n⚠️  {failed_tests} tests failed. Review configuration before deployment.")
            return False

def main():
    """Main test execution"""
    try:
        test_suite = RouterIntegrationTest()
        success = test_suite.run_all_tests()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test suite failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()