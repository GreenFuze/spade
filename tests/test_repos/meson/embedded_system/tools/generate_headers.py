#!/usr/bin/env python3
"""
Header generator - demonstrates Meson generator()

This script would be used with generator() to generate version headers.
(Not actively used in this simple build, but demonstrates the capability)
"""

import sys
from pathlib import Path


def generate_version_header(input_file: Path, output_file: Path):
    """Generate a version header from a template"""

    # Simple stub implementation
    header = f"""/* GENERATED VERSION HEADER */
#ifndef VERSION_HEADER_H
#define VERSION_HEADER_H

#define MODULE_VERSION "1.0.0"
#define MODULE_NAME "{input_file.stem}"

#endif // VERSION_HEADER_H
"""

    output_file.write_text(header)
    print(f"Generated version header: {output_file}")


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input> <output>")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])

    generate_version_header(input_file, output_file)


if __name__ == "__main__":
    main()
