#ifndef HANDLER_H
#define HANDLER_H

#include "core/system.h"
#include <stdint.h>

// Protocol message types (will be extended by generated code)
typedef enum {
    MSG_TYPE_UNKNOWN = 0,
    MSG_TYPE_REQUEST = 1,
    MSG_TYPE_RESPONSE = 2,
    MSG_TYPE_EVENT = 3
} message_type_t;

// Protocol message structure
typedef struct {
    message_type_t type;
    uint32_t id;
    uint8_t* payload;
    size_t payload_size;
} protocol_message_t;

// Initialize protocol handler
int protocol_init(void);

// Handle incoming message
int protocol_handle_message(const protocol_message_t* msg);

// Send message
int protocol_send_message(const protocol_message_t* msg);

// Cleanup
void protocol_cleanup(void);

#endif // HANDLER_H
