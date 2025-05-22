# Strong's Number Embedding Project - README

## Main Purpose

The primary goal of the `strong_number_embedding` project is to develop a system, envisioned to leverage Artificial Intelligence (AI) and Large Language Models (LLM), to automate the insertion of Strong's Numbers into various Bible translations that currently lack them. This will make deep linguistic study of the Bible more accessible across different languages.

## Background - What are Strong's Numbers?

Strong's Numbers are unique numerical identifiers assigned to each root word in the original Hebrew of the Old Testament and the Greek of the New Testament. They were created by James Strong, a 19th-century American biblical scholar.

These numbers are invaluable for Bible study because they allow readers, even those without prior knowledge of Hebrew or Greek, to:
*   Easily access the original language word behind a translated word.
*   Look up dictionary definitions, etymologies, and grammatical information for that original word.
*   Find other occurrences of the same original word throughout the Bible (cross-referencing), providing a deeper understanding of its usage and meaning.

A good example of Strong's Numbers in action can be seen on websites like the Faith, Hope, Love (FHL) Bible study portal (bible.fhl.net), where users can toggle Strong's Numbers on and off to explore the original text connections.

## Current Status & Resources

This project builds upon existing work and data:

*   **Completed Versions:** Two major Bible translations have already been meticulously annotated with Strong's Numbers and serve as foundational examples or potential training data for AI models:
    *   UNV (Chinese Union Version, 和合本)
    *   KJV (King James Version)

*   **Key Data Resources:** The project utilizes several key data resources, typically processed into JSON format (see the `original_text_preparation` directory for how these are generated). The Bible texts and Strong's Number dictionary information are sourced with authorization from bible.fhl.net.
    *   UNV (Chinese Union Version) text with embedded Strong's Numbers.
    *   KJV (King James Version) text with embedded Strong's Numbers.
    *   The complete original Old Testament text in Hebrew (based on the Masoretic Text, e.g., Biblia Hebraica Stuttgartensia - BHS).
    *   The complete original New Testament text in Greek (e.g., FHL Westcott-Hort Greek New Testament).
    *   A comprehensive Hebrew Strong's Number dictionary (mapping numbers to Hebrew words, definitions, and usage).
    *   A comprehensive Greek Strong's Number dictionary (mapping numbers to Greek words, definitions, and usage).

## Key Challenges & Project Goals

The core challenge is to accurately and efficiently embed Strong's Numbers into new Bible translations. The project aims to address this by:

1.  **Automation:** Developing methods to automatically insert Strong's Numbers, significantly reducing the laborious manual effort traditionally required for such tasks.
2.  **Alignment:** Ensuring that words or phrases in the target translation are accurately aligned with the correct Strong's Numbers from the original Hebrew or Greek texts. While verse-level alignment is a given (i.e., we know which verse in the translation corresponds to which verse in the original), word-level alignment is the critical task.
3.  **Leveraging Existing Data:** Utilizing the already annotated UNV (Chinese Union Version) and KJV (King James Version) versions as training data, reference guides, or validation sets to improve the annotation process for new translations.
4.  **AI/LLM Exploration:** Actively exploring and applying state-of-the-art AI and LLM technologies to tackle the automation and alignment challenges. This includes investigating how these models can learn from the existing data to predict Strong's Number placements in untagged texts.

## Project Structure

The project is organized as follows:

*   **`original_text_preparation/`**: This subdirectory is crucial. It contains all the necessary scripts, source data (primarily SQLite databases), and documentation for generating the clean, structured JSON data resources listed above. The tools in this directory handle the extraction and formatting of Bible texts and Strong's dictionaries, providing the foundational datasets required for the main Strong's Number embedding task. (See `original_text_preparation/README.txt` for more details on its contents and usage).

*   **(Future Directories):** As the project evolves, directories for AI model development, training scripts, evaluation tools, and output for newly annotated Bible versions will be added.

This project hopes to significantly contribute to biblical scholarship and accessibility by making the rich insights provided by Strong's Numbers available to a wider global audience.
