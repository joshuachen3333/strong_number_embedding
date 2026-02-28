# Spec: Spec Tooltip Control

## Overview

Define the behavior of the spec section tooltip feature, which displays specification section titles and summaries when hovering over section references like `[3.3.1]` in the parsed output.

## ADDED Requirements

### Requirement: Parser extracts spec section metadata dynamically

The parser SHALL dynamically extract section titles and summaries from the specification markdown file for all sections that have section numbers.

#### Scenario: Extracting section metadata from spec file

**Given** the specification file `SPECIFICATION_v1.8.md` contains section headers like:
```
#### 3.3.1 檢測算法（v1.8 通用版本：支持所有複合詞） <!-- spec:prefix -->
```
**When** the parser loads the spec file
**Then** the parser extracts:
- Section number: `3.3.1`
- Section title: `檢測算法（v1.8 通用版本：支持所有複合詞）`
- Section summary: First paragraph content (up to 200 characters)

### Requirement: Parser includes spec metadata in output

The parser output SHALL include a dedicated section containing spec reference metadata for all sections referenced in the parsed output.

#### Scenario: Spec metadata section in output

**Given** a parsed verse that references sections `[3.3.1]`, `[3.3.2]`, `[3.3.3]`
**When** the parser generates output
**Then** the output includes a spec metadata section:
```
Spec References Section:
[3.3.1]: 檢測算法（v1.8 通用版本：支持所有複合詞）
[3.3.2]: 合併規則（v1.8 通用版本）
[3.3.3]: 輸出格式
```

### Requirement: Spec checkbox control in right panel

The viewer SHALL display a "Spec" checkbox in the right panel header, positioned to the left of the Parsed/Raw/Notes toggle buttons.

#### Scenario: Spec checkbox placement

**Given** the viewer is loaded
**When** viewing the right panel header
**Then** a "Spec" checkbox appears to the left of the Parsed/Raw/Notes buttons
**And** the checkbox is unchecked by default

### Requirement: Spec reference elements are wrapped for tooltip

When the Spec checkbox is enabled, spec references in the parsed output SHALL be wrapped in elements that support hover tooltips.

#### Scenario: Spec reference wrapping

**Given** the Spec checkbox is checked
**And** the parsed output contains `[3.3.1]`
**When** rendering the parsed section
**Then** the reference is rendered as `<span class="spec-ref" data-spec="3.3.1" title="...">[3.3.1]</span>`

### Requirement: Hover tooltip displays spec content

When hovering over a spec reference with the Spec checkbox enabled, a CSS tooltip SHALL display the section title and summary.

#### Scenario: Tooltip on hover

**Given** the Spec checkbox is checked
**And** the parsed output contains a spec reference `[3.3.1]`
**When** the user hovers over `[3.3.1]`
**Then** a tooltip appears showing:
- Section number: `3.3.1`
- Section title: `檢測算法（v1.8 通用版本：支持所有複合詞）`

### Requirement: Tooltip uses CSS-only implementation

The tooltip SHALL be implemented using pure CSS (no JavaScript popup windows or modals).

#### Scenario: CSS tooltip implementation

**Given** a spec reference element with tooltip data
**When** the user hovers over it
**Then** the tooltip appears using CSS `:hover` and `::after` pseudo-elements
**And** no JavaScript event handlers are needed for tooltip display

### Requirement: Spec checkbox state persists in localStorage

The Spec checkbox state SHALL be saved to localStorage and restored on page reload.

#### Scenario: Checkbox state persistence

**Given** the user checks the Spec checkbox
**When** the page is reloaded
**Then** the Spec checkbox remains checked
