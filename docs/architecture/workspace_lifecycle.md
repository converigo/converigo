# Workspace Lifecycle

This document describes the lifecycle stages of the workspace runtime object.

## Workspace Created
- Entry Condition: user selects one or more files from the landing page.
- Exit Condition: workspace mode is initialized and visible.
- Allowed Events:
  - `file-selected`
  - `workspace-files-updated`

## Upload
- Entry Condition: files are staged and previewed.
- Exit Condition: files are ready for conversion and a target format is selected.
- Allowed Events:
  - `format-selected`
  - `file-selected`
  - `workspace-files-updated`

## Queue
- Entry Condition: files are queued for conversion but conversion has not started.
- Exit Condition: user triggers the convert action.
- Allowed Events:
  - `format-selected`
  - `file-selected`

## Conversion
- Entry Condition: convert action is triggered.
- Exit Condition: backend conversion completes or fails.
- Allowed Events:
  - `upload-started`
  - `upload-progress`
  - `upload-finished`
  - `conversion-ready`
  - `conversion-completed`

## Preparing
- Entry Condition: conversion completes successfully and DownloadManager receives payload.
- Exit Condition: download payload is validated and ready.
- Allowed Events:
  - `download-ready`

## Download
- Entry Condition: download artifacts are available.
- Exit Condition: user begins download or chooses an alternate action.
- Allowed Events:
  - `download-ready`
  - click actions on download UI

## History
- Entry Condition: session completes or is checkpointed for future reference.
- Exit Condition: session state is persisted or archived.
- Allowed Events:
  - `history-updated`

## Destroy
- Entry Condition: user clears the workspace or refreshes the page.
- Exit Condition: workspace session state is reset.
- Allowed Events:
  - `file-selected` (new session begins)
  - reset/clear actions

## Notes

- The workspace lifecycle is the central runtime object in Converigo.
- It encapsulates the transition from landing to finished flow.
- This lifecycle is intentionally decoupled from homepage and legacy business logic.
