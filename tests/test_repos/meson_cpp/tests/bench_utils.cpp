#include "utils.h"
#include <chrono>
#include <iostream>

int main()
{
	auto start = std::chrono::high_resolution_clock::now();

	for (int i = 0; i < 1000; ++i)
	{
		print_utils();
	}

	auto end = std::chrono::high_resolution_clock::now();
	auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

	std::cout << "Benchmark completed in " << duration.count() << " microseconds" << std::endl;
	return 0;
}
