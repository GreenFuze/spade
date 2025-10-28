project('meson-cpp', 'cpp',
  version : '1.0.0',
  default_options : ['warning_level=3',
                     'cpp_std=c++17'])

# Add executable
executable('hello_world',
           'src/main.cpp',
           'src/utils.cpp',
           install : true)

# Add library
library('utils',
        'src/utils.cpp',
        install : true)

# Add test
test('test_utils',
     executable('test_utils',
                'tests/test_utils.cpp',
                'src/utils.cpp'),
     args : ['--verbose'])

# Add benchmark
benchmark('bench_utils',
          executable('bench_utils',
                     'tests/bench_utils.cpp',
                     'src/utils.cpp'))
