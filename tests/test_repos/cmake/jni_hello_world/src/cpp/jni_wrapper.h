#pragma once

#include <string>
#include <jni.h>

class JNIWrapper
{
private:
	JavaVM *jvm;
	JNIEnv *env;
	jclass helloWorldClass;
	jclass helloWorldJNIClass;
	jmethodID helloMethod;
	jmethodID versionMethod;

public:
	JNIWrapper();
	~JNIWrapper();

	std::string callJavaHello();
	std::string callJavaVersion();

private:
	void initializeJVM();
	void loadJavaClasses();
	void setupMethodIDs();
	std::string jstringToString(jstring jstr);
};
