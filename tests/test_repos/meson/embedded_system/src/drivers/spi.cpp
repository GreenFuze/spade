#include "spi.hpp"
#include <iostream>

namespace drivers {

SPI::SPI(uint32_t clock_speed, SPIMode mode)
    : clock_speed_(clock_speed), mode_(mode), initialized_(false), cs_active_(false) {
}

SPI::~SPI() {
    if (initialized_) {
        std::cout << "SPI closed" << std::endl;
    }
}

bool SPI::init() {
    // Check system status before initializing
    if (system_get_status() != SYSTEM_STATUS_OK) {
        return false;
    }

    std::cout << "SPI initialized at " << clock_speed_ << " Hz, mode "
              << static_cast<int>(mode_) << std::endl;
    initialized_ = true;
    return true;
}

std::vector<uint8_t> SPI::transfer(const std::vector<uint8_t>& tx_data) {
    if (!initialized_) {
        return std::vector<uint8_t>();
    }

    // Simulate full-duplex transfer
    std::vector<uint8_t> rx_data(tx_data.size(), 0xFF);

    std::cout << "SPI transfer: " << tx_data.size() << " bytes" << std::endl;

    return rx_data;
}

void SPI::set_cs(bool active) {
    cs_active_ = active;
    std::cout << "SPI CS: " << (active ? "active" : "inactive") << std::endl;
}

} // namespace drivers
