#!/usr/bin/env python3
"""
RAG (Retrieval Augmented Generation) Assistant
Professional CLI tool for building and testing RAG systems
"""

import argparse
import json
import sys
import os
import requests
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    import psycopg
except ImportError:
    print("❌ psycopg not installed. Run: pip install psycopg[binary]")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed. Environment variables must be set manually.")
    pass

@dataclass
class RAGResult:
    query: str
    context: List[Dict[str, Any]]
    response: str
    metadata: Dict[str, Any]
    
    def __str__(self):
        return f"Query: {self.query}\nResponse: {self.response[:200]}..."

class RAGAssistant:
    def __init__(self, config_file: str = "rag_config.json"):
        self.config = self.load_config(config_file)
        
    def load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  Config file {config_file} not found, using defaults")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            "database": {
                "host": "localhost",
                "port": "5050",
                "database": "pgvector",
                "user": "postgres",
                "password": "postgres"
            },
            "embedding": {
                "model": "bge-m3",
                "ollama_url": "http://localhost:11434/api/embed"
            },
            "llm": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "api_key_env": "OPENAI_API_KEY",
                "base_url": "https://api.openai.com/v1/chat/completions",
                "temperature": 0.7,
                "max_tokens": 400
            }
        }
    
    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding using Ollama"""
        try:
            payload = {
                "model": self.config['embedding']['model'], 
                "input": text
            }
            response = requests.post(
                self.config['embedding']['ollama_url'], 
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["embeddings"][0]
            else:
                raise Exception(f"Ollama API error: {response.text}")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to connect to Ollama: {e}")
    
    def get_db_connection(self):
        """Get database connection"""
        try:
            db_config = self.config['database']
            return psycopg.connect(
                host=db_config['host'],
                port=db_config['port'],
                dbname=db_config['database'],
                user=db_config['user'],
                password=db_config['password']
            )
        except Exception as e:
            raise Exception(f"Database connection failed: {e}")
    
    def retrieve_context(
        self, 
        query: str, 
        limit: int = 5, 
        similarity_threshold: Optional[float] = None,
        subject_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant context from database"""
        
        print(f"🔍 Retrieving context for: '{query}'")
        
        # Generate embedding
        try:
            query_embedding = self.get_embedding(query)
            print(f"✅ Query embedding generated ({len(query_embedding)} dimensions)")
        except Exception as e:
            print(f"❌ Embedding generation failed: {e}")
            return []
        
        # Build SQL query
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        
        sql_parts = [
            "SELECT name, item_data, embedding <=> %s as similarity",
            "FROM items"
        ]
        
        params = [embedding_str]
        
        # Add filters
        where_conditions = []
        if similarity_threshold is not None:
            where_conditions.append("embedding <=> %s < %s")
            params.extend([embedding_str, similarity_threshold])
        
        if subject_filter:
            where_conditions.append("item_data->>'subject' = %s")
            params.append(subject_filter)
        
        if where_conditions:
            sql_parts.append("WHERE " + " AND ".join(where_conditions))
        
        sql_parts.extend([
            "ORDER BY embedding <=> %s",
            "LIMIT %s"
        ])
        
        params.extend([embedding_str, limit])
        
        sql = " ".join(sql_parts)
        
        # Execute query
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    print(f"📊 Executing similarity search...")
                    cursor.execute(sql, params)
                    results = cursor.fetchall()
                    
                    context = []
                    for name, item_data, similarity in results:
                        context.append({
                            "name": name,
                            "data": item_data,
                            "similarity": float(similarity)
                        })
                    
                    print(f"✅ Retrieved {len(context)} relevant items")
                    return context
                    
        except Exception as e:
            print(f"❌ Database query failed: {e}")
            return []
    
    def format_context(self, context: List[Dict[str, Any]], template: str = "default") -> str:
        """Format context for LLM consumption"""
        if not context:
            return "No relevant context found."
        
        if template == "simple":
            return "\n".join([f"- {item['name']}" for item in context])
        
        elif template == "detailed":
            formatted = []
            for i, item in enumerate(context, 1):
                data = item['data']
                authors = data.get('authors', ['Unknown'])
                if isinstance(authors, list):
                    authors_str = ", ".join(authors)
                else:
                    authors_str = str(authors)
                
                formatted.append(
                    f"{i}. \"{item['name']}\" by {authors_str}\n"
                    f"   - Subject: {data.get('subject', 'Unknown')}\n"
                    f"   - Relevance: {item['similarity']:.3f}"
                )
            return "\n\n".join(formatted)
        
        else:  # default
            formatted = []
            for item in context:
                data = item['data']
                subject = data.get('subject', 'Unknown')
                formatted.append(f"- \"{item['name']}\" (Subject: {subject}, Similarity: {item['similarity']:.3f})")
            return "\n".join(formatted)
    
    def query_llm(self, prompt: str, temperature: Optional[float] = None) -> str:
        """Query LLM with the given prompt"""
        llm_config = self.config['llm']
        
        if llm_config['provider'] == 'openai':
            return self._query_openai(prompt, temperature)
        elif llm_config['provider'] == 'ollama':
            return self._query_ollama(prompt, temperature)
        else:
            raise Exception(f"Unsupported LLM provider: {llm_config['provider']}")
    
    def _query_openai(self, prompt: str, temperature: Optional[float] = None) -> str:
        """Query OpenAI ChatGPT API"""
        llm_config = self.config['llm']
        
        # Get API key from environment
        api_key_env = llm_config.get('api_key_env', 'OPENAI_API_KEY')
        api_key = os.getenv(api_key_env)
        
        if not api_key:
            return f"❌ Error: {api_key_env} environment variable not set. Please set your OpenAI API key."
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": llm_config['model'],
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature or llm_config['temperature'],
            "max_tokens": llm_config.get('max_tokens', 400)
        }
        
        try:
            print(f"🤖 Querying {llm_config['model']}...")
            response = requests.post(
                llm_config['base_url'],
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content']
            else:
                return f"❌ OpenAI API Error: {response.status_code}, {response.text}"
                
        except Exception as e:
            return f"❌ LLM query failed: {e}"
    
    def _query_ollama(self, prompt: str, temperature: Optional[float] = None) -> str:
        """Query Ollama LLM (fallback option)"""
        llm_config = self.config['llm']
        
        payload = {
            "model": llm_config['model'],
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature or llm_config['temperature'],
                "num_predict": llm_config.get('max_tokens', 400)
            }
        }
        
        try:
            print(f"🤖 Querying {llm_config['model']}...")
            response = requests.post(
                llm_config['base_url'],
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('response', 'No response generated')
            else:
                return f"❌ Ollama API Error: {response.status_code}, {response.text}"
                
        except Exception as e:
            return f"❌ LLM query failed: {e}"
    
    def build_prompt(
        self, 
        query: str, 
        context: List[Dict[str, Any]], 
        template_name: str = "default"
    ) -> str:
        """Build prompt from query and context"""
        
        templates = self.config.get('prompt_templates', {})
        
        if template_name in templates:
            template = templates[template_name]
            system_prompt = template.get('system', '')
            user_template = template.get('user_template', '{query}\n\nContext:\n{context}')
            
            formatted_context = self.format_context(context, "detailed")
            user_prompt = user_template.format(query=query, context=formatted_context)
            
            if system_prompt:
                return f"System: {system_prompt}\n\nUser: {user_prompt}"
            else:
                return user_prompt
        else:
            # Default template
            formatted_context = self.format_context(context, "default")
            return f"Question: {query}\n\nRelevant information:\n{formatted_context}\n\nPlease provide a helpful response based on the above information."
    
    def run_rag_query(
        self,
        query: str,
        context_limit: int = 5,
        similarity_threshold: Optional[float] = None,
        subject_filter: Optional[str] = None,
        prompt_template: str = "default",
        llm_temperature: Optional[float] = None,
        no_context: bool = False
    ) -> RAGResult:
        """Run complete RAG pipeline"""
        
        print(f"🚀 Running RAG query: '{query}'")
        print("=" * 60)
        
        # Retrieve context (unless disabled)
        if no_context:
            print("⚠️  Running without context (LLM only)")
            context = []
        else:
            context = self.retrieve_context(
                query, 
                limit=context_limit,
                similarity_threshold=similarity_threshold,
                subject_filter=subject_filter
            )
        
        # Build prompt
        prompt = self.build_prompt(query, context, prompt_template)
        
        # Query LLM
        response = self.query_llm(prompt, llm_temperature)
        
        # Prepare result
        metadata = {
            "context_count": len(context),
            "similarity_threshold": similarity_threshold,
            "subject_filter": subject_filter,
            "prompt_template": prompt_template,
            "llm_temperature": llm_temperature or self.config['llm']['temperature']
        }
        
        return RAGResult(
            query=query,
            context=context,
            response=response,
            metadata=metadata
        )
    
    def run_configured_scenarios(self) -> None:
        """Run all configured RAG scenarios"""
        scenarios = self.config.get('scenarios', [])
        
        if not scenarios:
            print("⚠️  No scenarios configured")
            return
        
        print("🚀 Running configured RAG scenarios...")
        print("=" * 60)
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n🔸 Scenario {i}: {scenario['name']}")
            print(f"📝 Description: {scenario['description']}")
            print("-" * 40)
            
            result = self.run_rag_query(
                query=scenario['query'],
                context_limit=scenario.get('context_limit', 5),
                similarity_threshold=scenario.get('similarity_threshold'),
                subject_filter=scenario.get('filter_subject'),
                prompt_template=scenario.get('prompt_template', 'default'),
                llm_temperature=scenario.get('llm_temperature')
            )
            
            print(f"\n📋 Context found: {len(result.context)} items")
            if result.context:
                print("   " + "\n   ".join([f"- {item['name']}" for item in result.context[:3]]))
                if len(result.context) > 3:
                    print(f"   ... and {len(result.context) - 3} more")
            
            print(f"\n🤖 LLM Response:")
            print(result.response)
            print()
    
    def run_experiments(self) -> None:
        """Run configured experiments"""
        experiments = self.config.get('experiments', [])
        
        if not experiments:
            print("⚠️  No experiments configured")
            return
        
        print("🧪 Running RAG experiments...")
        print("=" * 60)
        
        for experiment in experiments:
            print(f"\n🔬 Experiment: {experiment['name']}")
            print(f"📝 Description: {experiment['description']}")
            print("-" * 40)
            
            if experiment['name'] == "Context Amount Impact":
                self._run_context_amount_experiment(experiment)
            elif experiment['name'] == "Temperature Effect":
                self._run_temperature_experiment(experiment)
            elif experiment['name'] == "Prompt Template Comparison":
                self._run_template_experiment(experiment)
            elif experiment['name'] == "Context Quality vs Quantity":
                self._run_quality_quantity_experiment(experiment)
    
    def _run_context_amount_experiment(self, experiment: Dict[str, Any]) -> None:
        """Run context amount experiment"""
        query = experiment['base_query']
        context_limits = experiment['context_limits']
        subject_filter = experiment.get('filter_subject')
        
        print(f"🔍 Base query: '{query}'")
        
        for limit in context_limits:
            print(f"\n📊 Context limit: {limit}")
            result = self.run_rag_query(
                query, 
                context_limit=limit, 
                subject_filter=subject_filter
            )
            print(f"   Response length: {len(result.response)} characters")
            print(f"   First 100 chars: {result.response[:100]}...")
    
    def _run_temperature_experiment(self, experiment: Dict[str, Any]) -> None:
        """Run temperature experiment"""
        query = experiment['base_query']
        temperatures = experiment['temperatures']
        context_limit = experiment.get('context_limit', 4)
        subject_filter = experiment.get('filter_subject')
        
        print(f"🔍 Base query: '{query}'")
        
        for temp in temperatures:
            print(f"\n🌡️  Temperature: {temp}")
            result = self.run_rag_query(
                query,
                context_limit=context_limit,
                subject_filter=subject_filter,
                llm_temperature=temp
            )
            print(f"   Response: {result.response[:150]}...")
    
    def _run_template_experiment(self, experiment: Dict[str, Any]) -> None:
        """Run template comparison experiment"""
        query = experiment['base_query']
        templates = experiment['templates']
        context_limit = experiment.get('context_limit', 3)
        subject_filter = experiment.get('filter_subject')
        
        print(f"🔍 Base query: '{query}'")
        
        for template in templates:
            print(f"\n📝 Template: {template}")
            result = self.run_rag_query(
                query,
                context_limit=context_limit,
                subject_filter=subject_filter,
                prompt_template=template
            )
            print(f"   Response: {result.response[:150]}...")
    
    def _run_quality_quantity_experiment(self, experiment: Dict[str, Any]) -> None:
        """Run quality vs quantity experiment"""
        query = experiment['base_query']
        scenarios = experiment['scenarios']
        subject_filter = experiment.get('filter_subject')
        
        print(f"🔍 Base query: '{query}'")
        
        for scenario in scenarios:
            print(f"\n📊 Scenario: {scenario['name']}")
            result = self.run_rag_query(
                query,
                context_limit=scenario['context_limit'],
                similarity_threshold=scenario['similarity_threshold'],
                subject_filter=subject_filter
            )
            print(f"   Context items: {len(result.context)}")
            print(f"   Response: {result.response[:150]}...")

def main():
    parser = argparse.ArgumentParser(
        description="RAG Assistant - Professional Retrieval Augmented Generation tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --query "Best books for learning Python" --context-limit 5
  %(prog)s --query "AI fundamentals" --subject ai --temperature 0.3
  %(prog)s --query "Web frameworks" --no-context  # LLM only, no RAG
  %(prog)s --scenarios  # Run all configured scenarios
  %(prog)s --experiments  # Run all configured experiments
        """
    )
    
    parser.add_argument('--query', '-q', type=str, help='User query for RAG system')
    parser.add_argument('--context-limit', '-l', type=int, default=5, 
                       help='Number of context items to retrieve (default: 5)')
    parser.add_argument('--similarity-threshold', '-t', type=float, 
                       help='Similarity threshold (0.0-1.0)')
    parser.add_argument('--subject', '-s', type=str, help='Filter by subject')
    parser.add_argument('--template', type=str, default='default',
                       help='Prompt template to use')
    parser.add_argument('--temperature', type=float, help='LLM temperature (0.0-1.0)')
    parser.add_argument('--no-context', action='store_true',
                       help='Run without context (LLM only)')
    parser.add_argument('--config', '-c', type=str, default='rag_config.json',
                       help='Configuration file (default: rag_config.json)')
    parser.add_argument('--scenarios', action='store_true', 
                       help='Run all configured RAG scenarios')
    parser.add_argument('--experiments', action='store_true',
                       help='Run all configured experiments')
    
    args = parser.parse_args()
    
    # Initialize assistant
    try:
        assistant = RAGAssistant(args.config)
    except Exception as e:
        print(f"❌ Failed to initialize RAG assistant: {e}")
        sys.exit(1)
    
    # Run based on arguments
    if args.scenarios:
        assistant.run_configured_scenarios()
    elif args.experiments:
        assistant.run_experiments()
    elif args.query:
        result = assistant.run_rag_query(
            query=args.query,
            context_limit=args.context_limit,
            similarity_threshold=args.similarity_threshold,
            subject_filter=args.subject,
            prompt_template=args.template,
            llm_temperature=args.temperature,
            no_context=args.no_context
        )
        
        print("\n" + "="*60)
        print("📋 RAG RESULT")
        print("="*60)
        print(f"Query: {result.query}")
        print(f"Context items: {len(result.context)}")
        
        if result.context:
            print("\nRetrieved context:")
            for i, item in enumerate(result.context, 1):
                print(f"  {i}. {item['name']} (similarity: {item['similarity']:.3f})")
        
        print(f"\nLLM Response:")
        print(result.response)
        
        print(f"\nMetadata: {result.metadata}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 