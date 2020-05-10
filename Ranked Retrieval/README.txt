1. Install Python version 3.6.5
2. Place RankedRetrieval.py in appropriate directory where you want to run the program
3. To install NLTK, run the command 
	pip3 install nltk==3.0 --user
4. Type python3 to open the Python 3 console
    python3
5. Python console opens up. Type the following command
    >>>import nltk
	>>>nltk.download('wordnet')
	>>>exit()
6. In case import nltk causes issues, follow the solution given on https://stackoverflow.com/questions/32930545/attributeerror-cant-set-attribute-from-nltk-book-import
   i.e., open internals.py by typing command vim <path of internals.py>
   vim editor with the code of internals.py opens up
   press i to enter edit mode
   find line parsed_pattern.pattern.groups = 1. It should be there around line 75
   remove that line from the file
   to save the file, type :wq and press Enter
   Now again try to follow Step 5.
7. Run the program
    python3 RankedRetrieval.py
8. The results show up on the console.

The default directory for Cranfield collection given in the code is "/people/cs/s/sanda/cs6322/Cranfield/*".
If you want to change it, please update your desired path as required on lines 244 of RankedRetrieval.py

The default file for stopwords is located at "/people/cs/s/sanda/cs6322/resourcesIR/stopwords"
If you want to change it, please update your desired path as required on lines 250 of RankedRetrieval.py

The default file for queries is located at "/people/cs/s/sanda/cs6322/hw3.queries"
If you want to change it, please update your desired path as required on lines 299 of RankedRetrieval.py

In case NLTK fails to get installed on the system, try to run the code on your local machine, using appropriate file path changes for Cranfield directory, stopwords and queries file by making changes on the line numbers mentioned above.