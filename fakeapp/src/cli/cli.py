#!/usr/bin/env python3
"""
FakeApp CLI - Sample command line interface
"""

import argparse
import sys

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='FakeApp CLI')
    parser.add_argument('--version', action='store_true', help='Show version')
    parser.add_argument('--config', help='Configuration file path')
    
    args = parser.parse_args()
    
    if args.version:
        print("FakeApp CLI v1.0.0")
        sys.exit(0)
    
    if args.config:
        print(f"Using config: {args.config}")
    
    print("FakeApp CLI - Ready")

if __name__ == '__main__':
    main()
