#include "jni_wrapper.h"
#include <iostream>
#include <stdexcept>
#include <cassert>

int main()
{
	std::cout << "Running JNI Wrapper Tests..." << std::endl;

	try
	{
		// Test 1: JNI Wrapper Initialization
		std::cout << "Test 1: JNI Wrapper Initialization..." << std::endl;
		JNIWrapper wrapper;
		std::cout << "✅ JNI Wrapper initialized successfully" << std::endl;

		// Test 2: Java Hello Method Call
		std::cout << "Test 2: Java Hello Method Call..." << std::endl;
		std::string result = wrapper.callJavaHello();
		assert(result.find("Hello from Java") != std::string::npos);
		assert(result.find("JNI integration") != std::string::npos);
		assert(result.length() > 0);
		std::cout << "✅ Java hello() method call successful: " << result << std::endl;

		// Test 3: Java Version Method Call
		std::cout << "Test 3: Java Version Method Call..." << std::endl;
		std::string version = wrapper.callJavaVersion();
		assert(version.find("JNI Hello World") != std::string::npos);
		assert(version.find("v1.0.0") != std::string::npos);
		assert(version.length() > 0);
		std::cout << "✅ Java getVersion() method call successful: " << version << std::endl;

		// Test 4: Multiple Calls
		std::cout << "Test 4: Multiple Calls..." << std::endl;
		for (int i = 0; i < 3; ++i)
		{
			std::string result2 = wrapper.callJavaHello();
			assert(result2.length() > 0);
			std::string version2 = wrapper.callJavaVersion();
			assert(version2.length() > 0);
		}
		std::cout << "✅ Multiple calls successful" << std::endl;

		std::cout << "\n🎉 All JNI Wrapper tests passed!" << std::endl;
		return 0;
	}
	catch (const std::exception &e)
	{
		std::cerr << "❌ Test failed: " << e.what() << std::endl;
		return 1;
	}
}