# Unit tests

if get_option('enable_tests')
  # Test for core library (C test with cmocka)
  if cmocka_dep.found()
    test_system = executable('test_system',
      'test_system.c',
      dependencies: [core_dep, cmocka_dep],
      install: false
    )
    test('Core System Tests', test_system)
  endif

  # Test for drivers library (C++ test with gtest)
  if gtest_dep.found()
    test_drivers = executable('test_drivers',
      'test_drivers.cpp',
      dependencies: [drivers_dep, gtest_dep],
      install: false
    )
    test('Driver Tests', test_drivers)
  endif
endif
