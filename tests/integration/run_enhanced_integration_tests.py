#!/usr/bin/env python3
"""
Enhanced Integration Test Runner

This script runs all enhanced integration tests with proper categorization,
reporting, and performance metrics.
"""

import asyncio
import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

def run_test_category(category_name, test_files, description):
    """Run a specific category of integration tests."""
    print(f"\n{'='*80}")
    print(f"🧪 RUNNING {category_name.upper()} TESTS")
    print(f"📝 {description}")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    # Run tests using pytest
    import subprocess
    
    test_paths = [f"tests/integration/{file}" for file in test_files]
    cmd = [
        sys.executable, "-m", "pytest",
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--durations=10",  # Show top 10 slowest tests
        "--color=yes",  # Colored output
        *test_paths
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n📊 {category_name} Test Results:")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"🔢 Exit Code: {result.returncode}")
        
        if result.stdout:
            print(f"\n📤 STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print(f"\n⚠️  STDERR:")
            print(result.stderr)
        
        return {
            "category": category_name,
            "duration": duration,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
        
    except subprocess.TimeoutExpired:
        print(f"⏰ {category_name} tests timed out after 5 minutes")
        return {
            "category": category_name,
            "duration": 300,
            "exit_code": -1,
            "stdout": "",
            "stderr": "Test timeout",
            "success": False
        }
    except Exception as e:
        print(f"❌ Error running {category_name} tests: {e}")
        return {
            "category": category_name,
            "duration": 0,
            "exit_code": -1,
            "stdout": "",
            "stderr": str(e),
            "success": False
        }

def generate_test_report(results):
    """Generate a comprehensive test report."""
    print(f"\n{'='*80}")
    print("📋 ENHANCED INTEGRATION TEST REPORT")
    print(f"🕐 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}")
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r["success"])
    failed_tests = total_tests - successful_tests
    total_duration = sum(r["duration"] for r in results)
    
    print(f"\n📈 SUMMARY:")
    print(f"✅ Successful Categories: {successful_tests}/{total_tests}")
    print(f"❌ Failed Categories: {failed_tests}/{total_tests}")
    print(f"⏱️  Total Duration: {total_duration:.2f} seconds")
    print(f"📊 Success Rate: {(successful_tests/total_tests)*100:.1f}%")
    
    print(f"\n📋 DETAILED RESULTS:")
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{status} {result['category']:<30} {result['duration']:>8.2f}s")
    
    if failed_tests > 0:
        print(f"\n🚨 FAILED CATEGORIES:")
        for result in results:
            if not result["success"]:
                print(f"❌ {result['category']}: {result['stderr']}")
    
    # Save detailed report to file
    report_file = f"integration_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_categories": total_tests,
                "successful_categories": successful_tests,
                "failed_categories": failed_tests,
                "success_rate": (successful_tests/total_tests)*100,
                "total_duration": total_duration
            },
            "results": results
        }, f, indent=2)
    
    print(f"\n💾 Detailed report saved to: {report_file}")
    
    return successful_tests == total_tests

def main():
    """Main test runner function."""
    print("🚀 ENHANCED INTEGRATION TEST SUITE")
    print("="*80)
    
    # Define test categories
    test_categories = [
        {
            "name": "Discovery Service",
            "files": ["test_discovery_integration.py"],
            "description": "Tests for OpenShift discovery service functionality and recent bug fixes"
        },
        {
            "name": "Configuration",
            "files": ["test_configuration_integration.py"],
            "description": "Tests for configuration validation and OpenAI proxy features"
        },
        {
            "name": "Error Scenarios",
            "files": ["test_error_scenarios_integration.py"],
            "description": "Tests for comprehensive error handling and edge cases"
        },
        {
            "name": "Original Integration",
            "files": ["test_mcp_integration.py"],
            "description": "Original integration tests for basic functionality"
        }
    ]
    
    # Check if test files exist
    for category in test_categories:
        for file in category["files"]:
            file_path = Path(f"tests/integration/{file}")
            if not file_path.exists():
                print(f"⚠️  Warning: Test file {file} not found, skipping category {category['name']}")
                category["files"] = [f for f in category["files"] if Path(f"tests/integration/{f}").exists()]
    
    # Run tests for each category
    results = []
    for category in test_categories:
        if category["files"]:  # Only run if files exist
            result = run_test_category(
                category["name"],
                category["files"],
                category["description"]
            )
            results.append(result)
        else:
            print(f"⏭️  Skipping {category['name']} - no test files found")
    
    # Generate comprehensive report
    all_passed = generate_test_report(results)
    
    # Exit with appropriate code
    if all_passed:
        print(f"\n🎉 ALL INTEGRATION TESTS PASSED!")
        sys.exit(0)
    else:
        print(f"\n💥 SOME INTEGRATION TESTS FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    main() 