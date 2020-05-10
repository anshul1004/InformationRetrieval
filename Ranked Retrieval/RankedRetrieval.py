"""
Author: Anshul Pardhi
The program performs a ranked retrieval model on a given set of queries,
tested on the Cranfield document collection
"""

import glob
import re
import math
import xml.etree.ElementTree as et
from collections import Counter
from nltk.stem import WordNetLemmatizer
from collections import OrderedDict


def tokenize(values):
    """
    Generate tokens by pre-processing raw data
    :param values:
    :return: list of tokens
    """
    sgml_values = values.strip()  # Remove preceding and trailing spaces
    sgml_values = sgml_values.replace("\n", " ")  # Remove the end of line escape character
    sgml_values = re.sub(r'[^a-zA-Z0-9.\s]', ' ', sgml_values)  # Replace all non-alphanumeric characters with space
    sgml_values = re.sub(r'[^a-zA-Z0-9\s]', '', sgml_values)  # Remove all dots, e.g. U.S.A. becomes USA
    sgml_values = sgml_values.lower()  # Convert all letters to lowercase
    return sgml_values.split()  # Split individual words on spaces and return


def get_unsorted_index(index_unsorted, word_list, doc_id_counter, doclen):
    """
    Update the unsorted index posting list
    :param index_unsorted:
    :param word_list:
    :param doc_id_counter:
    :param doclen:
    :return: index_unsorted
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
    return index_unsorted


def generate_index(index_unsorted):
    """
    Generate sorted index, adding a document frequency as well
    :param index_unsorted:
    :return: index
    """
    index = OrderedDict(sorted(index_unsorted.items()))

    # Generate uncompressed index
    for key in index:
        val = index[key]
        cnt = val.count('->') + 1  # df
        # Index is of the form {word:    df    posting_list(doc_id:tf:max_tf:doclen)
        index.update({key: str(cnt) + "\t" + val})

    return index


def get_w1_weight(tf, max_tf, collection_size, df):
    """
    Computes weights on the basis of max-tf term weighting
    :param tf:
    :param max_tf:
    :param collection_size:
    :param df:
    :return: w1_weight
    """
    return (0.4 + 0.6 * math.log10(float(tf) + 0.5) / math.log10(float(max_tf) + 1.0)) * \
           (math.log10(float(collection_size) / float(df)) / math.log10(float(collection_size)))


def get_w2_weight(tf, doclen, avg_doclen, collection_size, df):
    """
    Computes weights on the basis of Okapi term weighting
    :param tf:
    :param doclen:
    :param avg_doclen:
    :param collection_size:
    :param df:
    :return: w2_weight
    """
    return (0.4 + 0.6 * (float(tf) / (float(tf) + 0.5 + 1.5 * (float(doclen) / float(avg_doclen))))) * \
           (math.log10(float(collection_size) / float(df)) / math.log10(float(collection_size)))


def normalize_weights(curr_map):
    """
    Normalize the weights generated by the weighting scheme
    :param curr_map:
    :return: normalized weight map
    """
    new_map = {}
    for key in curr_map:
        values = curr_map[key].split()
        sq_sum = 0

        # Sum all the squares of weights belonging to a particular document
        for value in values:
            colon_split = value.split(":")
            sq_sum += float(colon_split[1]) * float(colon_split[1])

        sqrt_sq_sum = math.sqrt(sq_sum)

        # Normalize the weight and store in the dictionary
        for value in values:
            colon_split = value.split(":")
            normalized_weight_value = round(float(colon_split[1]) / sqrt_sq_sum, 3)
            if new_map.get(key) is None:
                new_map.update(
                    {key: str(colon_split[0]) + ":" + str(normalized_weight_value)})
            else:
                new_map.update(
                    {key: str(new_map.get(key)) + " " + str(colon_split[0]) + ":" + str(normalized_weight_value)})
    return new_map


def generate_weight_vector_map(index, collection_size, avg_doclen):
    """
    Generates weight vector map from the given index
    :param index:
    :param collection_size:
    :param avg_doclen:
    :return: weight vector map
    """
    curr_map_1 = {}  # Map based on W1 weighting scheme
    curr_map_2 = {}  # Map based on W2 weighting scheme

    for key in index:
        val = index[key]
        tab_sep = val.split("\t")
        df = tab_sep[0]
        postings_list = tab_sep[1].split("->")

        for posting in postings_list:
            posting_sep = posting.split(":")
            doc_id = posting_sep[0]
            tf = posting_sep[1]
            max_tf = posting_sep[2]
            doclen = posting_sep[3]

            w1_weight = get_w1_weight(tf, max_tf, collection_size, df)
            w2_weight = get_w2_weight(tf, doclen, avg_doclen, collection_size, df)

            # Maps will be of the form doc_id lemma1:weight1 lemma2:weight2 and so on
            if curr_map_1.get(doc_id) is None:
                curr_map_1.update(
                    {doc_id: str(key) + ":" + str(w1_weight)})
            else:
                curr_map_1.update(
                    {doc_id: str(curr_map_1.get(doc_id)) + " " + str(key) + ":" + str(w1_weight)})

            if curr_map_2.get(doc_id) is None:
                curr_map_2.update(
                    {doc_id: str(key) + ":" + str(w2_weight)})
            else:
                curr_map_2.update(
                    {doc_id: str(curr_map_2.get(doc_id)) + " " + str(key) + ":" + str(w2_weight)})

    # Normalize the weights for both the maps
    curr_map_1 = normalize_weights(curr_map_1)
    curr_map_2 = normalize_weights(curr_map_2)

    # Sort the map on the basis of doc_id
    return OrderedDict(sorted(curr_map_1.items(), key=lambda x: int(x[0]))), \
           OrderedDict(sorted(curr_map_2.items(), key=lambda x: int(x[0])))


def print_vector_representation(weight_vector_map):
    """
    Generic method to print the weight vector representation
    :param weight_vector_map:
    :return:
    """
    for key in weight_vector_map:
        print(key, weight_vector_map[key])


def get_top5_documents(query_weight_vector, document_weight_vector):
    """
    This method calculates the 5 most relevant documents for a given query and prints the results
    :param query_weight_vector:
    :param document_weight_vector:
    :return:
    """

    # Do this for each query
    for key_q in query_weight_vector:
        query_map = {}  # Query map is of the form lemma: weight_value
        query_val = query_weight_vector[key_q].split()
        for word in query_val:
            word_val = word.split(":")
            query_map.update({word_val[0]: word_val[1]})

        cos_prod_map = {}  # This map stores cosine products of a given query with all documents in collection

        # Do this for all documents in the collection
        for key_d in document_weight_vector:
            document_map = {}  # Document map is of the form lemma: weight_value
            document_val = document_weight_vector[key_d].split()
            for word in document_val:
                document_val = word.split(":")
                document_map.update({document_val[0]: document_val[1]})

            # Compute cosine product for a particular query and document
            cos_prod = 0
            for term in document_map:
                if term in query_map:
                    cos_prod += round(float(document_map[term]) * float(query_map[term]), 3)

            # This map is of the form cos_prod: document weight vector representation
            cos_prod_map.update({cos_prod: str(key_d) + " " + str(document_weight_vector[key_d])})

        # Sort the cos_prod map to get the most relevant queries (top-5)
        cos_prod_map = OrderedDict(sorted(cos_prod_map.items(), reverse=True))

        print("For query ", key_q)
        i = 1
        for key in cos_prod_map:
            if i > 5:
                break
            doc_identifier = cos_prod_map[key].split()[0]
            print("Rank:", i, " Score:", key, " Document Identifier:", doc_identifier)
            print("Headline: ", title_map.get(int(doc_identifier)))
            print("Vector Representation: ")
            print(cos_prod_map[key])
            print()
            i += 1
        print()


# The program starts here
directory = "/people/cs/s/sanda/cs6322/Cranfield/*"  # Change to point to the respective directory
#directory = "Cranfield/*"  # Change to point to the respective directory
collection = glob.glob(directory)

# Add stopwords from the given file containing the list of stopwords
stopwords = []
stopwords_file = open("/people/cs/s/sanda/cs6322/resourcesIR/stopwords", "r")
#stopwords_file = open("stopwords", "r")  # Change to point to the respective stopwords file location
for word in stopwords_file:
    stopwords.append(word.strip("\n").strip())
stopwords_file.close()

index_unsorted = {}
doc_id_counter = 0
total_doclen = 0
title_map = {}

# Repeat for every file in the collection
for file in collection:
    root = et.parse(file)
    doc_id_counter += 1
    tokens = []
    doclen = 0

    # Repeat for all child DOM elements
    for values in root.findall('*'):
        token_list = tokenize(values.text)
        for token in token_list:
            if token not in stopwords:
                tokens.append(token)  # Append every split word to the list of tokens
        doclen += len(tokens)

    # Add title of every document to title_map, which will later become headline for the top-5 relevant queries
    for values in root.findall("TITLE"):
        title_map.update({doc_id_counter: values.text.replace("\n", " ")})

    total_doclen += doclen

    # Perform lemmatization
    lemmatizer = WordNetLemmatizer()
    lemma_list = []
    for token in tokens:
        lemmatized_token = lemmatizer.lemmatize(token)
        lemma_list.append(lemmatized_token)

    index_unsorted = get_unsorted_index(index_unsorted, lemma_list, doc_id_counter, doclen)

collection_size = doc_id_counter
avg_doclen = total_doclen // collection_size

index = generate_index(index_unsorted)  # Generate document index

document_weight_vector_1, document_weight_vector_2 = generate_weight_vector_map(index, collection_size, avg_doclen)

queries = []
queries_file = open("/people/cs/s/sanda/cs6322/hw3.queries", "r")
#queries_file = open("hw3.queries", "r")  # Change to point to the respective queries file location

# Parse the queries file to get the queries
query_lines = queries_file.readlines()
for i in range(len(query_lines)):
    if query_lines[i].startswith("Q"):
        i += 1
        curr_query = ""
        while i < len(query_lines) and query_lines[i] != "\n":
            curr_query += query_lines[i]
            curr_query += " "
            i += 1
        curr_query = curr_query.replace("\n", "").strip()
        queries.append(curr_query)
        i += 1
queries_file.close()
query_index = {}
query_id_counter = 0
total_query_len = 0

# Perform tokenization, lemmatization and remove stop words to generate relevant terms for each query
for query in queries:
    query_id_counter += 1
    curr_query_list = []
    query_tokens = tokenize(query)

    for query_token in query_tokens:
        if query_token not in stopwords:
            curr_query_list.append(lemmatizer.lemmatize(query_token))

    query_len = len(curr_query_list)
    total_query_len += query_len
    query_index = get_unsorted_index(query_index, curr_query_list, query_id_counter, query_len)

query_collection_size = len(queries)
avg_query_doclen = total_query_len // query_collection_size

query_index = generate_index(query_index)  # Generate query index similar to document index
query_weight_vector_1, query_weight_vector_2 = generate_weight_vector_map(query_index, query_collection_size,
                                                                          avg_query_doclen)

print("Query vector representation for Weighting Scheme 1:")
print_vector_representation(query_weight_vector_1)
print()
print("Query vector representation for Weighting Scheme 2:")
print_vector_representation(query_weight_vector_2)
print()
print("Top 5 Documents Using Weighting Scheme 1:")
get_top5_documents(query_weight_vector_1, document_weight_vector_1)
print()
print("Top 5 Documents Using Weighting Scheme 2:")
get_top5_documents(query_weight_vector_2, document_weight_vector_2)