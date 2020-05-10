"""
Author: Anshul Pardhi
The program performs tokenization and stemming of Cranfield documents collection
"""
import time
import glob
import re
import xml.etree.ElementTree as et
from collections import Counter
# from nltk.stem.porter import PorterStemmer
from porter_stemmer_tartarus import PorterStemmer

start_time = time.time()  # The start time of program execution
directory = "/people/cs/s/sanda/cs6322/Cranfield/*"  # Change to point to the respective directory
# directory = "Cranfield/*"  # Change to point to the respective directory
collection = glob.glob(directory)  # Get all the files from the directory in a list

tokens = []  # Initialize the list of tokens, it will contain the final tokens

# Repeat for every file in the collection
for file in collection:
    root = et.parse(file)  # Get the root DOM element from the file

    # Repeat for all child DOM elements
    for values in root.findall('*'):
        sgml_values = values.text  # Get the value
        sgml_values = sgml_values.strip()  # Remove preceding and trailing spaces
        sgml_values = sgml_values.replace("\n", " ")  # Remove the end of line escape character
        sgml_values = re.sub(r'[^a-zA-Z0-9.\s]', ' ', sgml_values)  # Replace all non-alphanumeric characters with space
        sgml_values = re.sub(r'[^a-zA-Z0-9\s]', '', sgml_values)  # Remove all dots, e.g. U.S.A. becomes USA
        sgml_values = sgml_values.lower()  # Convert all letters to lowercase
        token_list = sgml_values.split()  # Split individual words on spaces
        for token in token_list:
            tokens.append(token)  # Append every split word to the list of tokens

# Print the time it took to gather the tokens from the collection
print("Tokenization time:", round(time.time() - start_time, 2), "seconds")

# Get the frequency of each token
token_count = Counter(tokens)
token_1 = []
for counts in token_count.most_common():
    if counts[1] == 1:
        token_1.append(counts[0])  # Get all the tokens appearing only once in the collection

# Print the answers to the asked questions
print("1. The number of tokens in the Cranfield text collection:", len(tokens))
print("2. The number of unique words in the Cranfield text collection:", len(set(tokens)))
print("3. The number of words that occur only once in the Cranfield text collection:", len(token_1))
print("4. The 30 most frequent words in the Cranfield text collection:", token_count.most_common(30))
print("5. The average number of word tokens per document:", len(tokens) // len(collection))

# Stemming begins!
stem_start_time = time.time()  # The start time of stemming execution
stemmer = PorterStemmer()  # Using PorterStemmer from NLTK for stemming

stem_list = []  # Initialize the list of stems, it will contain the final stems

# Repeat for every token in the list of tokens
for token in tokens:
    stemmed_token = stemmer.stem(token, 0, len(token) - 1)  # Use PorterStemmer to stem the token
    stem_list.append(stemmed_token)  # Append the stem to the list of stems

# Print the time it took for stemming
print("Stemming time:", round(time.time() - stem_start_time, 2), "seconds")

# Get the frequency of each stem
stem_count = Counter(stem_list)
stem_1 = []
for counts in stem_count.most_common():
    if counts[1] == 1:
        stem_1.append(counts[0])  # Get all the stems appearing only once in the collection

# Print the answers to the asked questions
print("1. The number of distinct stems in the Cranfield text collection:", len(set(stem_list)))
print("2. The number of stems that occur only once in the Cranfield text collection:", len(stem_1))
print("4. The 30 most frequent stems in the Cranfield text collection:", stem_count.most_common(30))
print("5. The average number of word-stems per document:", len(stem_list) // len(collection))

# Print the time it took for the whole program to run
print("Total time:", round(time.time() - start_time, 2), "seconds")
