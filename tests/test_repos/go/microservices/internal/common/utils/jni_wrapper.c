#include <jni.h>
#include <stdlib.h>
#include <string.h>
#include "jni_wrapper.h"

static JavaVM* jvm = NULL;
static JNIEnv* env = NULL;

int init_jvm(const char* classpath) {
    if (jvm != NULL) {
        return 0; // Already initialized
    }

    JavaVMOption options[1];
    char classpath_option[512];
    snprintf(classpath_option, sizeof(classpath_option), "-Djava.class.path=%s", classpath);
    options[0].optionString = classpath_option;

    JavaVMInitArgs vm_args;
    vm_args.version = JNI_VERSION_1_8;
    vm_args.options = options;
    vm_args.nOptions = 1;
    vm_args.ignoreUnrecognized = JNI_TRUE;

    jint result = JNI_CreateJavaVM(&jvm, (void**)&env, &vm_args);
    if (result != JNI_OK) {
        return -1;
    }

    return 0;
}

void cleanup_jvm(void) {
    if (jvm != NULL) {
        (*jvm)->DestroyJavaVM(jvm);
        jvm = NULL;
        env = NULL;
    }
}

char* format_text_jni(const char* input) {
    if (jvm == NULL || env == NULL) {
        return NULL;
    }

    // Find the TextUtils class
    jclass textUtilsClass = (*env)->FindClass(env, "com/greenfuze/microservices/utils/TextUtils");
    if (textUtilsClass == NULL) {
        return NULL;
    }

    // Find the formatText static method
    jmethodID formatMethod = (*env)->GetStaticMethodID(
        env,
        textUtilsClass,
        "formatText",
        "(Ljava/lang/String;)Ljava/lang/String;"
    );
    if (formatMethod == NULL) {
        (*env)->DeleteLocalRef(env, textUtilsClass);
        return NULL;
    }

    // Convert C string to Java String
    jstring jInput = (*env)->NewStringUTF(env, input);
    if (jInput == NULL) {
        (*env)->DeleteLocalRef(env, textUtilsClass);
        return NULL;
    }

    // Call the Java method
    jstring jResult = (jstring)(*env)->CallStaticObjectMethod(
        env,
        textUtilsClass,
        formatMethod,
        jInput
    );

    // Convert Java String back to C string
    char* result = NULL;
    if (jResult != NULL) {
        const char* utfResult = (*env)->GetStringUTFChars(env, jResult, NULL);
        if (utfResult != NULL) {
            result = strdup(utfResult);
            (*env)->ReleaseStringUTFChars(env, jResult, utfResult);
        }
        (*env)->DeleteLocalRef(env, jResult);
    }

    // Cleanup
    (*env)->DeleteLocalRef(env, jInput);
    (*env)->DeleteLocalRef(env, textUtilsClass);

    return result;
}
