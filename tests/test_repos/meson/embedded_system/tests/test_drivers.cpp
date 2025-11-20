#include <gtest/gtest.h>
#include "drivers/uart.hpp"
#include "drivers/spi.hpp"

extern "C" {
    #include "core/system.h"
}

class DriverTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Initialize system before each test
        system_init();
    }

    void TearDown() override {
        // Clean up after each test
        system_shutdown();
    }
};

// Test UART initialization
TEST_F(DriverTest, UARTInit) {
    drivers::UART uart(115200);
    EXPECT_TRUE(uart.init());
}

// Test UART send
TEST_F(DriverTest, UARTSend) {
    drivers::UART uart(115200);
    uart.init();

    const uint8_t data[] = {0x01, 0x02, 0x03};
    int sent = uart.send(data, sizeof(data));
    EXPECT_EQ(sent, sizeof(data));
}

// Test UART send string
TEST_F(DriverTest, UARTSendString) {
    drivers::UART uart(115200);
    uart.init();

    std::string msg = "Hello, UART!";
    int sent = uart.send_string(msg);
    EXPECT_EQ(sent, msg.length());
}

// Test SPI initialization
TEST_F(DriverTest, SPIInit) {
    drivers::SPI spi(1000000, drivers::SPIMode::MODE_0);
    EXPECT_TRUE(spi.init());
}

// Test SPI transfer
TEST_F(DriverTest, SPITransfer) {
    drivers::SPI spi(1000000, drivers::SPIMode::MODE_0);
    spi.init();

    std::vector<uint8_t> tx_data = {0xAA, 0xBB, 0xCC};
    std::vector<uint8_t> rx_data = spi.transfer(tx_data);

    EXPECT_EQ(rx_data.size(), tx_data.size());
}

// Test SPI chip select
TEST_F(DriverTest, SPIChipSelect) {
    drivers::SPI spi(1000000, drivers::SPIMode::MODE_0);
    spi.init();

    // Should not throw
    spi.set_cs(true);
    spi.set_cs(false);
}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
