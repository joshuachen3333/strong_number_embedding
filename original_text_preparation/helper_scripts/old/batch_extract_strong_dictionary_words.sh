#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <start_strong_number> <end_strong_number> [nt|ot]"
  exit 1
fi

# Validate that arguments are integers
if ! [[ "$1" =~ ^[0-9]+$ ]] || ! [[ "$2" =~ ^[0-9]+$ ]]; then
  echo "Error: Start and End Strong Numbers must be integers."
  exit 1
fi

# Assign and validate the range
START=$1
END=$2

if [ "$END" -le "$START" ]; then
  echo "Error: End number must be greater than start number."
  exit 1
fi

# Determine if the third argument is provided; default to 'ot'
MODE=${3:-ot}

# Validate the third argument
if [[ "$MODE" != "nt" && "$MODE" != "ot" ]]; then
  echo "Error: Invalid mode. Use 'nt' for New Testament or 'ot' for Old Testament."
  exit 1
fi

# Check if the helper script exists
HELPER_SCRIPT="./extract_strong_dictionary_word.sh"
if [ ! -f "$HELPER_SCRIPT" ]; then
  echo "Error: Required script '$HELPER_SCRIPT' not found."
  exit 1
fi

# Define suffixes for alphabetic entries
SUFFIXES=("a" "b")

# Print verbose message about the query range and mode
echo "Querying for ($MODE) Strong Numbers from $START to $END"

# Initialize JSON array
output="["

# Loop through the main range
for (( i=START; i<=END; i++ )); do
  # Process the base number (pure integer)
  echo "Processing Strong Number $i..."
  json=$("$HELPER_SCRIPT" "$i" "$MODE" 2>/dev/null)
  if [ -n "$json" ] && [[ "$json" == *"{"* ]]; then
    output+="$json,"
  else
    echo "Warning: No result for Strong Number $i."
  fi

  # Process alphanumeric Strong Numbers (e.g., 5238a, 5238b)
  for suffix in "${SUFFIXES[@]}"; do
    strong_number="${i}${suffix}"
    json=$("$HELPER_SCRIPT" "$strong_number" "$MODE" 2>/dev/null)
    if [ -n "$json" ] && [[ "$json" == *"{"* ]]; then
      output+="$json,"
    fi
  done
done

# Remove the trailing comma and close the JSON array
output=${output%,}
output+="]"

# Generate the output filename dynamically
# FILENAME="output_${MODE}_${START}_${END}.json"
FILENAME="strong_number_words_dict_${START}_${END}_${MODE}.json"

# Write the JSON array to the file
echo "$output" | jq . > "$FILENAME"

# Print completion message with the output file name
echo "JSON data saved to $FILENAME"
