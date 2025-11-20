#ifndef JNI_WRAPPER_H
#define JNI_WRAPPER_H

#ifdef __cplusplus
extern "C" {
#endif

// Initialize JVM and load Java class
int init_jvm(const char* classpath);

// Cleanup JVM
void cleanup_jvm(void);

// Format text using Java TextUtils.formatText()
// Returns a newly allocated string that must be freed by caller
char* format_text_jni(const char* input);

#ifdef __cplusplus
}
#endif

#endif // JNI_WRAPPER_H
