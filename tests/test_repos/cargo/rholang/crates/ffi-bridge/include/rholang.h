/*
 * RhoLang FFI Bridge - C Header
 * Public API for integrating RhoLang with C programs
 */

#ifndef RHOLANG_H
#define RHOLANG_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Platform initialization and cleanup */
int rholang_native_init(void);
void rholang_native_cleanup(void);

/* Memory management */
void* rholang_native_alloc(size_t size);
void rholang_native_free(void* ptr);

/* System utilities */
const char* rholang_native_getenv(const char* name);
int rholang_native_file_exists(const char* path);

/* Callback support for Rust -> C -> Rust */
typedef void (*rholang_callback_t)(int value);
void rholang_native_set_callback(rholang_callback_t callback);
void rholang_native_trigger_callback(int value);

/* String utilities */
char* rholang_native_string_copy(const char* str);

/* Error handling */
const char* rholang_native_error_string(int error_code);

/*
 * Functions exported from Rust (callable from C)
 * These are defined in the Rust side of the FFI bridge
 */

/* Initialize RhoLang runtime from C */
int rholang_runtime_init(void);

/* Execute RhoLang code from C */
int rholang_execute_code(const char* source_code, size_t len);

/* Shutdown RhoLang runtime from C */
void rholang_runtime_shutdown(void);

/* Get version information */
const char* rholang_get_version(void);

#ifdef __cplusplus
}
#endif

#endif /* RHOLANG_H */
