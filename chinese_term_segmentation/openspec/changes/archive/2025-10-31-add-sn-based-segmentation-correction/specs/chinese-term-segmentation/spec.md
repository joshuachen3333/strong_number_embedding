# Spec Delta: Chinese Term Segmentation - SN-Based Correction

This spec delta describes changes to the `chinese-term-segmentation` capability for Strong's Number-based segmentation correction.

## ADDED Requirements

### Requirement: Strong's Number Boundary Parser

The system SHALL parse UNV text with Strong's Numbers to extract authoritative Chinese term boundaries.

#### Scenario: Parse UNV with Strong's Numbers
**Given**: UNV text "神<H430>愛<H157>世人<H5971>"
**When**: StrongsNumberParser parses the text
**Then**: Extracts [("神", ["H430"]), ("愛", ["H157"]), ("世人", ["H5971"])]

---

### Requirement: Segmentation Boundary Corrector

The system SHALL correct initial segmentation results to align with UNV+SN standard boundaries.

#### Scenario: Merge Incorrectly Split Terms
**Given**: Initial segmentation ["獨生", "子"], UNV standard ["獨生子"]
**When**: BoundaryCorrector applies corrections
**Then**: Merges to ["獨生子"] and reports 1 merge correction

---

### Requirement: CLI Integration for SN Correction

The system SHALL provide a `--correct-with-sn` CLI flag to enable SN-based correction.

#### Scenario: Use --correct-with-sn Flag
**Given**: User runs `segment.py --verse "John 3:16" --version lcc --seg jieba --correct-with-sn`
**When**: CLI processes the command
**Then**: Displays initial segmentation, UNV reference, corrected segmentation, and metrics

---

### Requirement: Performance for SN Correction

The system SHALL add less than 100ms latency per verse for SN-based correction.

#### Scenario: Single Verse Performance
**Given**: A single verse correction request
**When**: System applies SN-based correction
**Then**: Additional latency is less than 100ms

## MODIFIED Requirements

### Requirement 2: Plugin-Based Segmentation Architecture

**What Changed**: Extended to support two-stage segmentation pipeline (initial + correction).

**Backward Compatibility**: Stage 2 is opt-in via `--correct-with-sn` flag. Default behavior unchanged.

#### Scenario: Backward Compatibility
**Given**: User runs segment.py without `--correct-with-sn`
**When**: System processes segmentation
**Then**: Behaves exactly as before (single-stage only)
