#include <iostream>
#include <jni.h>
#include "jni_wrapper.h"

int main()
{
	std::cout << "C++ JNI Hello World Application" << std::endl;

	try
	{
		// Initialize JNI wrapper
		JNIWrapper jni_wrapper;

		// Call Java HelloWorld.hello() method
		std::string result = jni_wrapper.callJavaHello();
		std::cout << "Java says: " << result << std::endl;

		// Call Java HelloWorldJNI.getVersion() method
		std::string version = jni_wrapper.callJavaVersion();
		std::cout << "Java version: " << version << std::endl;
	}
	catch (const std::exception &e)
	{
		std::cerr << "Error: " << e.what() << std::endl;
		return 1;
	}

	std::cout << "Application completed successfully!" << std::endl;
	return 0;
}
