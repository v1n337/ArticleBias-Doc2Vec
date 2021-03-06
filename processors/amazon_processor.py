from processors.processor import Processor
from utils import log_helper, file_helper, doc2vec_helper, scikit_ml_helper

log = log_helper.get_logger("AmazonProcessor")


class AmazonProcessor(Processor):

    def __init__(self, labeled_articles_source_file_path, doc2vec_model_file_path, ml_model_file_path,
                 articles_source_file_path):
        self.labeled_articles_file_path = labeled_articles_source_file_path
        self.articles_source_file_path = articles_source_file_path
        self.doc2vec_model_file_path = doc2vec_model_file_path
        self.ml_model_file_path = ml_model_file_path
        self.shuffle_count = 5

    def process(self):

        log.info("Commencing execution")

        # Get tagged articles from Veriday
        log.info("Getting tagged Veriday articles ... ")
        veriday_articles_raw = file_helper.get_articles_list(self.articles_source_file_path)
        veriday_tagged_articles = doc2vec_helper.get_tagged_articles_veriday(veriday_articles_raw)

        log.info("Getting tagged Amazon reviews ... ")
        tagged_articles, sentiment_scores_dict = \
            doc2vec_helper.get_tagged_amazon_reviews(self.labeled_articles_file_path)

        # combine both article sets
        tagged_articles.extend(veriday_tagged_articles)

        # model initialization and vocab building
        log.info("Initializing the doc2vec model ...")
        doc2vec_model = doc2vec_helper.init_model(tagged_articles)

        # shuffling and training the model
        log.info("Training the doc2vec model ...")
        for i in range(self.shuffle_count):
            log.info("Shuffles remaining: " + str(self.shuffle_count - i))
            doc2vec_helper.shuffle_and_train_articles(doc2vec_model, tagged_articles)

        # saving the doc2vec model to disk
        doc2vec_model.save(self.doc2vec_model_file_path)

        # Extracting parameters for and training the ML model
        x_docvecs, y_scores = scikit_ml_helper.extract_training_parameters(doc2vec_model, sentiment_scores_dict)
        log.info("Training the ML model ...")
        ml_model = scikit_ml_helper.train_linear_model(x_docvecs, y_scores)

        # saving the ml model to disk
        scikit_ml_helper.persist_model_to_disk(ml_model, self.ml_model_file_path)

        log.info("Completed execution")
