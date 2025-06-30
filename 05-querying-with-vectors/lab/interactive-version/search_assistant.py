#!/usr/bin/env python3
"""
Interactive Vector Search Assistant
Professional CLI tool for vector similarity search
"""

import argparse
import json
import sys
import os
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    import psycopg
except ImportError:
    print("❌ psycopg not installed. Run: pip install psycopg[binary]")
    sys.exit(1)

@dataclass
class SearchResult:
    name: str
    subject: str
    similarity: float
    
    def __str__(self):
        return f"📖 {self.name}\n   📂 Subject: {self.subject}\n   📊 Similarity: {self.similarity:.4f}"

class VectorSearchAssistant:
    def __init__(self, config_file: str = "search_config.json"):
        self.config = self.load_config(config_file)
        
    def load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  Config file {config_file} not found, using defaults")
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
    
    def search_similar(
        self, 
        query: str, 
        limit: int = 5, 
        threshold: Optional[float] = None,
        subject_filter: Optional[str] = None,
        distance_metric: str = "cosine"
    ) -> List[SearchResult]:
        """Perform vector similarity search"""
        
        print(f"🔍 Searching for: '{query}'")
        print(f"📊 Generating embedding...")
        
        # Generate embedding
        try:
            query_embedding = self.get_embedding(query)
            print(f"✅ Embedding generated ({len(query_embedding)} dimensions)")
        except Exception as e:
            print(f"❌ Embedding generation failed: {e}")
            return []
        
        # Choose distance operator
        distance_ops = {
            "cosine": "<=>",
            "euclidean": "<->", 
            "inner_product": "<#>"
        }
        
        if distance_metric not in distance_ops:
            print(f"⚠️  Unknown distance metric '{distance_metric}', using cosine")
            distance_metric = "cosine"
        
        distance_op = distance_ops[distance_metric]
        
        # Build SQL query
        embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
        
        sql_parts = [
            "SELECT name, item_data->>'subject' as subject,",
            f"ROUND((embedding {distance_op} %s)::numeric, 4) as similarity",
            "FROM items"
        ]
        
        params = [embedding_str]
        
        # Add filters
        where_conditions = []
        if threshold is not None:
            where_conditions.append(f"embedding {distance_op} %s < %s")
            params.extend([embedding_str, threshold])
        
        if subject_filter:
            where_conditions.append("item_data->>'subject' = %s")
            params.append(subject_filter)
        
        if where_conditions:
            sql_parts.append("WHERE " + " AND ".join(where_conditions))
        
        sql_parts.extend([
            f"ORDER BY embedding {distance_op} %s",
            "LIMIT %s"
        ])
        
        params.extend([embedding_str, limit])
        
        sql = " ".join(sql_parts)
        
        # Execute query
        try:
            with self.get_db_connection() as conn:
                with conn.cursor() as cursor:
                    print(f"🔍 Executing {distance_metric} similarity search...")
                    cursor.execute(sql, params)
                    results = cursor.fetchall()
                    
                    return [
                        SearchResult(name=row[0], subject=row[1] or "Unknown", similarity=float(row[2]))
                        for row in results
                    ]
        except Exception as e:
            print(f"❌ Database query failed: {e}")
            return []
    
    def run_configured_searches(self) -> None:
        """Run all configured search scenarios"""
        if 'searches' not in self.config:
            print("⚠️  No configured searches found in config file")
            return
        
        print("🚀 Running configured search scenarios...")
        print("=" * 60)
        
        for i, search in enumerate(self.config['searches'], 1):
            print(f"\n🔸 Scenario {i}: {search['name']}")
            print(f"📝 Description: {search['description']}")
            print("-" * 40)
            
            results = self.search_similar(
                query=search['query'],
                limit=search['limit'],
                threshold=search.get('similarity_threshold'),
                subject_filter=search.get('filter_subject')
            )
            
            if results:
                for j, result in enumerate(results, 1):
                    print(f"{j}. {result}")
            else:
                print("❌ No results found")
            
            print()
    
    def run_experiments(self) -> None:
        """Run configured experiments"""
        if 'experiments' not in self.config:
            print("⚠️  No experiments configured")
            return
        
        print("🧪 Running experiments...")
        print("=" * 60)
        
        for experiment in self.config['experiments']:
            print(f"\n🔬 Experiment: {experiment['name']}")
            print(f"📝 Description: {experiment['description']}")
            print("-" * 40)
            
            if experiment['name'] == "Similarity Threshold Comparison":
                self._run_threshold_experiment(experiment)
            elif experiment['name'] == "Distance Metric Comparison":
                self._run_metric_experiment(experiment)
            elif experiment['name'] == "Query Specificity Impact":
                self._run_specificity_experiment(experiment)
    
    def _run_threshold_experiment(self, experiment: Dict[str, Any]) -> None:
        """Run similarity threshold comparison"""
        query = experiment['base_query']
        thresholds = experiment['thresholds']
        
        print(f"🔍 Base query: '{query}'")
        
        for threshold in thresholds:
            print(f"\n📊 Threshold: {threshold}")
            results = self.search_similar(query, limit=3, threshold=threshold)
            print(f"   Found {len(results)} results")
            if results:
                best_result = results[0]
                print(f"   Best match: {best_result.name} (similarity: {best_result.similarity:.4f})")
    
    def _run_metric_experiment(self, experiment: Dict[str, Any]) -> None:
        """Run distance metric comparison"""
        query = experiment['base_query']
        metrics = experiment['metrics']
        
        print(f"🔍 Base query: '{query}'")
        
        for metric in metrics:
            print(f"\n📊 Distance metric: {metric}")
            results = self.search_similar(query, limit=3, distance_metric=metric)
            if results:
                best_result = results[0]
                print(f"   Best match: {best_result.name} (score: {best_result.similarity:.4f})")
    
    def _run_specificity_experiment(self, experiment: Dict[str, Any]) -> None:
        """Run query specificity comparison"""
        queries = experiment['queries']
        
        for i, query in enumerate(queries, 1):
            print(f"\n📊 Query {i}: '{query}'")
            results = self.search_similar(query, limit=2)
            if results:
                best_result = results[0]
                print(f"   Best match: {best_result.name} (similarity: {best_result.similarity:.4f})")
    
    def interactive_mode(self) -> None:
        """Run in interactive mode"""
        print("🎯 Interactive Vector Search Mode")
        print("Type 'quit' to exit, 'help' for commands")
        print("-" * 40)
        
        while True:
            try:
                query = input("\n🔍 Enter search query: ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                elif query.lower() == 'help':
                    self._show_help()
                    continue
                elif not query:
                    continue
                
                # Parse optional parameters
                parts = query.split(' --')
                search_query = parts[0]
                
                # Default parameters
                limit = 5
                threshold = None
                subject_filter = None
                distance_metric = "cosine"
                
                # Parse parameters
                for part in parts[1:]:
                    if part.startswith('limit '):
                        limit = int(part.split(' ', 1)[1])
                    elif part.startswith('threshold '):
                        threshold = float(part.split(' ', 1)[1])
                    elif part.startswith('subject '):
                        subject_filter = part.split(' ', 1)[1]
                    elif part.startswith('metric '):
                        distance_metric = part.split(' ', 1)[1]
                
                results = self.search_similar(
                    search_query, 
                    limit=limit, 
                    threshold=threshold,
                    subject_filter=subject_filter,
                    distance_metric=distance_metric
                )
                
                if results:
                    print(f"\n📋 Found {len(results)} results:")
                    for i, result in enumerate(results, 1):
                        print(f"{i}. {result}")
                else:
                    print("❌ No results found")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def _show_help(self) -> None:
        """Show help information"""
        print("""
📖 HELP - Interactive Search Commands

Basic search:
  artificial intelligence

With parameters:
  machine learning --limit 10
  python programming --threshold 0.6
  web development --subject programming
  data science --metric euclidean

Available parameters:
  --limit N          : Number of results (default: 5)
  --threshold N      : Similarity threshold (0.0-1.0)
  --subject NAME     : Filter by subject (ai, programming, web_development)
  --metric NAME      : Distance metric (cosine, euclidean, inner_product)

Special commands:
  help              : Show this help
  quit              : Exit interactive mode
        """)

def main():
    parser = argparse.ArgumentParser(
        description="Vector Search Assistant - Professional vector similarity search tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --query "machine learning algorithms" --limit 5
  %(prog)s --query "web development" --subject programming --threshold 0.6
  %(prog)s --scenarios  # Run all configured search scenarios
  %(prog)s --experiments  # Run all configured experiments
  %(prog)s --interactive  # Enter interactive mode
        """
    )
    
    parser.add_argument('--query', '-q', type=str, help='Search query')
    parser.add_argument('--limit', '-l', type=int, default=5, help='Number of results (default: 5)')
    parser.add_argument('--threshold', '-t', type=float, help='Similarity threshold (0.0-1.0)')
    parser.add_argument('--subject', '-s', type=str, help='Filter by subject')
    parser.add_argument('--metric', '-m', type=str, default='cosine', 
                       choices=['cosine', 'euclidean', 'inner_product'],
                       help='Distance metric (default: cosine)')
    parser.add_argument('--config', '-c', type=str, default='search_config.json',
                       help='Configuration file (default: search_config.json)')
    parser.add_argument('--scenarios', action='store_true', 
                       help='Run all configured search scenarios')
    parser.add_argument('--experiments', action='store_true',
                       help='Run all configured experiments')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Enter interactive mode')
    
    args = parser.parse_args()
    
    # Initialize assistant
    try:
        assistant = VectorSearchAssistant(args.config)
    except Exception as e:
        print(f"❌ Failed to initialize search assistant: {e}")
        sys.exit(1)
    
    # Run based on arguments
    if args.scenarios:
        assistant.run_configured_searches()
    elif args.experiments:
        assistant.run_experiments()
    elif args.interactive:
        assistant.interactive_mode()
    elif args.query:
        results = assistant.search_similar(
            query=args.query,
            limit=args.limit,
            threshold=args.threshold,
            subject_filter=args.subject,
            distance_metric=args.metric
        )
        
        if results:
            print(f"\n📋 Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result}")
        else:
            print("❌ No results found")
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 