#include "handler.h"
#include "protocol_generated.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static bool protocol_initialized = false;

int protocol_init(void) {
    printf("Protocol handler initializing...\n");

    // Initialize generated protocol handlers
    protocol_generated_init();

    protocol_initialized = true;
    return 0;
}

int protocol_handle_message(const protocol_message_t* msg) {
    if (!protocol_initialized || msg == NULL) {
        return -1;
    }

    printf("Handling message: type=%d, id=%u, size=%zu\n",
           msg->type, msg->id, msg->payload_size);

    // Dispatch to generated handlers based on message type
    switch (msg->type) {
        case MSG_TYPE_REQUEST:
            return protocol_generated_handle_request(msg->id, msg->payload, msg->payload_size);

        case MSG_TYPE_RESPONSE:
            return protocol_generated_handle_response(msg->id, msg->payload, msg->payload_size);

        case MSG_TYPE_EVENT:
            return protocol_generated_handle_event(msg->id, msg->payload, msg->payload_size);

        default:
            printf("Unknown message type: %d\n", msg->type);
            return -1;
    }
}

int protocol_send_message(const protocol_message_t* msg) {
    if (!protocol_initialized || msg == NULL) {
        return -1;
    }

    printf("Sending message: type=%d, id=%u, size=%zu\n",
           msg->type, msg->id, msg->payload_size);

    // Simulate sending
    return 0;
}

void protocol_cleanup(void) {
    protocol_generated_cleanup();
    protocol_initialized = false;
}
