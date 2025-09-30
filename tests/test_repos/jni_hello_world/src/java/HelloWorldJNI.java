/**
 * HelloWorldJNI class - provides JNI-specific functionality
 * and version information for the JNI Hello World project
 */
public class HelloWorldJNI {

	/**
	 * Returns the version of the JNI Hello World project
	 * 
	 * @return String containing project version
	 */
	public static String getVersion() {
		return "JNI Hello World v1.0.0";
	}

	/**
	 * Returns JNI-specific information
	 * 
	 * @return String containing JNI information
	 */
	public static String getJNIInfo() {
		return "JNI Version: " + System.getProperty("java.version") +
				" | Platform: " + System.getProperty("os.name");
	}

	/**
	 * Returns a status message indicating JNI readiness
	 * 
	 * @return String containing JNI status
	 */
	public static String getStatus() {
		return "JNI Hello World is ready for cross-language communication!";
	}
}
