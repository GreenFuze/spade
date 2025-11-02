#include <iostream>
#include <jni.h>
#include <windows.h>
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

	// Load and call Go shared library
	std::cout << "\nLoading Go shared library..." << std::endl;
	HMODULE hGoLib = LoadLibrary(TEXT("libhello.dll"));
	if (hGoLib == NULL)
	{
		std::cerr << "Failed to load libhello.dll" << std::endl;
		return 1;
	}

	// Get function pointer to HelloGo
	typedef void (*HelloGoFunc)();
	HelloGoFunc helloGo = (HelloGoFunc)GetProcAddress(hGoLib, "HelloGo");
	if (helloGo == NULL)
	{
		std::cerr << "Failed to find HelloGo function" << std::endl;
		FreeLibrary(hGoLib);
		return 1;
	}

	// Call the Go function
	helloGo();

	// Clean up
	FreeLibrary(hGoLib);

	std::cout << "Application completed successfully!" << std::endl;
	return 0;
}
