#!/usr/bin/env python3
"""
Protocol code generator - demonstrates Meson custom_target()

Reads a .proto file and generates C code for protocol handlers.
"""

import sys
from pathlib import Path


def generate_protocol_c(proto_content: str) -> str:
    """Generate protocol_generated.c file"""
    return f"""/* GENERATED FILE - DO NOT EDIT */
/* Generated from protocol.proto */

#include "protocol_generated.h"
#include <stdio.h>
#include <string.h>

void protocol_generated_init(void) {{
    printf("Protocol handlers initialized\\n");
}}

int protocol_generated_handle_request(uint32_t id, const uint8_t* payload, size_t size) {{
    printf("Handling request: id=%u, size=%zu\\n", id, size);
    // Generated handler code would go here
    return 0;
}}

int protocol_generated_handle_response(uint32_t id, const uint8_t* payload, size_t size) {{
    printf("Handling response: id=%u, size=%zu\\n", id, size);
    // Generated handler code would go here
    return 0;
}}

int protocol_generated_handle_event(uint32_t id, const uint8_t* payload, size_t size) {{
    printf("Handling event: id=%u, size=%zu\\n", id, size);
    // Generated handler code would go here
    return 0;
}}

void protocol_generated_cleanup(void) {{
    printf("Protocol handlers cleaned up\\n");
}}
"""


def generate_protocol_h(proto_content: str) -> str:
    """Generate protocol_generated.h file"""
    return f"""/* GENERATED FILE - DO NOT EDIT */
/* Generated from protocol.proto */

#ifndef PROTOCOL_GENERATED_H
#define PROTOCOL_GENERATED_H

#include <stdint.h>
#include <stddef.h>

// Initialize generated protocol handlers
void protocol_generated_init(void);

// Generated message handlers
int protocol_generated_handle_request(uint32_t id, const uint8_t* payload, size_t size);
int protocol_generated_handle_response(uint32_t id, const uint8_t* payload, size_t size);
int protocol_generated_handle_event(uint32_t id, const uint8_t* payload, size_t size);

// Cleanup
void protocol_generated_cleanup(void);

#endif // PROTOCOL_GENERATED_H
"""


def main():
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <input.proto> <output.c> <output.h>")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    output_c = Path(sys.argv[2])
    output_h = Path(sys.argv[3])

    # Read protocol definition
    proto_content = input_file.read_text()

    # Generate C file
    c_code = generate_protocol_c(proto_content)
    output_c.write_text(c_code)
    print(f"Generated: {output_c}")

    # Generate header file
    h_code = generate_protocol_h(proto_content)
    output_h.write_text(h_code)
    print(f"Generated: {output_h}")


if __name__ == "__main__":
    main()
