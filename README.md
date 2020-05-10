# InformationRetrieval
The project is divided into three parts:
1. Tokenization & Stemming
2. Indexing
3. Ranked Retrieval

Cranfield text document collection is used. It contains 1400 documents.

# Tokenization & Stemming
As part of preprocessing, the documents are first parsed to extract the relevant text. The documents are later tokenized and then stemmed using the open source implementation of Porter Stemmer.

# Indexing
The documents are stemmed using Porter Stemmer and lemmatized using NLTK's WordNetLemmatizer. Two different types of indexes are created: one using stemming and another using lemmatization. The indexes are also compressed using blocked compression and front coding.

# Ranked Retrieval
The indexed documents are then created into document vectors using two different weighting schemes: max tf term weighting and okapi term weighting. The ranked documents are then tested on a list of queries to test the relevancy of the model.
