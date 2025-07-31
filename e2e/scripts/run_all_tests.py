#!/usr/bin/env python3
"""
GuardNet E2E Test Runner
Comprehensive testing suite for all deployment scenarios
"""

import os
import sys
import time
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
import json

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def run_test_category(category: str, verbose: bool = False) -> Dict:
    """Run tests for a specific category"""
    test_dir = PROJECT_ROOT / "e2e" / "tests" / category
    
    if not test_dir.exists():
        return {"category": category, "status": "SKIPPED", "reason": "Directory not found"}
    
    print(f"\n🧪 Running {category.replace('_', ' ').title()} Tests...")
    print("=" * 50)
    
    # Count test files
    test_files = list(test_dir.glob("*.py"))
    if not test_files:
        return {"category": category, "status": "SKIPPED", "reason": "No test files found"}
    
    results = {
        "category": category,
        "status": "RUNNING", 
        "tests_run": 0,
        "tests_passed": 0,
        "tests_failed": 0,
        "start_time": time.time(),
        "test_files": []
    }
    
    for test_file in test_files:
        print(f"  🔍 Running {test_file.name}...")
        
        try:
            # Run the test file
            cmd = [sys.executable, str(test_file)]
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300,  # 5 minute timeout per test
                cwd=str(PROJECT_ROOT)
            )
            
            test_result = {
                "file": test_file.name,
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "duration": time.time() - results["start_time"]
            }
            
            if result.returncode == 0:
                print(f"    ✅ PASSED")
                results["tests_passed"] += 1
                test_result["status"] = "PASSED"
            else:
                print(f"    ❌ FAILED")
                results["tests_failed"] += 1
                test_result["status"] = "FAILED"
                if verbose:
                    print(f"    Error: {result.stderr}")
            
            results["test_files"].append(test_result)
            results["tests_run"] += 1
            
        except subprocess.TimeoutExpired:
            print(f"    ⏰ TIMEOUT")
            results["tests_failed"] += 1
            results["test_files"].append({
                "file": test_file.name,
                "status": "TIMEOUT",
                "error": "Test exceeded 5 minute timeout"
            })
        except Exception as e:
            print(f"    💥 ERROR: {e}")
            results["tests_failed"] += 1
            results["test_files"].append({
                "file": test_file.name,
                "status": "ERROR", 
                "error": str(e)
            })
    
    results["end_time"] = time.time()
    results["duration"] = results["end_time"] - results["start_time"]
    
    if results["tests_failed"] == 0:
        results["status"] = "PASSED"
        print(f"  ✅ All {category} tests passed!")
    else:
        results["status"] = "FAILED"
        print(f"  ❌ {results['tests_failed']} {category} tests failed")
    
    return results

def run_network_simulation_tests(duration: int = 60) -> Dict:
    """Run comprehensive network simulation tests"""
    print(f"\n🌐 Running Network Simulation Tests ({duration}s)...")
    print("=" * 50)
    
    try:
        from e2e.utils.network_sim import NetworkSimulator
        from e2e.utils.dns_client import DNSClient
        
        # Initialize DNS client pointing to GuardNet
        dns_client = DNSClient(server="127.0.0.1", port=8053)
        
        # Create network simulator
        sim = NetworkSimulator(dns_client)
        
        # Test 1: Family Network Simulation
        print("  📱 Creating family network...")
        family_devices = sim.create_family_network()
        
        def progress_callback(message):
            if "BLOCKED" in message:
                print(f"    🚫 {message}")
            elif "Starting" in message:
                print(f"    🚀 {message}")
        
        print(f"  🏃 Running {duration}s simulation with {len(family_devices)} devices...")
        family_results = sim.run_network_simulation(duration, progress_callback)
        
        # Test 2: Business Network Simulation
        sim.devices.clear()  # Clear family devices
        print("  🏢 Creating business network...")
        business_devices = sim.create_business_network()
        
        print(f"  🏃 Running {duration}s business simulation with {len(business_devices)} devices...")
        business_results = sim.run_network_simulation(duration, progress_callback)
        
        # Generate reports
        print("\n📊 Family Network Results:")
        print(sim.generate_report(family_results))
        
        print("\n📊 Business Network Results:")
        print(sim.generate_report(business_results))
        
        return {
            "status": "PASSED",
            "family_results": family_results,
            "business_results": business_results,
            "total_queries": family_results["total_queries"] + business_results["total_queries"],
            "total_blocked": family_results["blocked_queries"] + business_results["blocked_queries"]
        }
        
    except Exception as e:
        print(f"  💥 Network simulation failed: {e}")
        return {
            "status": "FAILED",
            "error": str(e)
        }

def check_guardnet_services() -> Dict:
    """Check if GuardNet services are running"""
    print("\n🔍 Checking GuardNet Services...")
    print("=" * 40)
    
    services_status = {}
    
    # Check DNS service
    try:
        result = subprocess.run(
            ["nslookup", "google.com", "127.0.0.1"],
            capture_output=True,
            text=True,
            timeout=10
        )
        services_status["dns_service"] = "RUNNING" if result.returncode == 0 else "FAILED"
        print(f"  DNS Service: {'✅' if result.returncode == 0 else '❌'}")
    except:
        services_status["dns_service"] = "FAILED"
        print("  DNS Service: ❌")
    
    # Check API Gateway
    try:
        import requests
        response = requests.get("http://localhost:3000/health", timeout=5)
        services_status["api_gateway"] = "RUNNING" if response.status_code == 200 else "FAILED"
        print(f"  API Gateway: {'✅' if response.status_code == 200 else '❌'}")
    except ImportError:
        services_status["api_gateway"] = "SKIPPED"
        print("  API Gateway: ⚠️  (requests module not available)")
    except:
        services_status["api_gateway"] = "FAILED"
        print("  API Gateway: ❌")
    
    # Check Dashboard
    try:
        import requests
        response = requests.get("http://localhost:3001", timeout=5)
        services_status["dashboard"] = "RUNNING" if response.status_code == 200 else "FAILED"
        print(f"  Dashboard: {'✅' if response.status_code == 200 else '❌'}")
    except ImportError:
        services_status["dashboard"] = "SKIPPED"
        print("  Dashboard: ⚠️  (requests module not available)")
    except:
        services_status["dashboard"] = "FAILED"
        print("  Dashboard: ❌")
    
    # Check Database
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="guardnet",
            user="guardnet", 
            password="dev-password"
        )
        conn.close()
        services_status["database"] = "RUNNING"
        print("  Database: ✅")
    except ImportError:
        services_status["database"] = "SKIPPED"
        print("  Database: ⚠️  (psycopg2 module not available)")
    except:
        services_status["database"] = "FAILED"
        print("  Database: ❌")
    
    return services_status

def generate_html_report(results: Dict, output_dir: Path):
    """Generate HTML test report"""
    output_dir.mkdir(parents=True, exist_ok=True)
    report_file = output_dir / "test_report.html"
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>GuardNet E2E Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #2196F3; color: white; padding: 20px; border-radius: 8px; }}
        .summary {{ background: #f5f5f5; padding: 15px; margin: 20px 0; border-radius: 8px; }}
        .test-category {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }}
        .passed {{ color: #4CAF50; }}
        .failed {{ color: #f44336; }}
        .skipped {{ color: #ff9800; }}
        .test-details {{ margin-left: 20px; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ GuardNet E2E Test Report</h1>
        <p>Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="summary">
        <h2>📊 Test Summary</h2>
        <p><strong>Total Categories:</strong> {len([r for r in results['categories'] if r['status'] != 'SKIPPED'])}</p>
        <p><strong>Total Tests:</strong> {sum(r.get('tests_run', 0) for r in results['categories'])}</p>
        <p><strong>Passed:</strong> <span class="passed">{sum(r.get('tests_passed', 0) for r in results['categories'])}</span></p>
        <p><strong>Failed:</strong> <span class="failed">{sum(r.get('tests_failed', 0) for r in results['categories'])}</span></p>
        <p><strong>Duration:</strong> {results.get('total_duration', 0):.1f} seconds</p>
    </div>
    
    <div class="test-category">
        <h2>🏥 Service Health Check</h2>
        {''.join([f'<p><strong>{service}:</strong> <span class="{"passed" if status == "RUNNING" else "failed"}">{status}</span></p>' for service, status in results.get('service_status', {}).items()])}
    </div>
"""
    
    # Add category results
    for category_result in results.get('categories', []):
        status_class = category_result['status'].lower()
        html_content += f"""
    <div class="test-category">
        <h2>🧪 {category_result['category'].replace('_', ' ').title()} Tests</h2>
        <p><strong>Status:</strong> <span class="{status_class}">{category_result['status']}</span></p>
        <p><strong>Duration:</strong> {category_result.get('duration', 0):.1f}s</p>
        
        <div class="test-details">
"""
        
        for test_file in category_result.get('test_files', []):
            test_status_class = test_file['status'].lower()
            html_content += f"""
            <p><strong>{test_file['file']}:</strong> <span class="{test_status_class}">{test_file['status']}</span></p>
"""
        
        html_content += "</div></div>"
    
    # Add network simulation results
    if 'network_simulation' in results:
        sim_result = results['network_simulation']
        html_content += f"""
    <div class="test-category">
        <h2>🌐 Network Simulation Results</h2>
        <p><strong>Status:</strong> <span class="{"passed" if sim_result['status'] == 'PASSED' else "failed"}">{sim_result['status']}</span></p>
        <p><strong>Total Queries:</strong> {sim_result.get('total_queries', 0)}</p>
        <p><strong>Total Blocked:</strong> {sim_result.get('total_blocked', 0)}</p>
    </div>
"""
    
    html_content += """
</body>
</html>"""
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"📄 HTML report generated: {report_file}")

def main():
    parser = argparse.ArgumentParser(description="GuardNet E2E Test Runner")
    parser.add_argument("--category", help="Run specific test category")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--report-html", help="Generate HTML report to directory")
    parser.add_argument("--simulation-duration", type=int, default=60, help="Network simulation duration (seconds)")
    parser.add_argument("--skip-services-check", action="store_true", help="Skip service health check")
    
    args = parser.parse_args()
    
    print("🛡️ GuardNet E2E Test Suite")
    print("=" * 50)
    
    start_time = time.time()
    results = {
        "start_time": start_time,
        "categories": [],
        "service_status": {},
        "network_simulation": {}
    }
    
    # Check service status first
    if not args.skip_services_check:
        results["service_status"] = check_guardnet_services()
    
    # Define test categories
    test_categories = [
        "dns_filtering",
        "ad_blocking", 
        "threat_intel",
        "router_deployment",
        "network_simulation",
        "performance"
    ]
    
    if args.category:
        if args.category in test_categories:
            test_categories = [args.category]
        else:
            print(f"❌ Unknown category: {args.category}")
            print(f"Available categories: {', '.join(test_categories)}")
            sys.exit(1)
    
    # Run test categories
    for category in test_categories:
        if category == "network_simulation" and not args.category:
            # Run network simulation separately
            results["network_simulation"] = run_network_simulation_tests(args.simulation_duration)
        else:
            category_result = run_test_category(category, args.verbose)
            results["categories"].append(category_result)
    
    # Calculate totals
    results["end_time"] = time.time()
    results["total_duration"] = results["end_time"] - start_time
    
    total_tests = sum(r.get('tests_run', 0) for r in results['categories'])
    total_passed = sum(r.get('tests_passed', 0) for r in results['categories'])
    total_failed = sum(r.get('tests_failed', 0) for r in results['categories'])
    
    print(f"\n🏁 Test Suite Complete!")
    print("=" * 50)
    print(f"⏱️  Total Duration: {results['total_duration']:.1f} seconds")
    print(f"🧪 Total Tests: {total_tests}")
    print(f"✅ Passed: {total_passed}")
    print(f"❌ Failed: {total_failed}")
    
    if results['network_simulation']:
        sim_status = results['network_simulation']['status']
        print(f"🌐 Network Simulation: {'✅' if sim_status == 'PASSED' else '❌'} {sim_status}")
    
    # Generate HTML report if requested
    if args.report_html:
        generate_html_report(results, Path(args.report_html))
    
    # Exit with error if any tests failed
    if total_failed > 0 or (results['network_simulation'] and results['network_simulation']['status'] != 'PASSED'):
        sys.exit(1)
    
    print("\n🎉 All tests passed! GuardNet is ready for deployment.")

if __name__ == "__main__":
    main()