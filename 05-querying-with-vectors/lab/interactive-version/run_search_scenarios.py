#!/usr/bin/env python3
"""
Run Configured Search Scenarios
Simple script to execute all search scenarios defined in search_config.json
"""

import json
import sys
from search_assistant import VectorSearchAssistant

def main():
    print("🚀 Vector Search Scenarios Runner")
    print("=" * 50)
    
    try:
        # Initialize search assistant
        assistant = VectorSearchAssistant()
        
        # Run all configured search scenarios
        assistant.run_configured_searches()
        
        print("\n🎯 Want to run experiments too?")
        response = input("Run experiments? (y/n): ").strip().lower()
        
        if response in ['y', 'yes']:
            print("\n" + "=" * 50)
            assistant.run_experiments()
        
        print("\n✅ All scenarios completed!")
        print("\n💡 Tips:")
        print("- Edit search_config.json to customize searches")
        print("- Use search_assistant.py --interactive for custom queries")
        print("- Try generate_search_embedding.py for SQL queries")
        
    except FileNotFoundError:
        print("❌ search_config.json not found!")
        print("Please make sure the configuration file exists.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running scenarios: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 