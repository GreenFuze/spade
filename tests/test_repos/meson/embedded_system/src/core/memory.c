#include "memory.h"
#include <stdlib.h>
#include <stdio.h>

#define MEMORY_POOL_SIZE (1024 * 1024)  // 1 MB

static uint8_t memory_pool[MEMORY_POOL_SIZE];
static size_t memory_used = 0;

int memory_init(void) {
    memory_used = 0;
    printf("Memory pool initialized (%zu bytes)\n", MEMORY_POOL_SIZE);
    return 0;
}

void memory_cleanup(void) {
    memory_used = 0;
}

void* memory_alloc(size_t size) {
    // Simple bump allocator
    size_t aligned_size = (size + 7) & ~7;  // 8-byte alignment

    if (memory_used + aligned_size > MEMORY_POOL_SIZE) {
        return NULL;
    }

    void* ptr = &memory_pool[memory_used];
    memory_used += aligned_size;

    // Use math library function
    double usage_percent = (double)memory_used / MEMORY_POOL_SIZE * 100.0;
    printf("Memory allocated: %zu bytes (%.2f%% used)\n", size, usage_percent);

    return ptr;
}

void memory_free(void* ptr) {
    // Simplified - does not actually free in this implementation
    (void)ptr;
}

size_t memory_get_used(void) {
    return memory_used;
}

size_t memory_get_available(void) {
    return MEMORY_POOL_SIZE - memory_used;
}
