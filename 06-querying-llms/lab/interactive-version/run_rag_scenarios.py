#!/usr/bin/env python3
"""
Run Configured RAG Scenarios
Simple script to execute all RAG scenarios defined in rag_config.json
"""

import json
import sys
from rag_assistant import RAGAssistant

def main():
    print("🚀 RAG Scenarios Runner")
    print("=" * 50)
    
    try:
        # Initialize RAG assistant
        assistant = RAGAssistant()
        
        # Run all configured RAG scenarios
        print("Running all configured scenarios...")
        assistant.run_configured_scenarios()
        
        print("\n🎯 Want to run experiments too?")
        response = input("Run experiments? (y/n): ").strip().lower()
        
        if response in ['y', 'yes']:
            print("\n" + "=" * 50)
            assistant.run_experiments()
        
        print("\n✅ All scenarios completed!")
        print("\n💡 Tips:")
        print("- Edit rag_config.json to customize scenarios")
        print("- Use rag_assistant.py --query 'your question' for custom queries")
        print("- Try --no-context to compare LLM-only vs RAG responses")
        print("- Experiment with different --temperature values")
        
    except FileNotFoundError:
        print("❌ rag_config.json not found!")
        print("Please make sure the configuration file exists.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running scenarios: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 