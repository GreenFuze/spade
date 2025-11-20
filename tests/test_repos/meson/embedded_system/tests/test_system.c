#include <stdarg.h>
#include <stddef.h>
#include <setjmp.h>
#include <cmocka.h>
#include "core/system.h"
#include "core/memory.h"

// Test system initialization
static void test_system_init(void **state) {
    (void) state; // unused

    int result = system_init();
    assert_int_equal(result, 0);
    assert_int_equal(system_get_status(), SYSTEM_STATUS_OK);

    system_shutdown();
}

// Test memory allocation
static void test_memory_alloc(void **state) {
    (void) state; // unused

    memory_init();

    void* ptr = memory_alloc(128);
    assert_non_null(ptr);
    assert_int_equal(memory_get_used(), 128);

    memory_cleanup();
}

// Test memory bounds
static void test_memory_bounds(void **state) {
    (void) state; // unused

    memory_init();

    // Get available memory
    size_t available = memory_get_available();
    assert_true(available > 0);

    memory_cleanup();
}

int main(void) {
    const struct CMUnitTest tests[] = {
        cmocka_unit_test(test_system_init),
        cmocka_unit_test(test_memory_alloc),
        cmocka_unit_test(test_memory_bounds),
    };

    return cmocka_run_group_tests(tests, NULL, NULL);
}
