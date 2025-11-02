import org.junit.Test;
import org.junit.Before;
import static org.junit.Assert.*;

/**
 * JUnit tests for HelloWorld Java classes
 */
public class HelloWorldTest {

	@Before
	public void setUp() {
		// Setup code if needed
	}

	@Test
	public void testHelloWorldHello() {
		// Test HelloWorld.hello() method
		String result = HelloWorld.hello();

		assertNotNull("Hello method should not return null", result);
		assertTrue("Result should contain 'Hello from Java'",
				result.contains("Hello from Java"));
		assertTrue("Result should contain 'JNI integration'",
				result.contains("JNI integration"));
		assertTrue("Result should not be empty", result.length() > 0);
	}

	@Test
	public void testHelloWorldGreet() {
		// Test HelloWorld.greet() method
		String result = HelloWorld.greet("TestUser");

		assertNotNull("Greet method should not return null", result);
		assertTrue("Result should contain 'Hello TestUser'",
				result.contains("Hello TestUser"));
		assertTrue("Result should contain 'from Java'",
				result.contains("from Java"));
	}

	@Test
	public void testHelloWorldGetJavaVersion() {
		// Test HelloWorld.getJavaVersion() method
		String version = HelloWorld.getJavaVersion();

		assertNotNull("Java version should not be null", version);
		assertTrue("Version should not be empty", version.length() > 0);
		// Version should contain at least one dot (e.g., "1.8.0" or "11.0.1")
		assertTrue("Version should contain version numbers", version.contains("."));
	}

	@Test
	public void testHelloWorldJNIGetVersion() {
		// Test HelloWorldJNI.getVersion() method
		String version = HelloWorldJNI.getVersion();

		assertNotNull("JNI version should not be null", version);
		assertTrue("Version should contain 'JNI Hello World'",
				version.contains("JNI Hello World"));
		assertTrue("Version should contain 'v1.0.0'",
				version.contains("v1.0.0"));
	}

	@Test
	public void testHelloWorldJNIGetJNIInfo() {
		// Test HelloWorldJNI.getJNIInfo() method
		String info = HelloWorldJNI.getJNIInfo();

		assertNotNull("JNI info should not be null", info);
		assertTrue("Info should contain 'JNI Version'",
				info.contains("JNI Version"));
		assertTrue("Info should contain 'Platform'",
				info.contains("Platform"));
		assertTrue("Info should not be empty", info.length() > 0);
	}

	@Test
	public void testHelloWorldJNIGetStatus() {
		// Test HelloWorldJNI.getStatus() method
		String status = HelloWorldJNI.getStatus();

		assertNotNull("Status should not be null", status);
		assertTrue("Status should contain 'JNI Hello World'",
				status.contains("JNI Hello World"));
		assertTrue("Status should contain 'ready'",
				status.contains("ready"));
		assertTrue("Status should not be empty", status.length() > 0);
	}

	@Test
	public void testMultipleCalls() {
		// Test multiple calls to ensure consistency
		for (int i = 0; i < 3; i++) {
			String hello = HelloWorld.hello();
			String version = HelloWorldJNI.getVersion();

			assertNotNull("Hello result should not be null", hello);
			assertNotNull("Version result should not be null", version);
			assertTrue("Hello result should not be empty", hello.length() > 0);
			assertTrue("Version result should not be empty", version.length() > 0);
		}
	}
}
