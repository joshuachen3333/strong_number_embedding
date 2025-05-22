#!/bin/bash

# Function to display usage instructions
usage() {
    echo "Usage: $0 [dic_type] [max_strong_number]"
    echo "  dic_type: 0 or 1 (default is 1)"
    echo "  max_strong_number: positive integer (default is 8853)"
    exit 1
}

# Check if help is requested or no arguments are passed
if [ "$1" == "--help" ] || [ "$1" == "-h" ] || [ $# -eq 0 ]; then
    usage
fi

# Parse arguments
dic_type="$1"
max_strong_number="$2"

# Set default values if arguments are missing OT=1 NT=0
if [ -z "$dic_type" ]; then
    dic_type=1
fi

## OT=8853 NT=5877
if [ -z "$max_strong_number" ]; then
    max_strong_number=8853
fi

# Validate dic_type
if [ "$dic_type" != "0" ] && [ "$dic_type" != "1" ]; then
    echo "Error: dic_type must be 0 or 1."
    usage
fi

# Validate max_strong_number
if ! [[ "$max_strong_number" =~ ^[1-9][0-9]*$ ]]; then
    echo "Error: max_strong_number must be a positive integer."
    usage
fi

# Initialize an empty array to hold records
records=()

# Initialize a counter for successful records
success_count=0

# Loop from 1 to max_strong_number
for i in $(seq 1 "$max_strong_number"); do
    # Fetch data for the current strong number with specified dic_type
    response=$(curl -s "https://bible.fhl.net/json/sd.php?k=$i&N=$dic_type")

    # Check if the status is 'success'
    status=$(echo "$response" | jq -r '.status')

    if [ "$status" == "success" ]; then
        # Extract the record
        record=$(echo "$response" | jq '.record[0]')

        # Append the record to the records array
        records+=("$record")

        # Increment the success counter
        success_count=$((success_count + 1))
    fi

    # Optional: Display progress
    echo "Processed strong number $i, total successful records: $success_count"

    # Optional: Sleep to avoid overwhelming the server (adjust the duration as needed)
    sleep 0.1
done

# Build the final JSON object
json_output=$(jq -n --argjson count "$success_count" --argjson records "$(printf '%s\n' "${records[@]}" | jq -s '.')" '{
  "record_count": $count,
  "record":
  $records
}')

# Write the JSON output to a temporary file
temp_file="temp.json"
echo "$json_output" > "$temp_file"

# Reformat the JSON to meet the indentation requirements using a Python script
output_file="dictionary.json"

python3 - <<EOF
import json

# Load JSON data from the temporary file
with open('$temp_file', 'r', encoding='utf-8') as f:
    data = json.load(f)

def format_json(data):
    lines = []
    lines.append('{')
    lines.append('  "record_count": %d,' % data['record_count'])
    lines.append('  "record":')
    lines.append('  [')

    records = data['record']
    for idx, record in enumerate(records):
        lines.append('  {')
        items = list(record.items())
        for i, (key, value) in enumerate(items):
            value_str = json.dumps(value, ensure_ascii=False)
            comma = ',' if i < len(items) - 1 else ''
            lines.append('    "%s": %s%s' % (key, value_str, comma))
        if idx < len(records) - 1:
            lines.append('  },')
        else:
            lines.append('  }')
    lines.append('  ]')
    lines.append('}')

    # Write the formatted JSON to the output file
    with open('$output_file', 'w', encoding='utf-8') as out_file:
        out_file.write('\n'.join(lines))

format_json(data)
EOF

# Remove the temporary file
rm "$temp_file"

echo "Scraping complete. Total successful records: $success_count"
