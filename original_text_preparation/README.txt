Here's a summary of the GitHub project `strong_number_embedding`'s `original_text_preparation` directory:

**Purpose of `original_text_preparation`:**

This directory contains tools and data for processing biblical texts as a foundational step for the broader `strong_number_embedding` project. Its primary goal is to prepare various Bible versions and Strong's Number resources, making them ready for the main project task, which is to embed Strong's Numbers into other Bible translations that do not yet have them. The scripts and data here allow for:
*   Extraction of Strong's Number dictionaries (mapping numbers to words and their meanings for both Old and New Testaments).
*   Extraction of various Bible versions (like KJV, Chinese Union Version, and original Hebrew and Greek texts) into a structured JSON format, with options to include or exclude the Strong's Numbers.

This prepared data serves as a finished guideline and resource for embedding Strong's numbers into additional Bible versions.

**Project Structure and Key Components within `original_text_preparation`:**

*   **`source_sqlite/`**: This directory holds the source SQLite database files (e.g., `bible_little.db`, `bible_kjv.db`) that contain the Bible texts and Strong's number information.
*   **`bible_text_json/`**: This directory is the output location for the extracted Bible texts in JSON format.
*   **`strong_dict_json/`**: This directory is the output location for the generated Strong's number dictionaries in JSON format.
*   **`helper_scripts/`**: Contains shell scripts that automate the extraction processes (e.g., `batch_extract_strong_dictionary_words2.sh`, `extract_whole_bible_db2json2.sh`).
*   **`doc/`**: Includes README files and documentation explaining how to use the scripts and understand the data formats.

**How to Use the Scripts (Based on READMEs in `doc/`):**

1.  **Generating Strong's Number Dictionaries:**
    *   Navigate to the `strong_dict_json` directory.
    *   You'll need the `batch_extract_strong_dictionary_words2.sh` script (copied from `helper_scripts/`) and the `bible_little.db` database file (copied from `source_sqlite/`).
    *   Running the script with parameters like `./batch_extract_strong_dictionary_words2.sh 1 9015 ot` will produce `strong_number_words_dict_1_9015_ot.json` for the Old Testament. A similar command is used for the New Testament.
2.  **Extracting Bible Versions:**
    *   Navigate to the `bible_text_json` directory or another working directory.
    *   Use the `extract_whole_bible_db2json2.sh` script (copied from `helper_scripts/`).
    *   You specify the input database file using the `-f` flag (e.g., `-f ../source_sqlite/bible_kjv.db`) and the desired version using the `-d` flag (e.g., `-d kjv`).
    *   This allows extraction of versions like UNV (Union Version), KJV (King James Version), BHS (Biblia Hebraica Stuttgartensia - Old Testament), and FHLWH (FHL Westcott-Hort Greek New Testament), with or without embedded Strong's numbers.

**Potential Use Cases for the Output Data:**

The structured JSON data produced by these preparation scripts can be valuable for:
*   **Input for the main `strong_number_embedding` goal:** Providing clean, aligned texts and dictionaries for embedding Strong's numbers into new Bible versions.
*   **Advanced Bible Study Tools:** Creating software for cross-lingual word studies, building interlinear Bibles, generating concordances, and comparing translations.
*   **Linguistic and Theological Research:** Facilitating lexical analysis of biblical texts and comparative linguistics.
*   **Natural Language Processing (NLP) and AI Applications:** Providing datasets for training machine translation models or developing semantic search for biblical texts.

In essence, the `original_text_preparation` directory provides a command-line toolkit to transform raw biblical data from SQLite databases into more accessible JSON formats, enriched with Strong's Numbers, ready for the primary embedding task or other scholarly and technical applications.
