# Converter Plugin Standard

## Converter Plugin Standard

This document defines the universal plugin specification for every future converter in Converigo. The standard is designed to be simple enough for rapid development, strict enough for long-term compatibility, and compatible with the current plugin architecture.

## Directory Structure

app/plugins/
  base/
    __init__.py
    base_plugin.py
  audio/
    __init__.py
    <plugin_name>.py
  video/
    __init__.py
    <plugin_name>.py
  image/
    __init__.py
    <plugin_name>.py
  document/
    __init__.py
    <plugin_name>.py
  registry.py

Each plugin must live in a category directory and expose one converter implementation class.

## Lifecycle Diagram

Register
  -> Validate
  -> Convert
  -> Optimize
  -> Output
  -> Cleanup

Each lifecycle stage must be explicit and deterministic.

## Lifecycle Requirements

1. Register
   - The plugin is discovered and registered with the plugin registry.
   - The plugin must expose stable metadata and declare supported formats.

2. Validate
   - The system must verify that the input file exists, has a supported extension, and matches the declared source format.
   - The plugin must reject unsupported combinations before execution.

3. Convert
   - The plugin executes the conversion pipeline using its declared engine or runtime.
   - The plugin must produce a deterministic output path and preserve the expected output type.

4. Optimize
   - The plugin may apply optional tuning such as codec selection, bitrate adjustments, or quality presets.
   - Optimization must not change the declared contract or silently alter the output type.

5. Output
   - The plugin must return a concrete output file path.
   - The output must be inspectable, relocatable, and compatible with downstream serving or download logic.

6. Cleanup
   - Temporary files, cache artifacts, and intermediate outputs must be removed.
   - Cleanup must happen even when conversion fails.

## Required Metadata

Every plugin must define:

- id: Stable unique identifier.
- name: Human-readable plugin name.
- category: One of audio, video, image, document, or other supported categories.
- source formats: Supported input extensions.
- target formats: Supported output extensions.
- version: Semantic version string.
- author: Maintainer or owner.
- description: Short explanation of purpose and behavior.
- supported platforms: Runtime environments supported by the plugin.
- ffmpeg required: Yes or no.
- dependencies: Any required runtime packages, binaries, or services.

## Required Methods

Every plugin must provide:

- register(): Register the plugin with the runtime.
- validate(source_path, target_format): Validate the input and the requested conversion.
- convert(source_path, target_format): Perform the conversion and return the output path.
- optimize(output_path): Apply optional optimization if supported.
- cleanup(temp_paths): Remove temporary files and intermediate artifacts.

Optional methods may include:

- supports(source_format, target_format)
- get_metadata()
- get_supported_targets()

## Error Handling Standard

All plugins must follow a consistent error model.

- Fail fast on unsupported input or target combinations.
- Raise or return explicit, user-readable errors.
- Preserve the original cause when wrapping exceptions.
- Never emit partial success states without a completed artifact.
- On failure, remove temporary files and leave no inconsistent output behind.

Recommended error categories:

- UnsupportedFormatError
- ValidationError
- ConversionError
- DependencyError
- OutputError

## Logging Standard

Plugins must log at a consistent level and with a consistent structure.

- Log plugin id, source format, target format, input path, and output path.
- Log start, success, and failure events.
- Log external tool invocations and their exit codes.
- Avoid logging secrets or raw binary content.

Recommended event names:

- plugin.registered
- plugin.validation.started
- plugin.validation.failed
- plugin.convert.started
- plugin.convert.completed
- plugin.convert.failed
- plugin.cleanup.completed

## Testing Standard

Every plugin must be tested for:

- successful conversion for a valid sample
- rejection for unsupported formats
- rejection for missing dependencies
- behavior with malformed or damaged inputs
- output file existence and expected extension
- deterministic output naming and cleanup behavior

Each plugin should include:

- one happy-path test
- one invalid-input test
- one dependency-failure test
- one regression case for any historical bug

## Performance Requirements

- Plugins must complete within reasonable operational limits for their category.
- Large files should stream where possible instead of loading the entire file into memory.
- Plugins should avoid unnecessary re-encoding when the format is already compatible.
- Each plugin should expose a timeout policy and fail predictably when an operation exceeds it.

Suggested baseline targets:

- Small image conversion: under 10 seconds
- Audio conversion: under 20 seconds
- Video conversion: under 60 seconds for typical files

## Security Requirements

Plugins must not:

- execute arbitrary user-supplied commands
- write outside the approved output directories
- accept path traversal or unsafe file names
- expose secrets in logs or error messages
- leave temporary files behind after execution

Plugins must validate input file paths, enforce allowed extensions, and use safe subprocess invocation patterns.

## File Naming Convention

Generated files must follow a deterministic pattern:

<uuid>.<target_extension>

Temporary files may use:

<uuid>.<source_extension>.tmp

Examples:

- 3f9e2a1c.mp3
- 3f9e2a1c.mp4.tmp

## Future Compatibility Notes

This standard is intentionally generic so that future converters can be added without redesign. The main compatibility principles are:

- Metadata must remain explicit and stable.
- Lifecycle stages must always be present.
- Error handling and logging must be consistent across all plugins.
- New plugins should not depend on hidden behavior or undocumented side effects.
- The registry should be able to discover and execute plugins without special-case code.
