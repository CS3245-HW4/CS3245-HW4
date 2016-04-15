import nltk
import sys
import getopt
import json
import heapq
import time
import math
import string
from itertools import groupby, chain, islice
from information_need import InformationNeed

show_time = False
LANG = "english"

k = 10  # number of results to return

def sort_relevant_docs(most_relevant_docs):
    """Given a list of tuples of documents in the format of (score, docID),
    sort them primarily by decreasing score, and tiebreak by increasing docID,
    and then return up to the first k elements in the list.

    :param most_relevant_docs: A list of tuples of documents and their scores,
    where each tuple contains (score, docID).
    """
    grouped_relevant = groupby(most_relevant_docs,
                               key=lambda score_doc_entry: score_doc_entry[0])
    sorted_relevant = [sorted(equal_score_entries[1],
                              key=lambda equal_score_entry:
                              equal_score_entry[1])
                       for equal_score_entries in grouped_relevant]
    flattened_relevant = chain.from_iterable(sorted_relevant)
    # Takes first k elements from the iterable. If there are less than k
    # elements, it stops when the iterable stops
    trimmed_relevant = islice(flattened_relevant, len(most_relevant_docs))
    # Finally, extract the docID from the tuple and convert it to a string to
    # be written to output
    relevant_docIDs = [str(docID) for score, docID in trimmed_relevant]
    return list(relevant_docIDs)


def first_k_most_relevant(doc_scores):
    """If there are more than k documents containing terms in a query, return
    the k documents with the highest scores, tiebroken by least docID first.
    If there are less than k documents, return them, sorted by highest scores,
    and tiebroken by least docID first.

    Heapify an array, O(n) + O(k lg n)

    :param doc_scores: A dictionary of docID to its corresponding document's
    score.
    """

    # invert the scores so that heappop gives us the smallest score
    scores = [(-score, docID) for docID, score in doc_scores.iteritems()]
    heapq.heapify(scores)
    most_relevant_docs = []
    for _ in range(len(scores)):
        if not scores:
            break
        most_relevant_docs.append(heapq.heappop(scores))
    if not most_relevant_docs:
        return most_relevant_docs
    # deals with equal-score cases
    kth_score, kth_docID = most_relevant_docs[-1]
    while scores:
        next_score, next_docID = heapq.heappop(scores)
        if next_score == kth_score:
            most_relevant_docs.append((next_score, next_docID))
        else:
            break
    return sort_relevant_docs(most_relevant_docs)

def docIDs_decreasing_score(doc_scores):
    """Returns the list of docIDs, sorted by descending document scores. The
    docIDs are also converted to strings here.

    :param doc_scores: A dictionary of docID to its corresponding document's
    score.
    """
    sorted_scores = sorted(doc_scores.iteritems(),
                           key=lambda score_entry: score_entry[1],
                           reverse=True)
    return [str(docID) for docID, score in sorted_scores]

def expand_query(sorted_docIDs, doc_scores, docs_metadata):
    top_20_docIDs = sorted_docIDs[:20]
    top_20_IPCs = set([docs_metadata[docID][1] for docID in top_20_docIDs])
    docs_in_IPCs = [docID for docID, doc_metadata in docs_metadata.iteritems() if doc_metadata[1] in top_20_IPCs]
    #print(len(docs_metadata))
    #print(len(top_20_IPCs))
    #print(len(docs_in_IPCs))
    docs_IPCs_scores = [(docID, doc_scores[docID]) if docID in doc_scores else (docID, float(0)) for docID in docs_in_IPCs]
    #print(docs_IPCs_scores[1])
    sorted_docs_IPCs_scores = sorted(docs_IPCs_scores, key=lambda score_entry: score_entry[1], reverse=True)
    sorted_docs = [docID for docID, doc_score in sorted_docs_IPCs_scores]
    
    #for docID in docs_in_IPCs:
    #    docs_IPCs_scores[docID] = doc_scores[docID] if docID in doc_scores else 0
    #converted_results = [docID for docID in sorted_nonzero_score_docIDs if docs_metadata[docID][1] in top_20_IPCs]
    #zero_score_results = [docID for docID in sorted_docIDs if docs_metadata[docID[1] in top_20_IPCs]
    return sorted_docs

def usage():
    """Prints the proper format for calling this script."""
    print "usage: " + sys.argv[0] + " -d dictionary-file " \
                                    "-p postings-file " \
                                    "-q file-of-queries " \
                                    "-o output-file-of-results"


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
    query = " ".join([q["title"], q["description"]])

    query_terms = normalize(query)
    single_term_query = len(query_terms) == 1
    doc_scores = {}

    for term in query_terms:
        doc_scores = update_relevance(doc_scores, dictionary, postings,
                                      query_terms, term, single_term_query)

    for docID in doc_scores:
        # [0] is length, [1] is IPC
        doc_scores[docID] /= docs_metadata[str(docID)][0]

    # It's OK to get all results, it's really fast anyway.
    #results = first_k_most_relevant(doc_scores)
    results = docIDs_decreasing_score(doc_scores)
    expanded_results = expand_query(results, doc_scores, docs_metadata)

    #def expand_query(sorted_docIDs, doc_scores, docs_metadata):
    # Remove .xml file extension
    output.write(" ".join([docID[:-4] for docID in expanded_results]))
    output.write("\n")

    postings.close()
    output.close()
    after = time.time() * 1000.0
    if show_time: print after-begin


"""
Dictionary
    - Position index
    - Length of postings list in characters
    - Pre-calculated idf

Postings
    - Doc ID
    - Pre-calculated log frequency weight
"""


def normalize(query):
    """ Tokenize and stem

    :param query:
    :return:
    """
    # punctuation_removed = string.translate(str(query), None,
    #                                       string.punctuation)
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
                     term, single_term_query):

    postings = read_postings(term, dictionary, postings_file)
    
    for docID_and_tf in postings:

        docID, tf_in_doc = docID_and_tf
        tf_in_query = query_terms.count(term)
        term_idf = dictionary[term][2]

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


def read_postings(term, dictionary, postings_file):
        """ Gets own postings list from file and stores it in its attribute.
        For search token nodes only.

        :param term:
        :param postings_file: File object referencing the file containing the
        complete set of postings lists.
        :param dictionary: Dictionary that takes search token keys, and
        returns a tuple of pointer and length. The pointer points to the
        starting point of the search token's postings list in the file. The
        length refers to the length of the search token's postings list in
        bytes.
        """

        if term in dictionary:
            term_pointer = dictionary[term][0]
            postings_length = dictionary[term][1]
            postings_file.seek(term_pointer)
            postings = postings_file.read(postings_length).split()
            postings = map(lambda docID_and_tf :
                           docID_and_tf.split(","), postings)
            postings = map(lambda docID_and_tf :
                           [docID_and_tf[0], float(docID_and_tf[1])],postings)
            return postings
        else:
            return []


def main():
    dictionary_file, postings_file, query_file, output_file = load_args()

    process_queries(dictionary_file, postings_file, query_file, output_file)


if __name__ == "__main__":
    main()