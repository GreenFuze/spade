/**
 * HelloWorld Java class - provides a simple hello world method
 * that can be called from C++ via JNI
 */
public class HelloWorld {

	/**
	 * Returns a hello world message
	 * 
	 * @return String containing hello world message
	 */
	public static String hello() {
		return "Hello from Java! JNI integration working perfectly!";
	}

	/**
	 * Returns a greeting with custom message
	 * 
	 * @param name Name to include in greeting
	 * @return String containing personalized greeting
	 */
	public static String greet(String name) {
		return "Hello " + name + " from Java!";
	}

	/**
	 * Returns the current Java version
	 * 
	 * @return String containing Java version information
	 */
	public static String getJavaVersion() {
		return System.getProperty("java.version");
	}
}
