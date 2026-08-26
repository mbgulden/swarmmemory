import argparse
import sys
from pathlib import Path
from .episodic import EpisodicStore
from .semantic import SemanticDistiller
from .types import MemoryQuery

def main():
    parser = argparse.ArgumentParser(description="SwarmMemory CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    query_parser = subparsers.add_parser("query", help="Query episodic memory")
    query_parser.add_argument("text", type=str)
    query_parser.add_argument("--db", type=str, default="memory.db")

    stats_parser = subparsers.add_parser("stats", help="Show memory stats")
    stats_parser.add_argument("--db", type=str, default="memory.db")

    gc_parser = subparsers.add_parser("gc", help="Garbage collect old episodes")
    gc_parser.add_argument("--days", type=int, default=30)
    gc_parser.add_argument("--db", type=str, default="memory.db")

    distill_parser = subparsers.add_parser("distill", help="Distill semantic context")
    distill_parser.add_argument("path", type=str)

    args = parser.parse_args()

    if args.command == "query":
        store = EpisodicStore(args.db)
        results = store.recall(MemoryQuery(text=args.text))
        for r in results:
            print(f"[{r.episode_id}] {r.content}")
            
    elif args.command == "stats":
        store = EpisodicStore(args.db)
        # simplified stats
        print("Stats logic here")
        
    elif args.command == "gc":
        store = EpisodicStore(args.db)
        count = store.gc(args.days)
        print(f"Garbage collected {count} episodes")
        
    elif args.command == "distill":
        distiller = SemanticDistiller()
        p = Path(args.path)
        if p.is_file():
            nodes = distiller.distill_file(p)
        else:
            nodes = distiller.distill_directory(p)
        
        for n in nodes:
            print(f"{n.symbol_type} {n.symbol_name} ({n.file_path})")

if __name__ == "__main__":
    main()
