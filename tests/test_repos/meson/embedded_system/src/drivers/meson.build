# Drivers library - shared library
drivers_sources = files(
  'uart.cpp',
  'spi.cpp'
)

drivers_inc = include_directories('.')

# Build shared library
libdrivers = shared_library('drivers',
  drivers_sources,
  include_directories: drivers_inc,
  dependencies: [core_dep, dl_dep],
  install: true
)

# Declare dependency for other targets
drivers_dep = declare_dependency(
  link_with: libdrivers,
  include_directories: drivers_inc,
  dependencies: core_dep
)
