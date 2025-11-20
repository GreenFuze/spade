# Core system library - static library
core_sources = files(
  'system.c',
  'memory.c'
)

core_inc = include_directories('.')

# Build static library
libcore = static_library('core',
  core_sources,
  include_directories: [core_inc, config_inc],
  dependencies: [json_dep, m_dep],
  install: true
)

# Declare dependency for other targets
core_dep = declare_dependency(
  link_with: libcore,
  include_directories: [core_inc, config_inc],
  dependencies: [json_dep]
)
