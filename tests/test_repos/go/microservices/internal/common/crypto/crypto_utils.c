// Simple C utility functions - no external dependencies

// Simple hash function - returns sum of all bytes
int simple_hash(const char* input) {
    if (!input) {
        return 0;
    }
    int sum = 0;
    const char* p = input;
    while (*p) {
        sum += (int)(*p);
        p++;
    }
    return sum;
}

// Simple XOR encryption/decryption with single byte key
void xor_encrypt(const unsigned char* input, unsigned char* output, int length, unsigned char key) {
    if (!input || !output || length <= 0) {
        return;
    }
    for (int i = 0; i < length; i++) {
        output[i] = input[i] ^ key;
    }
}
