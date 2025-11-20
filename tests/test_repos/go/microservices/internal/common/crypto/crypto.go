package crypto

/*
#include "crypto_utils.c"
#include <stdlib.h>
*/
import "C"
import (
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"errors"
	"golang.org/x/crypto/bcrypt"
	"unsafe"
)

// HashPassword hashes a password using bcrypt
func HashPassword(password string) (string, error) {
	bytes, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	return string(bytes), err
}

// CheckPasswordHash verifies a password against a hash
func CheckPasswordHash(password, hash string) bool {
	err := bcrypt.CompareHashAndPassword([]byte(hash), []byte(password))
	return err == nil
}

// GenerateRandomToken generates a random token
func GenerateRandomToken(length int) (string, error) {
	bytes := make([]byte, length)
	if _, err := rand.Read(bytes); err != nil {
		return "", err
	}
	return hex.EncodeToString(bytes), nil
}

// SHA256Hash computes SHA256 hash of input
func SHA256Hash(input string) string {
	hash := sha256.Sum256([]byte(input))
	return hex.EncodeToString(hash[:])
}

// SimpleHash computes a simple hash using C implementation (for demonstration)
// This uses CGo to call C code, demonstrating cross-language integration
func SimpleHash(input string) int {
	cInput := C.CString(input)
	defer C.free(unsafe.Pointer(cInput))
	return int(C.simple_hash(cInput))
}

// XOREncrypt performs XOR encryption using C implementation
func XOREncrypt(input []byte, key byte) []byte {
	if len(input) == 0 {
		return nil
	}
	output := make([]byte, len(input))
	C.xor_encrypt(
		(*C.uchar)(&input[0]),
		(*C.uchar)(&output[0]),
		C.int(len(input)),
		C.uchar(key),
	)
	return output
}

