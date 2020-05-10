1. Install Python version 2.7.5
2. Place both IndexBuilding.py and porter_stemmer_tartarus.py in the same directory
3. Go to the directory where you placed IndexBuilding.py and porter_stemmer_tartarus.py
4. To install NLTK, run the command 
	pip install nltk==3.0 --user
5. Type python to open the Python console
    python
6. Python console opens up. Type the following command
    >>>import nltk
	>>>nltk.download('wordnet')
	>>>exit()
7. Make sure you are in the same directory as IndexBuilding.py and porter_stemmer_tartarus.py
8. Run the program
    python IndexBuilding.py
9. The program statistics show up on the console (they are also given in the Program Description file)
10. 4 new files get generated in the same directory
     Index_Version1.uncompress.txt
	 Index_Version1.compressed.txt
	 Index_Version2.uncompress.txt
	 Index_Version2.compressed.txt
	 These generated files contain the 4 required indexes
11. Use cat Index_Version1.uncompress.txt to view contents of the file (the generated index) on the console, or use any appropriate editor of your choice (vim, gedit, emacs etc.) to view the contents of the file (the generated index). A copy of the generated files is also provided in the solution zip file uploaded on e-learning.

The default directory for Cranfield collection given in the code is "/people/cs/s/sanda/cs6322/Cranfield/*".
If you want to change it, please update your desired path as required on lines 214 of IndexBuilding.py

The default file for stopwords is located at "/people/cs/s/sanda/cs6322/resourcesIR/stopwords"
If you want to change it, please update your desired path as required on lines 220 of IndexBuilding.py

In case NLTK fails to get installed on the system (which is highly unlikely), try to run the code on your local machine, using appropriate file path changes for Cranfield directory and stopwords by making changes on the line numbers mentioned above.