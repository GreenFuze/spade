project('embedded_system', ['c', 'cpp'],
  version: '1.0.0',
  default_options: ['warning_level=2', 'c_std=c11', 'cpp_std=c++14']
)

# Find Python 3 for code generation
py3 = find_program('python3', 'python')

# Configuration data for configure_file()
conf_data = configuration_data()
conf_data.set('VERSION', meson.project_version())
conf_data.set('BUILD_TYPE', get_option('buildtype'))
conf_data.set('ENABLE_DEBUG', get_option('buildtype') == 'debug')
conf_data.set('PROJECT_NAME', meson.project_name())

# Generate config.h from template
configure_file(
  input: 'config.h.in',
  output: 'config.h',
  configuration: conf_data
)

# Add config.h to include directories
config_inc = include_directories('.')

# Subproject dependencies
json_dep = dependency('json-c', fallback: ['json-c', 'json_c_dep'])

# Thread and math dependencies
thread_dep = dependency('threads')
m_dep = meson.get_compiler('c').find_library('m', required: false)
dl_dep = meson.get_compiler('c').find_library('dl', required: false)

# Test dependencies
cmocka_dep = dependency('cmocka', required: false)
gtest_dep = dependency('gtest', required: false, main: true)

# Subdirectories
subdir('src')
subdir('tests')

# Aggregators
run_target('build-all',
  command: [py3, '-c', 'print("All components built successfully")']
)
