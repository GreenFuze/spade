#ifndef SPI_HPP
#define SPI_HPP

#include <cstdint>
#include <vector>

extern "C" {
    #include "core/system.h"
}

namespace drivers {

enum class SPIMode {
    MODE_0 = 0,
    MODE_1 = 1,
    MODE_2 = 2,
    MODE_3 = 3
};

class SPI {
public:
    SPI(uint32_t clock_speed, SPIMode mode);
    ~SPI();

    // Initialize SPI
    bool init();

    // Transfer data (full duplex)
    std::vector<uint8_t> transfer(const std::vector<uint8_t>& tx_data);

    // Set chip select
    void set_cs(bool active);

private:
    uint32_t clock_speed_;
    SPIMode mode_;
    bool initialized_;
    bool cs_active_;
};

} // namespace drivers

#endif // SPI_HPP
