import re
from collections import Counter
import argparse

# Constants
MIN_STRING_LENGTH = 20  # Minimum length of string to consider for abbreviation
MIN_OCCURRENCES = 40  # Minimum number of occurrences to abbreviate a string
DATE_TIME_PATTERN = r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}' # change the date time pattern 

def load_log_file(file_path):
    with open(file_path, 'r') as file:
        return file.readlines()

def find_frequent_strings(log_lines):
    all_words = ' '.join(log_lines).split()
    long_strings = [word for word in all_words if len(word) >= MIN_STRING_LENGTH]
    return Counter(long_strings)

def create_abbreviations(frequent_strings):
    return {string: f'STRING_{i:02d}' for i, (string, count) in enumerate(frequent_strings.items(), 1) if count >= MIN_OCCURRENCES}

def abbreviate_log(log_lines, abbreviations):
    abbreviated_lines = []
    for line in log_lines:
        # Replace date-time stamp
        line = re.sub(DATE_TIME_PATTERN, 'DTS', line)
        
        # Replace frequent long strings
        for original, abbr in abbreviations.items():
            line = line.replace(original, abbr)
        
        abbreviated_lines.append(line)
    
    return abbreviated_lines

def create_legend(abbreviations):
    legend = [
        "-----------",
        "Log Legends; in order to save message space, the following strings were shortened:",
        "DTS; stands for Date Time Stamp"
    ]
    for original, abbr in abbreviations.items():
        legend.append(f"{abbr}; stands for {original}")
    legend.append("-----------")
    return legend

def main(input_file, output_file):
    log_lines = load_log_file(input_file)
    frequent_strings = find_frequent_strings(log_lines)
    abbreviations = create_abbreviations(frequent_strings)
    
    abbreviated_lines = abbreviate_log(log_lines, abbreviations)
    legend = create_legend(abbreviations)
    
    with open(output_file, 'w') as file:
        file.write('\n'.join(legend))
        file.write('\n\n')
        file.writelines(abbreviated_lines)
    
    print(f"Abbreviated log file created: {output_file}")
    print(f"Original line count: {len(log_lines)}")
    print(f"Abbreviated line count: {len(abbreviated_lines) + len(legend) + 1}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Abbreviate log files to reduce size.")
    parser.add_argument("input_file", help="Path to the input log file")
    parser.add_argument("output_file", help="Path to the output abbreviated log file")
    args = parser.parse_args()
    
    main(args.input_file, args.output_file)
