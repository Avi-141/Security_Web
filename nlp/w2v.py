import gzip
import gensim
import logging



logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', 
                    level=logging.INFO)


def show_file_contents(input_file):
    with gzip.open(input_file, 'rb') as f:
        for i, line in enumerate(f):
            print(line)
            break


def read_input(input_file):
    """This method reads the input file which is in gzip format"""

    logging.info("reading file {0}...this may take a while".format(input_file))

    with gzip.open(input_file, 'rb') as f:
        for i, line in enumerate(f):
            if (i % 10000 == 0):
                logging.info("read {0} reviews".format(i))

            # do some pre-processing and return list of words for each review text

            yield gensim.utils.simple_preprocess(line)






if __name__ == '__main__':

    
    input_file = 'dataset.gz'

    # read first line of the dataset
    # show_file_contents(input_file)

    # documents is a list of lists
    documents = list(read_input(input_file))
    logging.info("Done reading dataset")

    # build vocabulary and train model
    model = gensim.models.Word2Vec(
            documents,
            size=150,
            window=10,
            min_count=2,
            workers=10)

    model.train(documents, total_examples=len(documents), epochs=10)

    w1 = "hello"
    model.wv.most_similar (positive=w1)