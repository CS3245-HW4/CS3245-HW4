import nltk
import sys
import getopt
import json
import time
import math
import string
from information_need import InformationNeed

show_time = False
LANG = "english"

k = 10  # number of results to return


def docIDs_decreasing_score(doc_scores):
    """Returns the list of docIDs, sorted by descending document scores. The
    docIDs are also converted to strings here.

    :param doc_scores: A dictionary of docID to its corresponding document's
    score.
    :return: List of str(docIDs) sorted by descending document scores.
    """
    sorted_scores = sorted(doc_scores.iteritems(),
                           key=lambda score_entry: score_entry[1],
                           reverse=True)
    return [str(docID) for docID, score in sorted_scores]


def expand_query(sorted_docIDs, doc_scores, docs_metadata):
    """Expands the query by retrieving the IPC classes of high-scoring
    documents, then adds all documents under the same IPC class to the result.

    :param sorted_docIDs: The list of all document IDs with nonzero tf-idf
    score against the query, sorted in descending score.
    :param doc_scores: Dictionary mapping from document ID to tf-idf score.
    :param docs_metadata: Dictionary of document metadata, including IPC classes
    """
    top_20_docIDs = sorted_docIDs[:20]
    top_20_IPCs = set([docs_metadata[docID][2] for docID in top_20_docIDs])
    docs_in_IPCs = [docID for docID, doc_metadata in docs_metadata.iteritems()
                    if doc_metadata[2] in top_20_IPCs]
    docs_IPCs_scores = [(docID, doc_scores[docID])
                        if docID in doc_scores
                        else (docID, float(0)) for docID in docs_in_IPCs]
    sorted_docs_IPCs_scores = sorted(docs_IPCs_scores,
                                     key=lambda score_entry: score_entry[1],
                                     reverse=True)
    sorted_docs = [docID for docID, doc_score in sorted_docs_IPCs_scores]
    return sorted_docs


def process_queries(dictionary_file, postings_file, query_file, output_file):
    # load dictionary
    begin = time.time() * 1000.0
    with open(dictionary_file) as dict_file:
        temp = json.load(dict_file)
        docs_metadata = temp[0]
        dictionary = temp[1]

    # open queries
    postings = file(postings_file)
    output = file(output_file, 'w')

    q = InformationNeed(query_file).get_data()
    # From here onwards, operations are split between title and description,
    # where we match the description to patent abstracts.
    query_title = q["title"]
    query_description = q["description"]

    title_terms = normalize(query_title)
    description_terms = normalize(query_description)

    single_term_title = len(title_terms) == 1
    single_term_description = len(description_terms) == 1
    
    title_scores = {}
    for term in title_terms:
        title_scores = update_relevance(title_scores, dictionary, postings,
                                        title_terms, term, single_term_title,
                                        "Title")
    for docID in title_scores:
        # [0] is title_length, [1] abstract_length, [2] is IPC
        title_scores[docID] /= docs_metadata[str(docID)][0]

    description_scores = {}
    for term in description_terms:
        description_scores = update_relevance(description_scores, dictionary,
                                              postings, description_terms,
                                              term, single_term_description,
                                              "Abstract")
    for docID in description_scores:
        # [0] is title_length, [1] abstract_length, [2] is IPC
        description_scores[docID] /= docs_metadata[str(docID)][1]
    doc_scores = {}
    for docID in docs_metadata:
        doc_scores[docID] = (title_scores.get(docID, 0) * 0.05) \
                            + (description_scores.get(docID, 0) * 0.95)
    
    results = docIDs_decreasing_score(doc_scores)
    expanded_results = expand_query(results, doc_scores, docs_metadata)

    # Remove .xml file extension
    output.write(" ".join([docID[:-4] for docID in expanded_results]))
    output.write("\n")

    postings.close()
    output.close()
    after = time.time() * 1000.0
    if show_time: print after-begin


def normalize(query):
    """ Tokenize and stem query, also removes punctuations and stopwords.

    :param query: Query to tokenize and stem.
    :return: List of normalized query tokens.
    """
    query_tokens = nltk.word_tokenize(query)
    punctuation_removed = [word for word in query_tokens
                           if word not in string.punctuation]
    stopwords_removed = [token.lower() for token in punctuation_removed
                         if token.lower()
                         not in set(nltk.corpus.stopwords.words(LANG))]
    stemmer = nltk.stem.PorterStemmer()
    query_terms = map(lambda word : stemmer.stem(word), stopwords_removed)
    return query_terms


def update_relevance(doc_scores, dictionary, postings_file, query_terms,
                     term, single_term_query, field):

    postings = read_postings(term, dictionary, postings_file, field)
    
    for docID_and_tf in postings:
        docID, tf_in_doc = docID_and_tf
        tf_in_query = query_terms.count(term)
        term_idf = dictionary[field][term][2]

        weight_of_term_in_doc = tf_in_doc
        weight_of_term_in_query = 1 \
            if single_term_query \
            else (1 + math.log10(tf_in_query)) * term_idf

        if docID not in doc_scores:
            doc_scores[docID] = 0

        doc_scores[docID] += weight_of_term_in_doc \
            if single_term_query \
            else weight_of_term_in_doc * weight_of_term_in_query

    return doc_scores


def read_postings(term, dictionary, postings_file, field):
        """ Gets own postings list from file and stores it in its attribute.
        For search token nodes only.

        :param term: Term to search
        :param postings_file: File object referencing the file containing the
        complete set of postings lists.
        :param dictionary: Dictionary that takes search token keys, and
        returns a tuple of pointer and length. The pointer points to the
        starting point of the search token's postings list in the file. The
        length refers to the length of the search token's postings list in
        bytes.
        :param field: The type of field parameter
        """

        if term in dictionary[field]:
            term_pointer = dictionary[field][term][0]
            postings_length = dictionary[field][term][1]
            postings_file.seek(term_pointer)
            postings = postings_file.read(postings_length).split()
            postings = map(lambda docID_and_tf :
                           docID_and_tf.split(","), postings)
            postings = map(lambda docID_and_tf :
                           [docID_and_tf[0], float(docID_and_tf[1])], postings)
            return postings
        else:
            return []


def main():
    # Get inputs
    dictionary_file, postings_file, query_file, output_file = load_args()
    # Runs search function
    process_queries(dictionary_file, postings_file, query_file, output_file)


def load_args():
    """Attempts to parse command line arguments fed into the script when it was
    called. Notifies the user of the correct format if parsing failed.
    """
    dictionary_file = postings_file = query_file = output_file = None

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
    except getopt.GetoptError, err:
        usage()
        sys.exit(2)
    for o, a in opts:
        if o == '-d':
            dictionary_file = a
        elif o == '-p':
            postings_file = a
        elif o == '-q':
            query_file = a
        elif o == '-o':
            output_file = a
        else:
            assert False, "unhandled option"
    if dictionary_file is None or postings_file is None \
            or query_file is None or output_file is None:
        usage()
        sys.exit(2)
    return dictionary_file, postings_file, query_file, output_file


def usage():
    """Prints the proper format for calling this script."""
    print "usage: " + sys.argv[0] + " -d dictionary-file " \
                                    "-p postings-file " \
                                    "-q file-of-queries " \
                                    "-o output-file-of-results"


if __name__ == "__main__":
    main()