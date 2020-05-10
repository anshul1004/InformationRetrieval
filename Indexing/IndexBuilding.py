"""
Author: Anshul Pardhi
The program performs creates ucompressed and compressed indexes from a set of
lemmatized and stemmed tokens from Cranfield document collection
"""

import sys
import time
import glob
import re
import xml.etree.ElementTree as et
from collections import Counter
from porter_stemmer_tartarus import PorterStemmer
from nltk.stem import WordNetLemmatizer
from collections import OrderedDict


def get_unsorted_index(index_unsorted, word_list, doc_id_counter, doclen):
    """
    Update the unsorted index posting list and get max_tf
    :param index_unsorted:
    :param word_list:
    :param doc_id_counter:
    :param doclen:
    :return: index_unsorted, max_tf
    """
    count = Counter(word_list)
    max_tf = count.most_common(1)[0][1]
    for counts in count.items():
        # Add -> to separate different documents inside the posting list
        # Posting list is of the form doc_id1:tf1:max_tf1:doclen1->doc_id2:tf2:max_tf2:doclen2 and so on
        if counts[0] in index_unsorted:
            index_unsorted.update({counts[0]: str(index_unsorted.get(counts[0])) + "->" + str(
                doc_id_counter) + ":" + str(counts[1]) + ":" + str(max_tf) + ":" + str(doclen)})
        else:
            index_unsorted.update(
                {counts[0]: str(doc_id_counter) + ":" + str(counts[1]) + ":" + str(max_tf) + ":" + str(doclen)})
    return index_unsorted, max_tf


def get_gamma_code(input_val):
    """
    Performs gamma encoding on the input string
    :param input_val:
    :return: gamma coded string
    """
    bin_val = bin(int(input_val)).replace("0b", "")
    offset = str(bin_val[1:])
    unary = ""
    for i in range(len(offset)):
        unary += "1"
    unary += "0"
    return unary + offset


def get_delta_code(input_val):
    """
    Performs delta encoding on the input string
    :param input_val:
    :return: delta coded string
    """
    bin_val = bin(int(input_val)).replace("0b", "")
    length = get_gamma_code(len(str(bin_val)))
    offset = str(bin_val[1:])
    return length + offset


def get_common_prefix(input_arr):
    """
    Get common prefix for a particular block for front coding
    :param input_arr:
    :return: common prefix
    """
    input_arr.sort(reverse=False)
    str1 = input_arr[0]
    str2 = input_arr[len(input_arr) - 1]
    len1 = len(str1)
    len2 = len(str2)
    prefix = ""
    i = 0
    j = 0
    while i < len1 and j < len2:
        if str1[i] != str2[j]:
            break
        prefix += str1[i]
        i += 1
        j += 1
    return prefix


def get_front_coding_key_str(front_coding_list, key_str):
    """
    Generate front coded string for a particular block
    :param front_coding_list:
    :param key_str:
    :return: key_str
    """
    common_prefix = get_common_prefix(front_coding_list)
    # Key string is of the form len(common_prefix)common_prefix*remaining_first_word+len(remaining_word)<>remaining_word
    # and so on
    if common_prefix != "":
        remaining_first_word = front_coding_list[0].split(common_prefix, 1)[1]
        if remaining_first_word != "":
            key_str += str(len(front_coding_list[0])) + str(common_prefix) + "*" + str(remaining_first_word)
        else:
            key_str += str(len(common_prefix)) + str(common_prefix) + "*"

    for word in front_coding_list:
        if common_prefix == "":
            key_str += str(len(word)) + str(word)
        else:
            if word != front_coding_list[0]:
                remaining_word = word.split(common_prefix, 1)[1]
                key_str += str(len(remaining_word)) + "<>" + str(remaining_word)
    return key_str


def generate_index(index_unsorted, block_size, index_flag):
    """
    A generic method to build all 4 types of indexes: compressed and uncompressed indexes using lemmatization and stemming
    :param index_unsorted:
    :param block_size:
    :param index_flag: 1:lemmatiztion; 2: stemming
    :return: index, index_compressed, key_str, max_df_list, min_df_list
    """
    index = OrderedDict(sorted(index_unsorted.items()))
    index_compressed = []
    key_str = ""
    i = -1
    front_coding_list = []
    max_cnt = 0
    min_cnt = 1
    max_df_list = []
    min_df_list = []

    # Generate uncompressed index
    for key in index:
        i += 1
        val = index[key]
        cnt = val.count('->') + 1  # df
        if cnt > max_cnt:
            max_cnt = cnt
        # Index is of the form {word:    df    posting_list(doc_id:tf:max_tf:doclen)
        index.update({key: str(cnt) + "\t" + val})

    elapsed_time_index_uncompressed = round(time.time() - start_time, 2)
    print("Elapsed time to build index version %s uncompressed: %s seconds" %
          (index_flag, elapsed_time_index_uncompressed))

    # Generate compressed index
    i = -1
    for key in index:
        i += 1
        val = index[key]
        cnt = val.count('->') + 1  # df

        if cnt == max_cnt:
            max_df_list.append(key + ":" + str(max_cnt))
        elif cnt == min_cnt:
            min_df_list.append(key + ":" + str(min_cnt))

        # Compress the dictionary term
        curr_ind = len(key_str)
        if index_flag == 1:
            # Use blocked compression to generated compressed key string
            key_str += str(len(key)) + str(key)
        elif index_flag == 2:
            # Use front coding to generate compressed key string
            if i % block_size == 0:
                if len(front_coding_list) > 0:
                    key_str = get_front_coding_key_str(front_coding_list, key_str)
                front_coding_list[:] = []
            front_coding_list.append(key)

        # Compress the postings list
        individual_posting = val.split('\t')[1].split('->')
        gap = 0
        val_str = ""
        for block_term_posting in individual_posting:
            block_terms = block_term_posting.split(':')
            if val_str == "":
                gap = block_terms[0]
            else:
                gap = int(block_terms[0]) - int(gap)

            if index_flag == 1:
                # Use gamma encoding to generate compressed postings list
                val_str += get_gamma_code(gap)
            elif index_flag == 2:
                # Use delta encoding to generate compressed postings list
                val_str += get_delta_code(gap)

        # Update the compressed index with a new entry
        if i % block_size == 0:
            # Compressed index is of the form {df:encoded_posting_list:string_index_of_key_str}
            index_compressed.append(str(cnt) + ":" + str(val_str) + ":" + str(curr_ind))
        else:
            # Compressed index is of the form {df:encoded_posting_list}
            index_compressed.append(str(cnt) + ":" + str(val_str))

    # Add the remaining terms of the last block to the front coded key string
    if index_flag == 2:
        if len(front_coding_list) > 0:
            key_str = get_front_coding_key_str(front_coding_list, key_str)

    elapsed_time_index_compressed = round(time.time() - start_time, 2)
    print("Elapsed time to build index version %s compressed: %s seconds" % (index_flag, elapsed_time_index_compressed))

    return index, index_compressed, key_str, max_df_list, min_df_list


# The program starts here
start_time = time.time()
directory = "/people/cs/s/sanda/cs6322/Cranfield/*"  # Change to point to the respective directory
#directory = "Cranfield/*"  # Change to point to the respective directory
collection = glob.glob(directory)

# Add stopwords from the given file containing the list of stopwords
stopwords = []
stopwords_file = open("/people/cs/s/sanda/cs6322/resourcesIR/stopwords", "r")
#stopwords_file = open("stopwords", "r") # Change to point to the respective stopwords file location
for word in stopwords_file:
    stopwords.append(word.strip("\n"))
stopwords_file.close()

index1_unsorted = {}
index2_unsorted = {}

doc_id_counter = 0
doc_max_tf = 0
max_doclen = 0
doc_max_tf_id = 0
max_doclen_id = 0

# Repeat for every file in the collection
for file in collection:
    root = et.parse(file)
    doc_id_counter += 1
    tokens = []
    doclen = 0

    # Repeat for all child DOM elements
    for values in root.findall('*'):
        sgml_values = values.text  # Get the value
        sgml_values = sgml_values.strip()  # Remove preceding and trailing spaces
        sgml_values = sgml_values.replace("\n", " ")  # Remove the end of line escape character
        sgml_values = re.sub(r'[^a-zA-Z0-9.\s]', ' ', sgml_values)  # Replace all non-alphanumeric characters with space
        sgml_values = re.sub(r'[^a-zA-Z0-9\s]', '', sgml_values)  # Remove all dots, e.g. U.S.A. becomes USA
        sgml_values = sgml_values.lower()  # Convert all letters to lowercase
        token_list = sgml_values.split()  # Split individual words on spaces
        doclen += len(token_list)
        for token in token_list:
            if token not in stopwords:
                tokens.append(token)  # Append every split word to the list of tokens

    # Perform lemmatization
    lemmatizer = WordNetLemmatizer()
    lemma_list = []
    for token in tokens:
        lemmatized_token = lemmatizer.lemmatize(token)
        lemma_list.append(lemmatized_token)

    # Create unsorted index 1
    index1_unsorted, curr_max_tf = get_unsorted_index(index1_unsorted, lemma_list, doc_id_counter, doclen)

    # Perform stemming
    stemmer = PorterStemmer()
    stem_list = []
    for token in tokens:
        stemmed_token = stemmer.stem(token, 0, len(token) - 1)
        stem_list.append(stemmed_token)

    # Create unsorted index 2
    index2_unsorted, curr_max_tf = get_unsorted_index(index2_unsorted, stem_list, doc_id_counter, doclen)

    # Get the document with maximum max_tf
    if curr_max_tf > doc_max_tf:
        doc_max_tf = curr_max_tf
        doc_max_tf_id = doc_id_counter

    # Get the document with maximum doclen
    if doclen > max_doclen:
        max_doclen = doclen
        max_doclen_id = doc_id_counter

# Generate uncompressed and compressed versions of index 1 using lemmatization and a block size of 4
index1, index1_compressed, key_str1, max_df1, min_df1 = generate_index(index1_unsorted, 4, 1)

# Generate uncompressed and compressed versions of index 2 using stemming and a block size of 8
index2, index2_compressed, key_str2, max_df2, min_df2 = generate_index(index2_unsorted, 8, 2)

# Write all 4 generated indexes to different files

index1_op = open('Index_Version1.uncompress.txt', 'w')
for entry in index1:
    index1_op.writelines(entry + "\t" + index1[entry] + "\n")
index1_op.close()

index1_comp_op = open('Index_Version1.compressed.txt', 'w')
index1_comp_op.write(key_str1 + "\n")
for entry in index1_compressed:
    index1_comp_op.write(entry + "\n")
index1_comp_op.close()

index2_op = open('Index_Version2.uncompress.txt', 'w')
for entry in index2:
    index2_op.writelines(entry + "\t" + index2[entry] + "\n")
index2_op.close()

index2_comp_op = open('Index_Version2.compressed.txt', 'w')
index2_comp_op.write(key_str2 + "\n")
for entry in index2_compressed:
    index2_comp_op.write(entry + "\n")
index2_comp_op.close()

# Generate some statistics for the generated indexes

print("Size of index version 1 uncompressed: ", sys.getsizeof(index1), "bytes")
print("Size of index version 1 compressed: ", sys.getsizeof(index1_compressed), "bytes")
print("Size of index version 2 uncompressed: ", sys.getsizeof(index2), "bytes")
print("Size of index version 2 compressed: ", sys.getsizeof(index2_compressed), "bytes")

print("Number of postings in index version 1 uncompressed: ", len(index1))
print("Number of postings in index version 1 compressed: ", len(index1_compressed))
print("Number of postings in index version 2 uncompressed: ", len(index2))
print("Number of postings in index version 1 compressed: ", len(index2_compressed))

query_list = ["reynolds", "prandtl", "flow", "pressure", "boundary", "shock", "nasa"]
for query_term in query_list:
    index_val = index1[query_term]
    tab_separated = index_val.split("\t")
    df = tab_separated[0]
    tf = []
    arrow_separated = tab_separated[1].split("->")
    for single_posting in arrow_separated:
        curr_tf = single_posting.split(":")[0] + ":" + single_posting.split(":")[1]
        tf.append(curr_tf)
    inverted_list_length = sys.getsizeof(tab_separated[1])
    print("For %s\n df = %s\n tf(docID:tf) = %s \n inverted list length = %s bytes" % (
    query_term, df, tf, inverted_list_length))

    if query_term == "nasa":
        print("NASA: \n df = ", df)
        i = 0
        while i < 3:
            current_posting_entry = arrow_separated[i]
            posting_entries = current_posting_entry.split(":")
            print("For entry %s in posting list \n tf = %s \n doclen = %s \n max_tf = %s"
                  % (i + 1, posting_entries[1], posting_entries[3], posting_entries[2]))
            i += 1

print("Dictionary term from index 1 with the largest df:value\n", max_df1)
print("Dictionary term from index 1 with the lowest df:value\n", min_df1)
print("Dictionary term from index 2 with the largest df:value\n", max_df2)
print("Dictionary term from index 2 with the lowest df:value\n", min_df2)
print("Document with the largest max_tf in collection: Doc #%s with a max_tf of %s" % (doc_max_tf_id, doc_max_tf))
print("Document with the largest doclen in the collection: Doc #%s with a doclen of %s" % (max_doclen_id, max_doclen))
