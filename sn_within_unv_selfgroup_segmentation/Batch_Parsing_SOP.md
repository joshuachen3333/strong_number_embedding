  SOP: Batch Parsing of UNV+SN Biblical Text (Revised)

  1.0 Objective

  To systematically parse a range of biblical verses, from a specified start point to a specified end point, and save the formatted output to individual files.

  2.0 Prerequisites

   1. Core Parsing Logic: The SPECIFICATION_v1.5.md file must be present. This document contains the key logic, token definitions, and rules for parsing the raw UNV+SN text.
   2. Output Format: The UNV_SN_Output_Format.md file must be present, as it defines the exact final output format to be used.
   3. Data Retrieval Script: The fetch_text.sh script must be available and executable.

  3.0 Procedure

  3.1 Initialization

   1. Receive Input: Acknowledge the starting and ending book, chapter, and verse for the batch job (e.g., "Parse from Genesis 1:1 to Genesis 1:15").
      *   **Automated Start Point (if only book provided):** If only a book is provided without specific starting and ending chapter/verse, the system will automatically determine the starting point. For an existing book, it will look at the last chapter and last verse processed and continue from the next verse. For a new book, it will start from chapter 1, verse 1.
   2. Create Directories: For each chapter in the request, create the necessary output directory structure using the mkdir -p command. The path should be output/{Book}/{Chapter}/.
       * Example: For a request to parse Genesis 1, create output/Gen/1/.

  3.2 Iteration

  Process each verse sequentially from the start point to the end point. For each verse:

   1. Fetch Data: Execute the fetch_text.sh script with the appropriate --engs, --chap, and --sec arguments to retrieve the JSON data from both qb.php and qp.php.

   2. Parse and Format:
       * Parse the bible_text from qb.php and the record array from qp.php by applying the core tokenization and grouping rules defined in `SPECIFICATION_v1.5.md`.
       * Generate the final formatted output string, strictly adhering to all presentation rules outlined in the `UNV_SN_Output_Format.md` file. This includes:
           * Correctly formatting individual and grouped Strong's numbers.
           * Adding *N references for morphology codes.
           * Appending the raw bible_text string.
           * Appending the Morphology Notes section.

   3. Handle Uncertainty:
       * During the parsing of a verse, if any ambiguity or data inconsistency is encountered that cannot be resolved with certainty (e.g., a Strong's number from qb.php is missing in
         qp.php), take the following steps:
           * Set the output filename to {verse_number}_uncertain.
           * Append a --- UNCERTAINTY NOTES --- section to the end of the file.
           * In this section, clearly and concisely describe the issue that was encountered.

   4. Write to File:
       * Use the write_file tool to save the complete, formatted output to the corresponding file in the directory created in step 3.2.
       * Standard filename: output/{Book}/{Chapter}/{verse_number}
       * Uncertainty filename: output/{Book}/{Chapter}/{verse_number}_uncertain

  3.3 Completion

   1. After the last verse in the range has been processed, announce that the batch job is complete and confirm the range of verses that were processed.


