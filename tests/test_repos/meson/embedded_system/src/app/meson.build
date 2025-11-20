# Main firmware application
app_sources = files(
  'main.c'
)

# Build firmware executable
firmware = executable('firmware.elf',
  app_sources,
  dependencies: [core_dep, drivers_dep, protocol_dep, thread_dep],
  install: true
)
