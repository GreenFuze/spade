#include "uart.hpp"
#include <iostream>
#include <cstring>

namespace drivers {

UART::UART(uint32_t baud_rate)
    : baud_rate_(baud_rate), initialized_(false) {
}

UART::~UART() {
    if (initialized_) {
        std::cout << "UART closed" << std::endl;
    }
}

bool UART::init() {
    // Check system status before initializing
    if (system_get_status() != SYSTEM_STATUS_OK) {
        return false;
    }

    std::cout << "UART initialized at " << baud_rate_ << " baud" << std::endl;
    initialized_ = true;
    return true;
}

int UART::send(const uint8_t* data, size_t length) {
    if (!initialized_) {
        return -1;
    }

    // Simulate sending data
    std::cout << "UART sending " << length << " bytes" << std::endl;
    return static_cast<int>(length);
}

int UART::receive(uint8_t* buffer, size_t max_length) {
    if (!initialized_) {
        return -1;
    }

    // Simulate receiving data
    size_t received = max_length > 0 ? 1 : 0;
    if (received > 0) {
        buffer[0] = 0x42;  // Dummy data
    }
    return static_cast<int>(received);
}

int UART::send_string(const std::string& str) {
    return send(reinterpret_cast<const uint8_t*>(str.c_str()), str.length());
}

} // namespace drivers
