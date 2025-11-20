package utils

/*
#cgo CFLAGS: -I${SRCDIR}
#cgo LDFLAGS: -ljvm
#cgo linux LDFLAGS: -L/usr/lib/jvm/default-java/lib/server
#cgo darwin LDFLAGS: -L/System/Library/Frameworks/JavaVM.framework/Libraries
#cgo windows LDFLAGS: -L"C:/Program Files/Java/jdk*/lib/server"

#include "jni_wrapper.h"
#include <stdlib.h>
*/
import "C"
import (
	"unsafe"
)

var jvmInitialized bool

// InitJava initializes the JVM with the given classpath
func InitJava(classpath string) error {
	if jvmInitialized {
		return nil
	}

	cClasspath := C.CString(classpath)
	defer C.free(unsafe.Pointer(cClasspath))

	result := C.init_jvm(cClasspath)
	if result != 0 {
		return &JavaError{Message: "Failed to initialize JVM"}
	}

	jvmInitialized = true
	return nil
}

// CleanupJava cleans up the JVM
func CleanupJava() {
	if jvmInitialized {
		C.cleanup_jvm()
		jvmInitialized = false
	}
}

// FormatText formats text using Java TextUtils.formatText()
func FormatText(input string) (string, error) {
	if !jvmInitialized {
		return "", &JavaError{Message: "JVM not initialized. Call InitJava first"}
	}

	cInput := C.CString(input)
	defer C.free(unsafe.Pointer(cInput))

	cResult := C.format_text_jni(cInput)
	if cResult == nil {
		return "", &JavaError{Message: "Failed to format text"}
	}
	defer C.free(unsafe.Pointer(cResult))

	return C.GoString(cResult), nil
}

// JavaError represents an error from Java operations
type JavaError struct {
	Message string
}

func (e *JavaError) Error() string {
	return "Java error: " + e.Message
}
