#include "core/system.h"
#include "core/memory.h"
#include "protocol/handler.h"
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>

// Forward declarations for C++ drivers (using extern "C" on their side)
// We'll call them through a C wrapper in a real implementation
// For this stub, we'll just reference the system

static void* worker_thread(void* arg) {
    (void)arg;

    printf("Worker thread started\n");

    // Allocate some memory
    void* buffer = memory_alloc(256);
    if (buffer == NULL) {
        printf("Failed to allocate memory\n");
        return NULL;
    }

    // Send a test protocol message
    protocol_message_t msg = {
        .type = MSG_TYPE_REQUEST,
        .id = 1,
        .payload = (uint8_t*)buffer,
        .payload_size = 256
    };

    protocol_send_message(&msg);

    printf("Worker thread finished\n");
    return NULL;
}

int main(int argc, char** argv) {
    (void)argc;
    (void)argv;

    printf("=== Embedded System Firmware ===\n");
    printf("Version: %s\n", VERSION);
    printf("Build type: %s\n", BUILD_TYPE);

    // Initialize system
    if (system_init() != 0) {
        fprintf(stderr, "System initialization failed\n");
        return 1;
    }

    // Initialize protocol handler
    if (protocol_init() != 0) {
        fprintf(stderr, "Protocol initialization failed\n");
        system_shutdown();
        return 1;
    }

    // Create worker thread
    pthread_t thread;
    if (pthread_create(&thread, NULL, worker_thread, NULL) != 0) {
        fprintf(stderr, "Failed to create worker thread\n");
        protocol_cleanup();
        system_shutdown();
        return 1;
    }

    // Wait for worker thread
    pthread_join(thread, NULL);

    // Cleanup
    protocol_cleanup();
    system_shutdown();

    printf("Firmware exited successfully\n");
    return 0;
}
