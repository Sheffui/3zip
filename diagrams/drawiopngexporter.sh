#!/bin/bash

# Default values
DRAWIO_DIR=""
OUTPUT_DIR=""

# Function to display usage instructions
usage() {
    echo "Usage: $0 -i /path/to/drawio/files [-o /path/to/output/png/files]"
    echo "  -i: Specify the input directory containing .drawio files (required)."
    echo "  -o: Specify the output directory for PNG files (optional, defaults to <input_dir>/png)."
    exit 1
}

# Parse command-line arguments
while getopts ":i:o:" opt; do
    case ${opt} in
        i)
            DRAWIO_DIR="$OPTARG"
            ;;
        o)
            OUTPUT_DIR="$OPTARG"
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            usage
            ;;
        :)
            echo "Option -$OPTARG requires an argument." >&2
            usage
            ;;
    esac
done

# Validate input directory
if [[ -z "$DRAWIO_DIR" ]]; then
    echo "Error: Input directory (-i) is required."
    usage
fi

# Set default output directory if not provided
if [[ -z "$OUTPUT_DIR" ]]; then
    OUTPUT_DIR="$DRAWIO_DIR/png"
fi

# Create the output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Iterate over all .drawio files in the input directory
for file in "$DRAWIO_DIR"/*.drawio; do
    # Check if the file exists (in case no .drawio files are found)
    if [[ -f "$file" ]]; then
        # Extract the base name of the file (without extension)
        base_name=$(basename "$file" .drawio)

        # Export the .drawio file as a PNG
        /usr/bin/drawio --export --format png --output "$OUTPUT_DIR/$base_name.png" "$file"

        echo "Exported: $file -> $OUTPUT_DIR/$base_name.png"
    else
        echo "No .drawio files found in $DRAWIO_DIR"
        exit 1
    fi
done
