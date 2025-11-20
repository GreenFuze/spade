#ifndef SYSTEM_H
#define SYSTEM_H

#include "config.h"
#include <stdint.h>
#include <json-c/json.h>

// System initialization
int system_init(void);

// System status
typedef enum {
    SYSTEM_STATUS_OK = 0,
    SYSTEM_STATUS_ERROR = 1,
    SYSTEM_STATUS_BUSY = 2
} system_status_t;

// Get system status
system_status_t system_get_status(void);

// System configuration from JSON
int system_load_config(struct json_object *config);

// System shutdown
void system_shutdown(void);

#endif // SYSTEM_H
