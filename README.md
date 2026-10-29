
# MyAI-Assistant

Personal AI assistant for Android and Windows.

## About

MyAI-Assistant is a personal AI assistant project designed to simplify everyday tasks, research, document processing, data analysis, translation, and automation.

Development starts on Android, using browser-based tools and cloud services where possible. Later, the project will be extended to support development and local workflows on Windows.

The assistant will be modular, allowing new AI models, tools, and integrations to be added as the project evolves.

## Goals

- Build a practical personal AI assistant.
- Support voice-based interaction and commands.
- Process Excel spreadsheets and structured data.
- Connect different AI models through supported APIs.
- Extract information from photos and documents.
- Translate between Russian and Chinese.
- Automate repetitive tasks and file workflows.
- Integrate with OneDrive for document storage and processing.
- Support development on Android first and Windows later.
- Protect personal data, credentials, and business information.

## Planned Features

### 1. Voice Control

- Voice input for commands and questions.
- Text-to-speech responses where supported.
- Hands-free interaction as a future enhancement.
- Configurable language and voice settings.

### 2. Excel and Data Processing

- Read and process Excel workbooks and CSV files.
- Extract structured data from documents and photos.
- Create and update tables.
- Perform calculations and data validation.
- Generate summaries and reports.
- Support purchasing, inventory, and supplier data workflows.

### 3. Multiple AI Models

- Support different AI models through their available APIs.
- Use a configurable model selection mechanism.
- Separate model integration from the assistant's core logic.
- Handle API errors, usage limits, and unavailable services.
- Keep API credentials outside the source code.

Model availability, pricing, and capabilities will depend on the selected provider.

### 4. Photo and Document Recognition

- Extract text from photographs and scanned documents.
- Process invoices, receipts, product labels, and delivery documents.
- Convert extracted information into structured data.
- Allow users to review and correct recognized values.
- Validate important fields before updating tables.

Recognition results must be checked before they are used for important business decisions.

### 5. Russian-Chinese Translation

- Translate text between Russian and Chinese.
- Support simplified Chinese as the initial Chinese language option.
- Prepare supplier messages and purchasing requests.
- Translate product names, specifications, and business documents.
- Provide a workflow for future voice translation.
- Allow users to review translations before sending them.

Real-time speech translation will depend on available speech recognition, translation, and audio services.

### 6. Automation and OneDrive

- Work with selected files stored in OneDrive.
- Organize document-processing workflows.
- Transfer extracted information into approved tables.
- Automate repetitive tasks using supported integrations.
- Prepare workflows for Microsoft Excel and Power Automate.
- Require confirmation before consequential operations.

File access and automation will use explicitly authorized permissions.

## Technology

The technology stack has not yet been finalized.

Potential components include:

- Python for application logic.
- OpenAI API for optional AI model integration.
- Other AI providers through supported APIs.
- GitHub for version control and project collaboration.
- OpenAI Codex for coding assistance.
- Microsoft OneDrive for file storage.
- Microsoft Excel for spreadsheet workflows.
- Microsoft Power Automate for supported automation scenarios.
- Speech recognition, text-to-speech, and OCR tools where needed.

The final stack will be selected according to compatibility, security, cost, and availability.

## Project Structure

The project structure will be introduced incrementally.

The planned modules may include:

- `core/` — assistant logic and shared services.
- `models/` — AI model integrations.
- `voice/` — speech input and audio output.
- `documents/` — photo, OCR, and document processing.
- `spreadsheets/` — Excel and CSV processing.
- `translation/` — Russian-Chinese translation.
- `integrations/` — OneDrive and external services.
- `automation/` — reusable workflows.
- `tests/` — automated checks.
- `docs/` — setup instructions and technical documentation.

These are planned directories, not files or modules that already exist.

## Implementation Roadmap

### Phase 1 — Foundation and Security

- [x] Create the private GitHub repository.
- [x] Connect the repository to ChatGPT.
- [ ] Approve and add the initial README.
- [ ] Define the initial project structure.
- [ ] Select the first implementation approach compatible with Android.
- [ ] Establish rules for credentials, permissions, and data protection.

### Phase 2 — Basic AI Assistant

- [ ] Implement a basic question-and-answer workflow.
- [ ] Connect the first supported AI model.
- [ ] Add configuration and error handling.
- [ ] Document setup and usage.
- [ ] Test the basic workflow.

### Phase 3 — Documents and Spreadsheets

- [ ] Process selected photos and documents.
- [ ] Extract text and structured fields.
- [ ] Read and generate Excel or CSV data.
- [ ] Add validation and manual review.
- [ ] Generate basic reports.

### Phase 4 — Russian-Chinese Translation

- [ ] Add text translation between Russian and Chinese.
- [ ] Support supplier messages and product terminology.
- [ ] Add translation review.
- [ ] Evaluate speech translation options.

### Phase 5 — Voice Control and Multiple Models

- [ ] Add voice input.
- [ ] Add spoken responses where supported.
- [ ] Add configurable AI model selection.
- [ ] Handle provider failures and usage limits.
- [ ] Test language and voice workflows.

### Phase 6 — OneDrive and Automation

- [ ] Connect OneDrive using authorized access.
- [ ] Process files from selected folders.
- [ ] Integrate approved Excel workflows.
- [ ] Evaluate Power Automate for repetitive tasks.
- [ ] Add confirmations and error recovery.
- [ ] Test the complete document-to-spreadsheet workflow.

### Phase 7 — Windows Development

- [ ] Prepare a Windows development environment.
- [ ] Document installation and configuration.
- [ ] Test compatibility across Android-based workflows and Windows.
- [ ] Improve packaging, testing, and maintainability.

Phases may overlap when dependencies allow. Each feature should be tested before being considered complete.

## Security

- Never commit API keys, passwords, access tokens, or other secrets.
- Store credentials outside the source code.
- Use the minimum permissions required for each integration.
- Review changes before committing or publishing them.
- Do not grant external services unnecessary access to private data.
- Request confirmation before deleting files, overwriting important data, or sending external messages.
- Validate extracted document data before using it in business workflows.
- Avoid sending sensitive documents to external services without authorization.
- Keep logs free of credentials and unnecessary personal information.

## Development Principles

- Make changes in small, reviewable steps.
- Test functionality before considering it complete.
- Document setup, configuration, and known limitations.
- Avoid unnecessary dependencies.
- Prefer modular components that can be replaced independently.
- Keep Android-first workflows practical without requiring a local computer.
- Require approval before making significant changes.
- Do not claim a feature is implemented until it has been tested.

## Current Status

- [x] GitHub repository created.
- [x] Repository connected to ChatGPT.
- [ ] Initial README approved and added.
- [ ] Project structure created.
- [ ] First AI model integration implemented.
- [ ] Document and spreadsheet processing implemented.
- [ ] Russian-Chinese translation implemented.
- [ ] Voice control implemented.
- [ ] OneDrive integration implemented.
- [ ] Windows development workflow prepared.

## License

No license has been selected yet. The project is currently intended for personal use.
