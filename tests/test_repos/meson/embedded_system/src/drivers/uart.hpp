#ifndef UART_HPP
#define UART_HPP

#include <cstdint>
#include <string>

extern "C" {
    #include "core/system.h"
}

namespace drivers {

class UART {
public:
    UART(uint32_t baud_rate);
    ~UART();

    // Initialize UART
    bool init();

    // Send data
    int send(const uint8_t* data, size_t length);

    // Receive data
    int receive(uint8_t* buffer, size_t max_length);

    // Send string
    int send_string(const std::string& str);

private:
    uint32_t baud_rate_;
    bool initialized_;
};

} // namespace drivers

#endif // UART_HPP
