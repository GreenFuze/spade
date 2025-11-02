#include "jni_wrapper.h"
#include <iostream>
#include <stdexcept>

JNIWrapper::JNIWrapper() : jvm(nullptr), env(nullptr),
						   helloWorldClass(nullptr), helloWorldJNIClass(nullptr),
						   helloMethod(nullptr), versionMethod(nullptr)
{
	initializeJVM();
	loadJavaClasses();
	setupMethodIDs();
}

JNIWrapper::~JNIWrapper()
{
	if (env)
	{
		env->DeleteLocalRef(helloWorldClass);
		env->DeleteLocalRef(helloWorldJNIClass);
	}
	if (jvm)
	{
		jvm->DestroyJavaVM();
	}
}

void JNIWrapper::initializeJVM()
{
	JavaVMOption options[1];
	options[0].optionString = const_cast<char *>("-Djava.class.path=java_hello_lib-1.0.0.jar");

	JavaVMInitArgs vm_args;
	vm_args.version = JNI_VERSION_1_8;
	vm_args.nOptions = 1;
	vm_args.options = options;
	vm_args.ignoreUnrecognized = JNI_FALSE;

	jint result = JNI_CreateJavaVM(&jvm, (void **)&env, &vm_args);
	if (result != JNI_OK)
	{
		throw std::runtime_error("Failed to create Java VM");
	}
}

void JNIWrapper::loadJavaClasses()
{
	helloWorldClass = env->FindClass("HelloWorld");
	if (!helloWorldClass)
	{
		throw std::runtime_error("Failed to find HelloWorld class");
	}

	helloWorldJNIClass = env->FindClass("HelloWorldJNI");
	if (!helloWorldJNIClass)
	{
		throw std::runtime_error("Failed to find HelloWorldJNI class");
	}
}

void JNIWrapper::setupMethodIDs()
{
	helloMethod = env->GetStaticMethodID(helloWorldClass, "hello", "()Ljava/lang/String;");
	if (!helloMethod)
	{
		throw std::runtime_error("Failed to find HelloWorld.hello() method");
	}

	versionMethod = env->GetStaticMethodID(helloWorldJNIClass, "getVersion", "()Ljava/lang/String;");
	if (!versionMethod)
	{
		throw std::runtime_error("Failed to find HelloWorldJNI.getVersion() method");
	}
}

std::string JNIWrapper::callJavaHello()
{
	jstring jresult = (jstring)env->CallStaticObjectMethod(helloWorldClass, helloMethod);
	if (env->ExceptionCheck())
	{
		env->ExceptionDescribe();
		env->ExceptionClear();
		throw std::runtime_error("Exception occurred calling Java hello() method");
	}

	return jstringToString(jresult);
}

std::string JNIWrapper::callJavaVersion()
{
	jstring jresult = (jstring)env->CallStaticObjectMethod(helloWorldJNIClass, versionMethod);
	if (env->ExceptionCheck())
	{
		env->ExceptionDescribe();
		env->ExceptionClear();
		throw std::runtime_error("Exception occurred calling Java getVersion() method");
	}

	return jstringToString(jresult);
}

std::string JNIWrapper::jstringToString(jstring jstr)
{
	if (!jstr)
	{
		return "";
	}

	const char *cstr = env->GetStringUTFChars(jstr, nullptr);
	std::string result(cstr);
	env->ReleaseStringUTFChars(jstr, cstr);
	env->DeleteLocalRef(jstr);

	return result;
}
