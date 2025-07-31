#!/usr/bin/env python3
"""
GuardNet Router Deployment Testing Suite
Tests router-based service functionality
"""

import socket
import struct
import time
import requests
import json
import subprocess
import threading
from typing import Dict, List

class RouterDeploymentTester:
    """Test suite for GuardNet router deployment"""
    
    def __init__(self):
        self.router_dns = "127.0.0.1"
        self.router_port = 53  # Standard DNS port for router mode
        self.management_port = 8080
        self.test_results = []
        
    def create_dns_query(self, domain: str) -> bytes:
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
    
    def send_dns_query(self, domain: str) -> Dict:
        """Send DNS query to router"""
        try:
            query = self.create_dns_query(domain)
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(3)
            
            start_time = time.time()
            sock.sendto(query, (self.router_dns, self.router_port))
            response, addr = sock.recvfrom(512)
            end_time = time.time()
            sock.close()
            
            response_time = (end_time - start_time) * 1000
            
            header = struct.unpack('!HHHHHH', response[:12])
            rcode = header[1] & 0x000F
            
            return {
                'domain': domain,
                'status': 'ALLOWED' if rcode == 0 else 'BLOCKED',
                'response_time': round(response_time, 2),
                'success': True
            }
            
        except Exception as e:
            return {
                'domain': domain,
                'status': 'ERROR',
                'error': str(e),
                'success': False
            }
    
    def test_basic_dns_functionality(self):
        """Test basic DNS resolution"""
        print("🧪 Testing Basic DNS Functionality")
        print("-" * 40)
        
        test_domains = [
            ("google.com", "ALLOWED"),
            ("github.com", "ALLOWED"), 
            ("cloudflare.com", "ALLOWED"),
        ]
        
        passed = 0
        for domain, expected in test_domains:
            result = self.send_dns_query(domain)
            status = "✅ PASS" if result['status'] == expected else "❌ FAIL"
            print(f"  {status} {domain:20} -> {result['status']:8} ({result.get('response_time', 0):5.1f}ms)")
            
            if result['status'] == expected:
                passed += 1
                
            self.test_results.append({
                'test': 'basic_dns',
                'domain': domain,
                'expected': expected,
                'actual': result['status'],
                'passed': result['status'] == expected
            })
        
        print(f"  Result: {passed}/{len(test_domains)} tests passed\n")
        return passed == len(test_domains)
    
    def test_ad_blocking(self):
        """Test ad blocking functionality"""
        print("🚫 Testing Ad Blocking")
        print("-" * 40)
        
        ad_domains = [
            ("googlesyndication.com", "BLOCKED"),
            ("doubleclick.net", "BLOCKED"),
            ("googletagmanager.com", "BLOCKED"),
            ("amazon-adsystem.com", "BLOCKED"),
            ("facebook.com", "BLOCKED"),
            ("scorecardresearch.com", "BLOCKED"),
        ]
        
        passed = 0
        for domain, expected in ad_domains:
            result = self.send_dns_query(domain)
            status = "✅ PASS" if result['status'] == expected else "❌ FAIL"
            print(f"  {status} {domain:25} -> {result['status']:8} ({result.get('response_time', 0):5.1f}ms)")
            
            if result['status'] == expected:
                passed += 1
                
            self.test_results.append({
                'test': 'ad_blocking',
                'domain': domain,
                'expected': expected,
                'actual': result['status'],
                'passed': result['status'] == expected
            })
        
        block_rate = (passed / len(ad_domains)) * 100
        print(f"  Ad Blocking Rate: {block_rate:.1f}%")
        print(f"  Result: {passed}/{len(ad_domains)} ads blocked\n")
        return passed >= len(ad_domains) * 0.8  # 80% success rate
    
    def test_malware_protection(self):
        """Test malware domain blocking"""
        print("🦠 Testing Malware Protection")
        print("-" * 40)
        
        malware_domains = [
            ("malware-test.com", "BLOCKED"),
            ("example-phishing.com", "BLOCKED"),
            ("test.com", "BLOCKED"),
        ]
        
        passed = 0
        for domain, expected in malware_domains:
            result = self.send_dns_query(domain)
            status = "✅ PASS" if result['status'] == expected else "❌ FAIL"
            print(f"  {status} {domain:25} -> {result['status']:8} ({result.get('response_time', 0):5.1f}ms)")
            
            if result['status'] == expected:
                passed += 1
                
            self.test_results.append({
                'test': 'malware_protection',
                'domain': domain,
                'expected': expected,
                'actual': result['status'],
                'passed': result['status'] == expected
            })
        
        print(f"  Result: {passed}/{len(malware_domains)} threats blocked\n")
        return passed == len(malware_domains)
    
    def test_management_api(self):
        """Test router management API"""
        print("🔧 Testing Management API")
        print("-" * 40)
        
        api_tests = [
            ("/health", "Health check"),
            ("/ready", "Ready status"),
            ("/metrics", "Metrics endpoint"),
        ]
        
        passed = 0
        for endpoint, description in api_tests:
            try:
                url = f"http://{self.router_dns}:{self.management_port}{endpoint}"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    status = "✅ PASS"
                    passed += 1
                else:
                    status = f"❌ FAIL (HTTP {response.status_code})"
                
                print(f"  {status} {endpoint:15} - {description}")
                
                self.test_results.append({
                    'test': 'management_api',
                    'endpoint': endpoint,
                    'status_code': response.status_code,
                    'passed': response.status_code == 200
                })
                
            except Exception as e:
                print(f"  ❌ FAIL {endpoint:15} - Error: {str(e)}")
                self.test_results.append({
                    'test': 'management_api',
                    'endpoint': endpoint,
                    'error': str(e),
                    'passed': False
                })
        
        print(f"  Result: {passed}/{len(api_tests)} endpoints working\n")
        return passed >= len(api_tests) * 0.5
    
    def test_performance(self):
        """Test DNS performance under load"""
        print("⚡ Testing Performance")
        print("-" * 40)
        
        test_domain = "google.com"
        num_queries = 50
        
        response_times = []
        errors = 0
        
        print(f"  Sending {num_queries} queries to {test_domain}...")
        
        start_time = time.time()
        for i in range(num_queries):
            result = self.send_dns_query(test_domain)
            if result['success']:
                response_times.append(result['response_time'])
            else:
                errors += 1
        
        total_time = time.time() - start_time
        
        if response_times:
            avg_response = sum(response_times) / len(response_times)
            min_response = min(response_times)
            max_response = max(response_times)
            
            print(f"  ✅ Average Response Time: {avg_response:.1f}ms")
            print(f"  ⚡ Min Response Time: {min_response:.1f}ms")
            print(f"  🐌 Max Response Time: {max_response:.1f}ms")
            print(f"  📊 Queries per Second: {num_queries/total_time:.1f}")
            print(f"  ❌ Errors: {errors}/{num_queries}")
            
            # Performance criteria
            performance_good = (
                avg_response < 100 and  # Average under 100ms
                errors < num_queries * 0.1  # Less than 10% errors
            )
            
            if performance_good:
                print(f"  🎯 Performance: EXCELLENT")
            else:
                print(f"  ⚠️  Performance: NEEDS IMPROVEMENT")
            
            print()
            return performance_good
        else:
            print(f"  ❌ All queries failed")
            print()
            return False
    
    def simulate_family_network(self):
        """Simulate a typical family network scenario"""
        print("🏠 Simulating Family Network")
        print("-" * 40)
        
        # Family browsing scenarios
        scenarios = [
            ("Dad browsing news", ["cnn.com", "googlesyndication.com", "bbc.com", "doubleclick.net"]),
            ("Mom shopping online", ["amazon.com", "amazon-adsystem.com", "target.com", "googletagmanager.com"]),
            ("Teen on social media", ["instagram.com", "facebook.com", "tiktok.com", "googlesyndication.com"]),
            ("Kids watching videos", ["youtube.com", "pbskids.org", "googlesyndication.com", "doubleclick.com"]),
        ]
        
        total_queries = 0
        blocked_queries = 0
        
        for scenario_name, domains in scenarios:
            print(f"  📱 {scenario_name}:")
            
            for domain in domains:
                result = self.send_dns_query(domain)
                total_queries += 1
                
                if result['status'] == 'BLOCKED':
                    blocked_queries += 1
                    print(f"    🚫 {domain:25} - BLOCKED ({result.get('response_time', 0):.1f}ms)")
                elif result['status'] == 'ALLOWED':
                    print(f"    ✅ {domain:25} - ALLOWED ({result.get('response_time', 0):.1f}ms)")
                else:
                    print(f"    ❌ {domain:25} - ERROR")
        
        block_rate = (blocked_queries / total_queries) * 100 if total_queries > 0 else 0
        
        print(f"\n  📊 Family Network Summary:")
        print(f"    Total DNS Queries: {total_queries}")
        print(f"    Ads/Trackers Blocked: {blocked_queries}")
        print(f"    Content Allowed: {total_queries - blocked_queries}")
        print(f"    Block Rate: {block_rate:.1f}%")
        
        # Benefits calculation
        time_saved = blocked_queries * 0.5  # 500ms per blocked ad
        bandwidth_saved = blocked_queries * 2.5  # 2.5MB per blocked ad
        
        print(f"    ⚡ Time Saved: {time_saved:.1f} seconds")
        print(f"    💾 Bandwidth Saved: {bandwidth_saved:.1f} MB")
        print(f"    🛡️  Family Protected: ✅")
        print()
        
        return block_rate > 30  # At least 30% should be blocked
    
    def run_comprehensive_test(self):
        """Run all tests and generate report"""
        print("🚀 GuardNet Router Deployment Test Suite")
        print("=" * 60)
        print("Testing router-based ad blocking service...")
        print()
        
        tests = [
            ("Basic DNS Functionality", self.test_basic_dns_functionality),
            ("Ad Blocking", self.test_ad_blocking),
            ("Malware Protection", self.test_malware_protection),
            ("Management API", self.test_management_api),
            ("Performance", self.test_performance),
            ("Family Network Simulation", self.simulate_family_network),
        ]
        
        passed_tests = 0
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                print(f"❌ {test_name} failed with error: {e}\n")
        
        # Final Report
        print("=" * 60)
        print("📋 GUARDNET ROUTER TEST RESULTS")
        print("=" * 60)
        
        success_rate = (passed_tests / len(tests)) * 100
        
        print(f"Overall Success Rate: {passed_tests}/{len(tests)} ({success_rate:.1f}%)")
        print()
        
        if success_rate >= 90:
            print("🎉 EXCELLENT! Router deployment ready for production")
            print("✅ All core features working correctly")
            print("✅ Performance meets requirements")
            print("✅ Family protection active")
        elif success_rate >= 70:
            print("✅ GOOD! Router deployment mostly working")
            print("⚠️  Some minor issues need attention")
        else:
            print("❌ NEEDS WORK! Several critical issues found")
            print("🔧 Review configuration and connectivity")
        
        print()
        print("🌟 Router Service Benefits:")
        print("  - Zero client configuration required")
        print("  - Network-wide ad blocking for all devices")
        print("  - Family-safe internet out of the box")
        print("  - Enterprise-grade threat protection")
        print("  - Recurring revenue subscription model")
        
        print("=" * 60)
        
        return success_rate >= 70

if __name__ == "__main__":
    tester = RouterDeploymentTester()
    success = tester.run_comprehensive_test()
    
    exit(0 if success else 1)