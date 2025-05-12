# Meet2Obsidian: Project Structure

This file visualizes the current structure of the Meet2Obsidian project. This diagram will be updated as the project evolves.

## ASCII Directory Tree

```
meet2obsidian/
├── CLAUDE.md
├── LICENSE
├── PROJECT_STRUCTURE.md
├── README.md
├── create-docs-dirs.sh
├── docs/
│   ├── README.md
│   ├── api/
│   │   ├── README.md
│   │   ├── claude.md
│   │   └── revai.md
│   ├── assets/
│   │   └── templates/
│   │       ├── api-template.md
│   │       └── component-template.md
│   ├── dev/
│   │   ├── README.md
│   │   └── components/
│   │       ├── API Key Management.md
│   │       ├── API Key Security.md
│   │       └── Logging.md
│   ├── development.md
│   ├── examples/
│   │   ├── config-examples/
│   │   │   └── basic-config.yaml
│   │   └── template-examples/
│   │       └── default.md.j2
│   ├── index.md
│   ├── internal_docs/
│   │   ├── INTRODUCTION.md
│   │   ├── Kanban meet2obsidian dev.md
│   │   ├── Архитектура системы.md
│   │   ├── Дорожная карта.md
│   │   ├── Технический стек.md
│   │   └── Функциональные и нефункциональные требования.md
│   ├── usage.md
│   └── user/
│       ├── README.md
│       ├── getting-started/
│       │   └── installation.md
│       └── usage/
│           ├── api-keys.md
│           ├── cli-commands.md
│           └── logging.md
├── examples/
│   ├── import_test.py
│   ├── logging_example.py
│   ├── security_example.py
│   └── test_logging_compliance.py
├── meet2obsidian/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── claude.py
│   │   └── revai.py
│   ├── audio/
│   │   ├── __init__.py
│   │   └── extractor.py
│   ├── cache.py
│   ├── cli.py
│   ├── cli_commands/
│   │   └── logs_command.py
│   ├── config.py
│   ├── core.py
│   ├── monitor.py
│   ├── note/
│   │   ├── __init__.py
│   │   ├── generator.py
│   │   └── obsidian.py
│   └── utils/
│       ├── __init__.py
│       ├── logging.py
│       ├── security.py
│       └── status.py
├── pyproject.toml
├── requirements.txt
├── scripts/
│   ├── check_videos.py
│   ├── install.sh
│   ├── setup_api_keys.py
│   └── setup_launchagent.sh
├── setup.py
├── tmp/
│   ├── completed_epics_summary.md
│   ├── config_implementation_fixes.md
│   ├── epic7_logging_tests_report.md
│   ├── epic8_implementation_report.md
│   ├── epic9_implementation_report.md
│   └── logging_tests_documentation.md
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── integration/
    │   ├── __init__.py
    │   ├── test_pipeline.py
    │   └── test_security_integration.py
    ├── run_tests.py
    └── unit/
        ├── __init__.py
        ├── test_cli.py
        ├── test_config.py
        ├── test_core.py
        ├── test_logging.py
        └── test_security.py
```

## Mermaid Project Structure Diagram

```mermaid
graph TD
    Root["Meet2Obsidian"] --> Docs["docs/"]
    Root --> Meet2Obsidian["meet2obsidian/"]
    Root --> Scripts["scripts/"]
    Root --> Tests["tests/"]
    Root --> ConfigFiles["Configuration Files"]
    Root --> TmpFiles["tmp/"]

    %% Documentation structure
    Docs --> DocsREADME["README.md"]
    Docs --> DocsAPI["api/"]
    Docs --> DocsAssets["assets/"]
    Docs --> DocsDev["dev/"]
    Docs --> DocsExamples["examples/"]
    Docs --> DocsInternal["internal_docs/"]
    Docs --> DocsUser["user/"]
    Docs --> DocsIndex["index.md"]
    Docs --> DocsUsage["usage.md"]
    Docs --> DocsDevelopment["development.md"]

    %% API docs
    DocsAPI --> DocsAPIReadme["README.md"]
    DocsAPI --> DocsAPIClaude["claude.md"]
    DocsAPI --> DocsAPIRevai["revai.md"]

    %% Assets
    DocsAssets --> DocsAssetsTemplates["templates/"]
    DocsAssetsTemplates --> DocsAssetsTemplatesAPI["api-template.md"]
    DocsAssetsTemplates --> DocsAssetsTemplatesComponent["component-template.md"]

    %% Dev docs
    DocsDev --> DocsDevReadme["README.md"]
    DocsDev --> DocsDevComponents["components/"]
    DocsDevComponents --> DocsDevComponentsAPIKey["API Key Management.md"]
    DocsDevComponents --> DocsDevComponentsAPIKeySecurity["API Key Security.md"]
    DocsDevComponents --> DocsDevComponentsLogging["Logging.md"]

    %% Examples
    DocsExamples --> DocsExamplesConfig["config-examples/"]
    DocsExamplesConfig --> DocsExamplesConfigBasic["basic-config.yaml"]
    DocsExamples --> DocsExamplesTemplates["template-examples/"]
    DocsExamplesTemplates --> DocsExamplesTemplatesDefault["default.md.j2"]

    %% Internal docs
    DocsInternal --> DocsInternalIntro["INTRODUCTION.md"]
    DocsInternal --> DocsInternalKanban["Kanban meet2obsidian dev.md"]
    DocsInternal --> DocsInternalArch["Архитектура системы.md"]
    DocsInternal --> DocsInternalRoadmap["Дорожная карта.md"]
    DocsInternal --> DocsInternalTechStack["Технический стек.md"]
    DocsInternal --> DocsInternalRequirements["Функциональные и нефункциональные требования.md"]

    %% User docs
    DocsUser --> DocsUserReadme["README.md"]
    DocsUser --> DocsUserGettingStarted["getting-started/"]
    DocsUserGettingStarted --> DocsUserGettingStartedInstall["installation.md"]
    DocsUser --> DocsUserUsage["usage/"]
    DocsUserUsage --> DocsUserUsageLogging["logging.md"]
    DocsUserUsage --> DocsUserUsageAPIKeys["api-keys.md"]
    DocsUserUsage --> DocsUserUsageCLI["cli-commands.md"]

    %% Main Python package structure
    Meet2Obsidian --> Meet2ObsidianInit["__init__.py"]
    Meet2Obsidian --> Meet2ObsidianAPI["api/"]
    Meet2Obsidian --> Meet2ObsidianAudio["audio/"]
    Meet2Obsidian --> Meet2ObsidianNote["note/"]
    Meet2Obsidian --> Meet2ObsidianUtils["utils/"]
    Meet2Obsidian --> Meet2ObsidianCLI["cli.py"]
    Meet2Obsidian --> Meet2ObsidianCLICommands["cli_commands/"]
    Meet2Obsidian --> Meet2ObsidianConfig["config.py"]
    Meet2Obsidian --> Meet2ObsidianCore["core.py"]
    Meet2Obsidian --> Meet2ObsidianMonitor["monitor.py"]
    Meet2Obsidian --> Meet2ObsidianCache["cache.py"]

    %% CLI Commands
    Meet2ObsidianCLICommands --> Meet2ObsidianCLICommandsLogs["logs_command.py"]

    %% API Package
    Meet2ObsidianAPI --> Meet2ObsidianAPIInit["__init__.py"]
    Meet2ObsidianAPI --> Meet2ObsidianAPIClaude["claude.py"]
    Meet2ObsidianAPI --> Meet2ObsidianAPIRevai["revai.py"]

    %% Audio Package
    Meet2ObsidianAudio --> Meet2ObsidianAudioInit["__init__.py"]
    Meet2ObsidianAudio --> Meet2ObsidianAudioExtractor["extractor.py"]

    %% Note Package
    Meet2ObsidianNote --> Meet2ObsidianNoteInit["__init__.py"]
    Meet2ObsidianNote --> Meet2ObsidianNoteGenerator["generator.py"]
    Meet2ObsidianNote --> Meet2ObsidianNoteObsidian["obsidian.py"]

    %% Utils Package
    Meet2ObsidianUtils --> Meet2ObsidianUtilsInit["__init__.py"]
    Meet2ObsidianUtils --> Meet2ObsidianUtilsLogging["logging.py"]
    Meet2ObsidianUtils --> Meet2ObsidianUtilsSecurity["security.py"]
    Meet2ObsidianUtils --> Meet2ObsidianUtilsStatus["status.py"]

    %% Scripts
    Scripts --> ScriptsCheckVideos["check_videos.py"]
    Scripts --> ScriptsInstall["install.sh"]
    Scripts --> ScriptsSetupApiKeys["setup_api_keys.py"]
    Scripts --> ScriptsSetupLaunchAgent["setup_launchagent.sh"]
    
    %% Tmp files
    TmpFiles --> TmpConfigFixes["config_implementation_fixes.md"]
    TmpFiles --> TmpLoggingDocs["logging_tests_documentation.md"]
    TmpFiles --> TmpEpic7Report["epic7_logging_tests_report.md"]
    TmpFiles --> TmpEpic8Report["epic8_implementation_report.md"]
    TmpFiles --> TmpEpic9Report["epic9_implementation_report.md"]
    TmpFiles --> TmpEpicsSummary["completed_epics_summary.md"]

    %% Tests
    Tests --> TestsInit["__init__.py"]
    Tests --> TestsConftest["conftest.py"]
    Tests --> TestsRunTests["run_tests.py"]
    Tests --> TestsIntegration["integration/"]
    Tests --> TestsUnit["unit/"]

    %% Integration Tests
    TestsIntegration --> TestsIntegrationInit["__init__.py"]
    TestsIntegration --> TestsIntegrationPipeline["test_pipeline.py"]
    TestsIntegration --> TestsIntegrationSecurity["test_security_integration.py"]

    %% Unit Tests
    TestsUnit --> TestsUnitInit["__init__.py"]
    TestsUnit --> TestsUnitCLI["test_cli.py"]
    TestsUnit --> TestsUnitConfig["test_config.py"]
    TestsUnit --> TestsUnitCore["test_core.py"]
    TestsUnit --> TestsUnitLogging["test_logging.py"]
    TestsUnit --> TestsUnitSecurity["test_security.py"]

    %% Configuration Files
    ConfigFiles --> ProjectToml["pyproject.toml"]
    ConfigFiles --> Requirements["requirements.txt"]
    ConfigFiles --> Setup["setup.py"]
    ConfigFiles --> License["LICENSE"]
    ConfigFiles --> Readme["README.md"]
    ConfigFiles --> ClaudeMD["CLAUDE.md"]
    ConfigFiles --> ProjectStructureMD["PROJECT_STRUCTURE.md"]

    %% Styling
    classDef code fill:#f9f9f9,stroke:#666,stroke-width:1px
    classDef doc fill:#e8f4ea,stroke:#666,stroke-width:1px
    classDef test fill:#f2e8ea,stroke:#666,stroke-width:1px
    classDef config fill:#e8eaf4,stroke:#666,stroke-width:1px
    classDef tmp fill:#fef9e6,stroke:#666,stroke-width:1px

    class Meet2Obsidian,Meet2ObsidianAPI,Meet2ObsidianAudio,Meet2ObsidianNote,Meet2ObsidianUtils code
    class Docs,DocsAPI,DocsAssets,DocsDev,DocsExamples,DocsInternal,DocsUser doc
    class Tests,TestsIntegration,TestsUnit test
    class ConfigFiles,ProjectToml,Requirements,Setup,License,Readme,ClaudeMD,ProjectStructureMD config
    class TmpFiles,TmpConfigFixes,TmpLoggingDocs tmp
```

## Implementation Status

The project is in active development. Current status:

- **Core implementation**:
  - Configuration module (`config.py`) implementation completed ✅
  - Logging module fully implemented with structured logging and rotation ✅
  - Security module for API key management fully implemented ✅
  - Basic structure is set up for other modules
  - CLI commands system established for logs and API key management ✅

- **Documentation**:
  - Comprehensive documentation for completed components
  - Developer docs for API Key Security and Logging components
  - User documentation for Logging and API Keys
  - CLI command documentation
  - Internal developer docs available in `docs/internal_docs/`
  - API documentation in progress

- **Tests**:
  - Full testing infrastructure with conftest.py and run_tests.py ✅
  - Unit and integration tests for all implemented components ✅
  - Support for test markers and selective test execution ✅
  - Test-driven development approach being followed
  - Comprehensive CLI interface tests added ✅

- **Examples**:
  - Example of logging functionality
  - Example of secure API key management
  - Comprehensive examples showing usage of all implemented components

Key functional components:

- `utils/security.py`: KeychainManager for securely storing API keys in macOS Keychain ✅
- `config.py`: Configuration management system with JSON support and validation ✅
- `utils/logging.py`: Structured logging system with JSON format and rotation ✅
- `cli_commands/logs_command.py`: CLI commands for log management ✅
- `cli_commands/apikeys_command.py`: CLI commands for API key management ✅
- `scripts/setup_api_keys.py`: Script for setting up and testing API keys ✅

### Completed Epics:
- **Epic 6**: Configuration module implementation ✅ (2025-05-12)
- **Epic 7**: Tests for logging module ✅ (2025-05-12)
  - ✅ Task 1: Tests for logging configuration
  - ✅ Task 2: Tests for logging levels
  - ✅ Task 3: Tests for log rotation
  - ✅ Task 4: Tests for structured logging
- **Epic 8**: Implementation of logging module ✅ (2025-05-12)
  - ✅ Task 1: Configure structlog for structured logging
  - ✅ Task 2: Implement file and console output
  - ✅ Task 3: Configure log rotation
  - ✅ Task 4: Create convenient interface for obtaining loggers
- **Epic 9**: Tests for secure API key storage ✅ (2025-05-12)
  - ✅ Task 1: Tests for saving keys in Keychain
  - ✅ Task 2: Tests for retrieving keys from Keychain
  - ✅ Task 3: Tests for deleting keys
  - ✅ Task 4: Tests for error handling
  - ✅ Task 5: Integration tests with real system keychain
- **Epic 10**: Implementation of API key storage module ✅ (2025-05-12)
  - ✅ Task 1: Create class for working with Keychain through keyring library
  - ✅ Task 2: Implement API key saving
  - ✅ Task 3: Implement API key retrieval
  - ✅ Task 4: Implement API key deletion
  - ✅ Task 5: Create CLI commands for API key management
  - ✅ Task 6: Update API key setup tools
- **Epic 11**: Tests for CLI interface ✅ (2025-05-12)
  - ✅ Task 1: Tests for start/stop commands
  - ✅ Task 2: Tests for status command
  - ✅ Task 3: Tests for config command (prepared for future implementation)
  - ✅ Task 4: Tests for argument processing

Last Updated: 2025-05-13