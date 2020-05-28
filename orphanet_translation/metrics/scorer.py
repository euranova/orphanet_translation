"""Scorer module."""
import logging
import os

import numpy as np
import textdistance
from tqdm import tqdm


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

TEXTDISTANCE_FUNCTIONS = \
    [
     'jaro_wrinkler', 'jaro', 'strcmp95', 'needleman_wunsch', 'gotoh',
     'smith_waterman', 'jaccard', 'sorensen', 'sorensen_dice',
     'tversky', 'overlap', 'tanimoto', 'cosine', 'monge_elkan',
     'ratcliff_obershelp', 'identity'
    ]


class Scorer():
    """Scorer class to score the quality of the translations."""

    def __init__(self, scoring_functions=['jaro']):
        """Initialize Scorer.

        Args:
            scoring_functions (list of string, optional): the metrics used,
                have to be a similaryty in textdistance. Defaults to 'jaro'.
                Values in : ['jaro_wrinkler', 'jaro', 'strcmp95',
                'needleman_wunsch', 'gotoh', 'smith_waterman', 'jaccard',
                'sorensen', 'sorensen_dice', 'tversky', 'overlap', 'tanimoto',
                'cosine', 'monge_elkan', 'ratcliff_obershelp']

        """
        if not all([metric in TEXTDISTANCE_FUNCTIONS
                    for metric in scoring_functions]):
            error_msg = 'Unknown scoring function, look at the '\
                        + 'doc to see the availables functions name.'
            logger.error(error_msg)
            raise ValueError(error_msg)

        self.scoring_functions = scoring_functions

    @staticmethod
    def _scoring_label(row, lang, scoring_function):
        """Compare the two labels columns only.

        This function compares the labels and does not look
        at the alt column. Built to be used in an apply on a
        pd.DataFrame.

        Args:
            row (pd.Serie): the row the function will look at.
            lang (str): the two letters name of the language.
            scoring_function (func): a function which compute
                similarity between two strings.

        Returns:
            float: the maximum of the similarity between the obtained labels
                and the gold one.

        """
        lang = lang.capitalize()
        if row['label'+lang] != '' and row['goldLabel'+lang] != '':
            score = max([scoring_function(row['goldLabel'+lang], elem)
                         for elem in row['label'+lang].split('|')])
        else:
            score = np.nan
        return score

    @staticmethod
    def _scoring_best_label(row, lang, scoring_function):
        """Compare the translations with the gold label.

        This function compares the gold label with the labels and altLabels of
        the translations. Built to be used in an apply on a pd.DataFrame.

        Args:
            row (pd.Serie): the row the function will look at.
            lang (str): the two letter name of the language.
            scoring_function (func): a function which compute
                similarity between two strings.

        Returns:
            float: the maximum of the similarity between the obtained labels
                and altLabels and the gold label.

        """
        lang = lang.capitalize()
        if row['label'+lang] != '' and row['goldLabel'+lang] != '':
            score = max([scoring_function(row['goldLabel'+lang], elem)
                         for elem in row['label'+lang].split('|')
                         + row['alt'+lang].split('|')])
        else:
            score = np.nan
        return score

    @staticmethod
    def _scoring_mean_best_label(row, lang, scoring_function):
        """Mean of the comparison of all translations and all the gold labels.

        This function compares the gold label and altLabels with the labels
        and altLabels of the translations and output the mean.
        Built to be used in an apply on a pd.DataFrame.

        Args:
            row (pd.Serie): the row the function will look at.
            lang (str): the two letter name of the language.
            scoring_function (func): a function which compute similarity
                between two strings.

        Returns:
            float: the mean of the max similarity between the obtained labels
                and altLabels and the gold label and altLabels.

        """
        lang = lang.capitalize()
        if row['label'+lang] != '' and row['goldLabel'+lang] != '':
            score = np.mean(
                [max([scoring_function(elem_gold, elem)
                      for elem in row['label'+lang].split('|')
                      + row['alt'+lang].split('|')])
                 for elem_gold in [row['goldLabel'+lang]]
                 + row['goldAlt'+lang].split('|')])
        else:
            score = np.nan
        return score

    @staticmethod
    def _scoring_max_best_label(row, lang, scoring_function):
        """Max of the comparison of all translations and all the gold labels.

        This function compares the gold label and altLabels with the labels
        and altLabels of the translations and outputs the max.
        Built to be used in an apply on a pd.DataFrame.

        Args:
            row (pd.Serie): the row the function will look at.
            lang (str): the two letter name of the language.
            scoring_function (func): a function which compute similarity
                between two strings.

        Returns:
            float: the max of the max similarity between the obtained labels
                and altLabels and the gold label and altLabels.

        """
        lang = lang.capitalize()
        if row['label'+lang] != '' and row['goldLabel'+lang] != '':
            score = max(
                [max([scoring_function(elem_gold, elem)
                      for elem in row['label'+lang].split('|')
                      + row['alt'+lang].split('|')])
                 for elem_gold in [row['goldLabel'+lang]]
                 + row['goldAlt'+lang].split('|')])
        else:
            score = np.nan
        return score

    def __get_score(self, translation_df, metric, output_dir):
        """Get the score for a given metric.

        This function compute the score for a given metric, then creates
        a text file with the results inside and the histogram for each
        language of the four metrics described in the paper.

        Args:
            translation_df (pd.DataFrame): dataFrame with the gold label and
                the translations.
            metric (str): name of the algorithm used to compute the similarity.
                Has to be in textdistance.
            output_dir (str): path of the folder where the files will be
                created

        Returns:
            [type]: [description]

        """
        logger.info(f'Start computing results with {metric} metric.')
        quality_metrics = ['label', 'best_label', 'mean_best_label',
                           'max_best_label']
        dict_results = {}
        columns = translation_df.columns
        lang_list = [column.replace('label', '') for column in columns
                     if 'label' in column[:5]]
        filename = os.path.join(output_dir, metric+'.txt')
        result_file = open(filename, 'wt')
        result_file.write(f'Results computed with the {metric} metric.\n')

        for lang in tqdm(lang_list):
            result_file.write(f'Result in {lang}:\n')
            for quality_metric in quality_metrics:
                column_name = 'score' + metric.capitalize()\
                              + lang.capitalize() + quality_metric.capitalize()
                metric_function = getattr(self, '_scoring_' + quality_metric)
                logger.debug(f'{column_name}, {lang}, {lang_list}')
                translation_df.loc[:, column_name] =\
                    translation_df.apply(
                        lambda row: metric_function(
                            row, lang, getattr(textdistance, metric)),
                        axis=1
                    )
                mean_result = translation_df.loc[:, column_name].mean()
                result_file.write(f'\t{quality_metric}: {mean_result}\n')
        return translation_df

    def score(self, translation_df, output_dir='results'):
        """Score the quality of the translations.

        Args:
            translation_df (pd.DataFrame): DataFrame with the translated
                labels and the gold ones. For each language, the following
                columns are needed:
                ['labelLang', 'altLang', 'goldLabelLang', 'goldAltLang']
            output_dir (str, optional): [description]. Defaults to 'results'.

        Returns:
            pd.DataFrame: translation + columns with the scores.

        """
        dict_results = {}

        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

        for metric in self.scoring_functions:
            translation_df = self.__get_score(translation_df, metric,
                                              output_dir)

        return translation_df
