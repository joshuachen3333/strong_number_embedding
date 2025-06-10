# User Guide: Dual Synchronized Bible Reader

Welcome to the Dual Synchronized Bible Reader! This guide will help you set up and use this application.

## 1. Overview

The Dual Synchronized Bible Reader allows you to view two Bible text readers side-by-side (or top-bottom). The main reader acts as the primary navigation, and the second reader automatically synchronizes to display the same Bible passage (book, chapter, and verse). You can configure the second reader to use a different Bible version or toggle Strong's number display independently.

**Important Note:** This version of the application is a client-side demonstration and uses a **mock (simulated) backend**. All data is fetched based on predefined mock responses or simulated calls to `bible.fhl.net`'s JSON API. Synchronization currently works only when both readers are on the **same HTML page**.

## 2. Installation / Setup

As this is a client-side application, setup is straightforward:

1.  **Obtain Application Files:** Ensure you have the `dual_reader` directory and all its contents. This includes:
    *   `dual_reader/index.html`
    *   `dual_reader/DESIGN.md`
    *   `dual_reader/IMPLEMENTATION.md`
    *   `dual_reader/USER_GUIDE.md` (this file)
    *   `dual_reader/css/style.css`
    *   `dual_reader/js/mock_mediator.js`
    *   `dual_reader/js/main_reader_frontend.js`
    *   `dual_reader/js/second_reader_frontend.js`
    *   `dual_reader/js/app.js`
    (These files would typically be acquired by downloading and extracting a ZIP archive of the project or by cloning the Git repository.)

2.  **Directory Structure:**
    If you downloaded a ZIP, extract it. You should have a main project folder, and inside it, a `dual_reader` directory structured as follows:
    ```
    your_project_root_folder/
    └── dual_reader/
        ├── index.html
        ├── DESIGN.md
        ├── IMPLEMENTATION.md
        ├── USER_GUIDE.md
        ├── css/
        │   └── style.css
        └── js/
            ├── mock_mediator.js
            ├── main_reader_frontend.js
            ├── second_reader_frontend.js
            └── app.js
    ```
    (If you cloned a Git repository that also contains an `original_text_preparation` folder at the root, the `dual_reader` folder will be alongside it.)

3.  **Open in Browser:** Navigate into the `dual_reader` directory and open the `index.html` file (i.e., `your_project_root_folder/dual_reader/index.html`) in a modern web browser (e.g., Chrome, Firefox, Edge, Safari).
    *   You can usually do this by double-clicking this `index.html` file or using your browser's "File > Open File..." menu and navigating to it.

No server setup is required for this version.

## 3. How to Use

Once `index.html` is open in your browser, you will see two reader panels: "Main Reader" and "Second Reader".

### 3.1. Main Reader

*   **Loading Content:**
    1.  **Select Book:** Choose a Bible book from the "Book" dropdown (e.g., "Luke").
    2.  **Enter Chapter:** Type a chapter number into the "Chapter" input field (e.g., 12).
    3.  **Click "Load Chapter":** The main reader will display the selected chapter. (By default, it loads 'UNV' version with Strong's numbers enabled).
*   **Scrolling and Synchronization:**
    *   As you scroll through the Main Reader, the application will identify the verse at the top of its view.
    *   This current passage (book, chapter, and verse) will be communicated to the Second Reader, which will then update its display accordingly.

### 3.2. Second Reader

*   **Automatic Synchronization:** The Second Reader will automatically load and attempt to scroll to the passage shown in the Main Reader.
*   **Independent Controls:**
    *   **Version:** You can select a different Bible version for the Second Reader using its "Version" dropdown (e.g., "KJV", "ESV"). When you change the version, the Second Reader will reload the currently synchronized chapter in the newly selected version.
    *   **Strong's Numbers:** You can toggle the display of Strong's numbers for the Second Reader using the "Strong's Numbers" checkbox. This will also cause the Second Reader to reload its view of the current chapter with the new setting.
        *   **Note on Strong's Numbers:** Strong's number tags (e.g., `{<WG1722>}`) are currently displayed as plain text within the verse. They are not yet clickable for definitions.

## 4. Features and Limitations

### Features:

*   Dual reader interface.
*   Main reader controls chapter navigation.
*   Second reader synchronizes to the main reader's passage.
*   Second reader has independent controls for Bible version and Strong's number display.
*   Content is based on (mocked) `bible.fhl.net` JSON API, including embedded Strong's number tags.

### Current Limitations:

*   **Mock Backend:** The application uses a `mock_mediator.js` to simulate all backend interactions and API calls to `bible.fhl.net`. It does not make live calls to the internet in its current state. The Bible text provided is sample/mock data generated by this simulator.
*   **Same-Page Only:** Synchronization only works because both reader components are on the same HTML page and communicate via client-side JavaScript. Cross-device or cross-browser-tab synchronization is not supported in this version.
*   **Strong's Number Interactivity:** Strong's number tags are displayed as text and are not clickable for definitions.
*   **Book Selection:** The list of books in the Main Reader's dropdown is a predefined sample and may not be exhaustive.
*   **Error Handling:** Basic error messages are shown, but error handling is not exhaustive.
*   **No User Data Persistence:** Settings for the second reader (version, Strong's toggle) are not saved between browser sessions.

## 5. Troubleshooting

*   **Content Not Loading:** Ensure `index.html` and the `js/` and `css/` subdirectories are all correctly placed within the `dual_reader` folder. Check your browser's developer console (usually opened with F12) for any error messages about missing files.
*   **Synchronization Issues:** This version is designed for same-page operation. If you've modified the files or are trying to run components separately, synchronization will not work.

Enjoy using the Dual Synchronized Bible Reader!
```
