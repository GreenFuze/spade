/*
 * Native C implementation for RhoLang FFI bridge
 * Demonstrates Rust -> C and C -> Rust interoperability
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../include/rholang.h"

/* Platform-specific initialization */
int rholang_native_init(void) {
    printf("RhoLang native platform initialized\n");
    return 0;
}

/* Platform-specific cleanup */
void rholang_native_cleanup(void) {
    printf("RhoLang native platform cleaned up\n");
}

/* Memory allocation wrapper */
void* rholang_native_alloc(size_t size) {
    void* ptr = malloc(size);
    if (!ptr) {
        fprintf(stderr, "Native allocation failed for size %zu\n", size);
        return NULL;
    }
    memset(ptr, 0, size);
    return ptr;
}

/* Memory deallocation wrapper */
void rholang_native_free(void* ptr) {
    if (ptr) {
        free(ptr);
    }
}

/* System call wrapper for getting environment variables */
const char* rholang_native_getenv(const char* name) {
    return getenv(name);
}

/* Platform-specific file operations */
int rholang_native_file_exists(const char* path) {
    FILE* f = fopen(path, "r");
    if (f) {
        fclose(f);
        return 1;
    }
    return 0;
}

/* Callback function that Rust can provide */
static rholang_callback_t user_callback = NULL;

void rholang_native_set_callback(rholang_callback_t callback) {
    user_callback = callback;
}

void rholang_native_trigger_callback(int value) {
    if (user_callback) {
        user_callback(value);
    } else {
        printf("No callback set\n");
    }
}

/* String manipulation helper */
char* rholang_native_string_copy(const char* str) {
    if (!str) return NULL;
    size_t len = strlen(str);
    char* copy = (char*)malloc(len + 1);
    if (copy) {
        strcpy(copy, str);
    }
    return copy;
}

/* Error code utilities */
const char* rholang_native_error_string(int error_code) {
    switch (error_code) {
        case 0: return "Success";
        case -1: return "Generic error";
        case -2: return "Memory allocation error";
        case -3: return "File not found";
        case -4: return "Permission denied";
        default: return "Unknown error";
    }
}
