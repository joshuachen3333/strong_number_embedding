# Software Design: Dual Synchronized Bible Reader

## 1. Overview

This document outlines the software design for the Dual Synchronized Bible Reader application. The application allows a user to view a main Bible reader and a second Bible reader that synchronizes its displayed chapter and verse with the main reader, while allowing independent control over version and Strong's number display in the second reader.

The current implementation is a client-side application using HTML, CSS, and JavaScript, with a mock mediator to simulate backend functionality and facilitate communication between the reader components on the same page.

## 2. Architecture

The application employs a **Mediator pattern** on the client-side to manage communication and data flow between the two reader components and the (simulated) data source.

*   **Upstream Data Source:** `bible.fhl.net` (specifically its `json/qb.php` API for Bible content and `json/sd.php` for Strong's definitions).
*   **Mock Mediator (`mock_mediator.js`):** A client-side JavaScript object that simulates a backend service. It is responsible for:
    *   Fetching data from `bible.fhl.net`'s JSON API (simulated by returning mock data structures that mimic the real API's responses).
    *   Providing a defined API for the reader components to request data.
    *   Managing the synchronization state (current book, chapter, verse).
    *   Orchestrating updates between the Main Reader and Second Reader in a same-page context (using callbacks).
*   **Main Reader Component (`main_reader_frontend.js` & HTML in `index.html`):** The primary reader interface.
    *   Displays Bible chapters.
    *   Detects user scrolling to determine the current verse.
    *   Reports its current passage to the Mock Mediator.
    *   Fetches content from the Mock Mediator.
*   **Second Reader Component (`second_reader_frontend.js` & HTML in `index.html`):** The secondary, synchronized reader.
    *   Displays Bible chapters based on synchronization data from the Mock Mediator.
    *   Allows independent selection of Bible version and Strong's number display.
    *   Fetches its specific content (with its chosen parameters) from the Mock Mediator.
    *   Scrolls to the synchronized verse.

## 3. Components

### 3.1. Mock Mediator (`mock_mediator.js`)

*   **Purpose:** Simulates a backend service for fetching Bible data and managing synchronization state. Enables decoupled development of frontend components.
*   **Key Responsibilities:**
    *   Expose an API for reader components (see API Contract below).
    *   (Simulate) Fetching data from `bible.fhl.net/json/qb.php` for chapter content and `bible.fhl.net/json/sd.php` for Strong's definitions.
    *   (Simulate) Transform data from the upstream API into a consistent format for the frontend components.
    *   Store the current synchronized passage (book, chapter, verse).
    *   Notify the Second Reader when the synchronized passage changes.
    *   Implement basic data caching (simulated).

### 3.2. Main Reader Frontend (`main_reader_frontend.js`)

*   **Purpose:** Provides the primary Bible reading interface and acts as the source for scroll synchronization.
*   **Key Responsibilities:**
    *   Allow user to select/load a Bible book and chapter.
    *   Request chapter content from the Mock Mediator.
    *   Render the received Bible content (verse numbers, text including Strong's tags).
    *   Detect the topmost visible verse during scrolling.
    *   Report the current verse to the Mock Mediator for synchronization.

### 3.3. Second Reader Frontend (`second_reader_frontend.js`)

*   **Purpose:** Provides a secondary Bible reading interface that stays synchronized with the Main Reader's passage but allows independent display settings.
*   **Key Responsibilities:**
    *   Allow user to select Bible version and toggle Strong's number display.
    *   Receive synchronization updates (book, chapter, verse) from the Mock Mediator.
    *   Request chapter content (for the synchronized chapter but with its own version/Strong's settings) from the Mock Mediator.
    *   Render the received Bible content.
    *   Automatically scroll to the synchronized verse.

## 4. Mediator API Contract (Simulated)

The Mock Mediator exposes the following conceptual API:

### 4.1. `GET /api/chapter` (Simulated by `mockMediator.fetchChapter`)

*   **Request Query Parameters:**
    *   `book` (string): English book name (e.g., "Luke").
    *   `chapter` (integer): Chapter number.
    *   `version` (string): Version code (e.g., "unv", "kjv").
    *   `strong` (integer): `1` for Strong's, `0` otherwise.
*   **Response (JSON):**
    ```json
    {
        "status": "success" | "error",
        "request": { /* echoed request params */ },
        "data": { // If success
            "book_engs": "Luke",
            "book_chineses": "路",
            "chapter_num": 12,
            "version_code": "unv",
            "version_name": "FHL和合本 (Mocked)",
            "verses": [
                { "verse_num": 1, "text": "Verse text with {<WGXXXX>} tags..." }
                // ... more verses
            ]
        },
        "message": "Error message if status is error"
    }
    ```

### 4.2. `POST /api/sync` (Simulated by `mockMediator.syncPosition`)

*   **Request Body (JSON):**
    ```json
    { "book": "Luke", "chapter": 12, "verse": 5, "mainReaderVersion": "unv" }
    ```
*   **Response (JSON):**
    ```json
    { "status": "success" | "error", "message": "Status message" }
    ```
*   **Side Effect:** Triggers update callback for the Second Reader.

### 4.3. `GET /api/strong_definition` (Simulated by `mockMediator.fetchStrongDefinition`)

*   **Request Query Parameters:**
    *   `number` (string): Strong's number (e.g., "G1722").
*   **Response (JSON):**
    ```json
    {
        "status": "success" | "error",
        "data": { // If success
            "strong_number": "G1722",
            "original_word": "...",
            "definition_zh": "...",
            "definition_en": "..."
        },
        "message": "Error message"
    }
    ```

## 5. Data Flow

### 5.1. Initial Load

1.  `main_reader_frontend.js` initializes.
2.  User (or default setting) selects book/chapter for Main Reader.
3.  Main Reader calls `mockMediator.fetchChapter()` for its content.
4.  Mock Mediator returns (simulated) chapter data.
5.  Main Reader renders content.
6.  Main Reader determines its initial verse and calls `mockMediator.syncPosition()`.
7.  `second_reader_frontend.js` initializes and registers its update function (`loadPassage`) with `mockMediator.registerSecondReaderUpdateCallback()`.
8.  `mockMediator.syncPosition()` (from step 6) invokes the Second Reader's registered update function (`loadPassage`) with the initial book, chapter, and verse.
9.  Second Reader calls `mockMediator.fetchChapter()` for its version of the content, using its own UI settings for version/Strong's.
10. Mock Mediator returns chapter data for Second Reader.
11. Second Reader renders content and scrolls to the initial verse.

### 5.2. Main Reader Scroll

1.  User scrolls Main Reader.
2.  `main_reader_frontend.js` detects new topmost verse.
3.  Main Reader calls `mockMediator.syncPosition()` with new book, chapter, verse.
4.  `mockMediator.syncPosition()` updates its internal state and invokes Second Reader's `loadPassage` callback with new passage details.
5.  Second Reader fetches new chapter data (if chapter changed) or uses existing data (if only verse changed within the same chapter), applying its own version/Strong's settings.
6.  Second Reader re-renders content and scrolls to the new verse.

### 5.3. Second Reader Setting Change

1.  User changes version or Strong's toggle in Second Reader.
2.  `second_reader_frontend.js` event listener fires.
3.  Second Reader calls `mockMediator.fetchChapter()` for the *currently synchronized chapter* but with its new display settings.
4.  Mock Mediator returns data.
5.  Second Reader re-renders its content and scrolls to the current synchronized verse.

## 6. Future Considerations (Beyond Mock Mediator)

*   Replacing `mock_mediator.js` with a real backend service.
*   Using WebSockets for real-time communication between readers (especially if they are in different browser windows/tabs or devices) and the backend mediator.
*   Implementing a proper database or more robust caching in the mediator.
*   Full implementation of clickable Strong's numbers with definition popups.

```
