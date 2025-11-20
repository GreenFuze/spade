#include "system.h"
#include "memory.h"
#include <stdio.h>
#include <stdlib.h>

static system_status_t current_status = SYSTEM_STATUS_OK;

int system_init(void) {
    printf("System initializing (version %s)...\n", VERSION);

    // Initialize memory subsystem
    if (memory_init() != 0) {
        current_status = SYSTEM_STATUS_ERROR;
        return -1;
    }

    current_status = SYSTEM_STATUS_OK;
    return 0;
}

system_status_t system_get_status(void) {
    return current_status;
}

int system_load_config(struct json_object *config) {
    if (config == NULL) {
        return -1;
    }

    // Parse configuration
    struct json_object *obj;
    if (json_object_object_get_ex(config, "debug_mode", &obj)) {
        int debug_mode = json_object_get_boolean(obj);
        printf("Debug mode: %d\n", debug_mode);
    }

    return 0;
}

void system_shutdown(void) {
    printf("System shutting down...\n");
    memory_cleanup();
    current_status = SYSTEM_STATUS_OK;
}
