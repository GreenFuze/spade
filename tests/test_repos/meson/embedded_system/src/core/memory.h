#ifndef MEMORY_H
#define MEMORY_H

#include <stddef.h>
#include <stdint.h>
#include <math.h>

// Memory pool management
int memory_init(void);
void memory_cleanup(void);

// Memory allocation
void* memory_alloc(size_t size);
void memory_free(void* ptr);

// Memory statistics
size_t memory_get_used(void);
size_t memory_get_available(void);

#endif // MEMORY_H
