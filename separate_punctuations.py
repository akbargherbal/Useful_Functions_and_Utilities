import re

def separate_punctuations_file(input_file_path, output_file_path):
    with open(input_file_path, 'r') as input_file, open(output_file_path, 'w') as output_file:
        for line in input_file:
            # Use regular expression to find all punctuations in the line
            punctuations = re.findall(r'[^\w\s]', line)

            # Replace all punctuations with spaces and split the line into words
            words = re.sub(r'[^\w\s]', ' ', line).split()

            # Create a list to hold the final output
            output = []

            # Loop through each word in the list of words
            for word in words:
                # If the word has punctuations, add them to the output list separately
                if any(p in word for p in punctuations):
                    word_punctuations = [p for p in word if p in punctuations]
                    word = re.sub(r'[^\w\s]', '', word)
                    output.extend([word] + word_punctuations)
                else:
                    # Otherwise, add the word to the output list as is
                    output.append(word)

            # Join the words and punctuations in the output list and write to the output file
            output_line = ' '.join(output) + '\n'
            output_file.write(output_line)

if __name__ == '__main__':
    input_file = input('Enter the input file path: ')
    output_file = input('Enter the output file path: ')
    separate_punctuations_file(input_file, output_file)
    
