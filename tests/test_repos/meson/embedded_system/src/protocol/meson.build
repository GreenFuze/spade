# Protocol library - uses custom_target for code generation
protocol_sources = files(
  'handler.c'
)

protocol_inc = include_directories('.')

# Custom target: Generate protocol code from .proto file
# This demonstrates custom_target() with Python script
protocol_gen = custom_target('protocol_codegen',
  input: 'protocol.proto',
  output: ['protocol_generated.c', 'protocol_generated.h'],
  command: [py3, '@SOURCE_ROOT@/tools/generate_protocol.py', '@INPUT@', '@OUTPUT0@', '@OUTPUT1@'],
  install: false
)

# Build static library with generated code
libprotocol = static_library('protocol',
  [protocol_sources, protocol_gen],
  include_directories: [protocol_inc, config_inc],
  dependencies: core_dep,
  install: true
)

# Declare dependency for other targets
protocol_dep = declare_dependency(
  link_with: libprotocol,
  include_directories: protocol_inc,
  dependencies: core_dep
)
