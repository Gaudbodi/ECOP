#!/usr/bin/env python3
"""
Test script to verify Selenium scraping functionality for GHAAP website.
Specifically tests for finding element with ID="wt_smssend".
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scrape_weather import scrape_ghaap_with_selenium, build_ghaap_url
import json

def test_selenium_scraping():
    """Test Selenium scraping with different URLs and target elements."""
    
    print("=== Testing Selenium Scraping for GHAAP ===\n")
    
    # Test URLs
    test_urls = [
        build_ghaap_url(region="REG02", district="DS031", crop="CT0000000001", year="2025"),
        "https://ghaap.com/weather-forecast/index.php",
        "https://ghaap.com/weather-forecast/index.php?p=crop-search-event&regiontxt=REG02&districttxt=DS031&crop=CT0000000001&yeartxt=2025"
    ]
    
    # Test different target element IDs
    target_elements = [
        "wt_smssend",
        "wt_sms",
        "smssend",
        "advisory",
        "forecast"
    ]
    
    for i, url in enumerate(test_urls):
        print(f"\n--- Test {i+1}: {url} ---")
        
        for target_id in target_elements:
            print(f"\nTesting target element ID: {target_id}")
            
            try:
                result = scrape_ghaap_with_selenium(url, target_element_id=target_id, timeout=15)
                
                print(f"Success: {result.get('success', False)}")
                print(f"Target element found: {result.get('target_element_found', False)}")
                
                if result.get('target_element_found'):
                    target_text = result.get('target_element_text', '')
                    print(f"Target element text: {target_text[:200]}...")
                    
                    # Save successful result
                    with open(f"selenium_result_{target_id}.json", 'w', encoding='utf-8') as f:
                        json.dump(result, f, indent=2, ensure_ascii=False)
                    print(f"Result saved to selenium_result_{target_id}.json")
                    
                    return result  # Return first successful result
                
                additional_content = result.get('additional_content', [])
                if additional_content:
                    print(f"Found {len(additional_content)} additional content areas")
                    for j, content in enumerate(additional_content[:2]):
                        print(f"  Content {j+1}: {content[:100]}...")
                
                table_data = result.get('table_data', [])
                if table_data:
                    print(f"Found {len(table_data)} tables")
                    for table in table_data:
                        print(f"  Table {table['table_index']}: {table['row_count']} rows")
                
            except Exception as e:
                print(f"Error testing {target_id}: {e}")
        
        # If we found the target element, break
        if any(result.get('target_element_found', False) for result in []):
            break
    
    print("\n=== Test completed ===")
    return None

if __name__ == "__main__":
    test_selenium_scraping()
