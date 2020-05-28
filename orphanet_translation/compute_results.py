"""Main function to compue the results."""
import argparse
import json
import logging
import os

import numpy as np
import pandas as pd
from wikidata_property_extraction import translation, header, second_order

from orphanet_translation import loader
from orphanet_translation.metrics import coverage, scorer, synonyms

LANG_LIST = ['en', 'fr', 'de', 'es', 'pl', 'it', 'pt', 'nl', 'cs']

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _load_from_file(data_folder):
    file_path = os.path.join(data_folder, 'full_data_df.json')
    full_data_df = pd.read_json(file_path)
    return full_data_df


def _load_from_wikidata_query(data_folder, user_agent, result_folder):
    header.initialize_user_agent(user_agent)

    xref_onto_df = loader.load_ordo_external_references(data_folder)

    dict_properties = {'P492': 'OMIM', 'P2892': 'UMLS', 'P486': 'MeSH',
                       'P672': 'MeSH', 'P6694': 'MeSH', 'P6680': 'MeSH',
                       'P3201': 'MedDRA', 'P494': 'ICD-10', 'P4229': 'ICD-10'}

    translator = second_order.SecondOrder('P1550', xref_onto_df,
                                          dict_properties, LANG_LIST,
                                          all_elem=True, nb_elems_values=250)

    full_data_df = translator.translate()

    path_json = os.path.join(result_folder, 'full_data_df.json')

    full_data_df.to_json(path_json)
    return full_data_df


def _compute_all_results(full_onto_df, result_df, metric_list, results_folder):
    if not os.path.exists(results_folder):
        os.mkdir(results_folder)

    scoring = scorer.Scorer(metric_list)
    logger.info('Start computing coverage.')
    # Compute the coverage
    coverage.compute_coverage(full_onto_df, result_df, results_folder)

    logger.info('Start computing number of labels.')

    # Compute the average number of labels by Orphanet entity in function of
    # the language
    synonyms.count_synonyms(result_df, results_folder)

    logger.info('Start computing quality scores.')

    # Compute the quality score
    scoring.score(result_df, output_dir=results_folder)


def main(data_folder, metric_list, results_folder, user_agent,
         recompute=False, no_gct=False):
    """Get the data and compute the results.

    Args:
        data_folder (str): Folder with the data.
        metric_list (list): List of string with the name of the quality
            metrics.
        results_folder (str): Folder where the results will be written.
        user_agent (str): user_agent to query Wikidata.
        recompute (bool, optional): True, query the data frow Wikidata,
            false, from files. Defaults to False.
        no_gct (bool, optional): Flag to specify if translation from Google
            Cloud translation are available.

    """
    # Load gold label from Ordo dataset
    logger.info('Load ordo data from file.')
    ordo_df = loader.load_ordo_data(data_folder)

    # Load the Wikidata data
    if recompute:
        logger.info('Starting to query Wikidata.')
        full_data_df = _load_from_wikidata_query(data_folder, user_agent,
                                                 results_folder)
    else:
        logger.info('Load Wikidata data from file.')
        full_data_df = _load_from_file(data_folder)

    full_data_df.loc[:, 'value_property'] = \
        full_data_df['value_property'].astype(str)

    # Load the data obtained with Google Cloud Translation
    logger.info('Load Google Cloud Translation data from file.')
    gct_translation_df = loader.load_gct_data(data_folder)

    # Create the result folder it does not exist yet
    if not os.path.exists(results_folder):
        os.mkdir(results_folder)

    logger.info('First-order')
    # Merge data obtained through first_order links and gold data
    first_order_df = \
        full_data_df[full_data_df['source_degree'] == 'First']
    first_order_df = first_order_df.applymap(loader._empty_elem_wikidata)
    first_order_df = loader._merge_same_ordo_id(first_order_df)

    xref_wiki_ordo_1st_df = pd.merge(ordo_df, first_order_df, left_index=True,
                                     right_on='value_property')

    xref_wiki_ordo_1st_df.fillna('', inplace=True)

    _compute_all_results(ordo_df, xref_wiki_ordo_1st_df, metric_list,
                         os.path.join(results_folder, 'wikidata_first_only'))

    logger.info('Second-order')
    # Merge data obtained through second_order links and gold data
    second_only_df = \
        full_data_df[full_data_df['source_degree'] == 'Second']
    second_only_df = second_only_df.applymap(loader._empty_elem_wikidata)
    second_only_df = loader._merge_same_ordo_id(second_only_df)

    xref_wiki_ordo_2nd_df = pd.merge(ordo_df, second_only_df, left_index=True,
                                     right_on='value_property', how='inner')

    xref_wiki_ordo_2nd_df.fillna('', inplace=True)

    _compute_all_results(ordo_df, xref_wiki_ordo_2nd_df, metric_list,
                         os.path.join(results_folder, 'wikidata_second_only'))

    logger.info('First- and second-order')
    # Merge data obtained through first- and second-order links and gold data
    first_second_wiki_df = full_data_df.applymap(loader._empty_elem_wikidata)
    first_second_wiki_df = loader._merge_same_ordo_id(first_second_wiki_df)

    xref_wiki_ordo_1st_2nd_df = pd.merge(ordo_df, first_second_wiki_df,
                                         left_index=True,
                                         right_on='value_property',
                                         how='inner')

    xref_wiki_ordo_1st_2nd_df.fillna('', inplace=True)

    _compute_all_results(ordo_df, xref_wiki_ordo_1st_2nd_df, metric_list,
                         os.path.join(results_folder, 'wikidata_full'))

    if not no_gct:
        logger.info('Google Cloud Translation')
        # Load data obtained through Google Cloud Translation
        gct_translation_df.index = gct_translation_df.index.map(str)

        # Merge data obtained through Google Cloud Translation and gold data
        xref_gct_ordo_df = pd.merge(ordo_df, gct_translation_df,
                                    left_index=True, right_index=True)
        xref_gct_ordo_df.drop(['goldLabelEn', 'goldAltEn'], axis=1,
                              inplace=True)

        xref_gct_ordo_df.fillna('', inplace=True)

        _compute_all_results(ordo_df, xref_gct_ordo_df, metric_list,
                             os.path.join(results_folder, 'gct'))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Compute results of Orphanet translation through Wikidata'
    )
    parser.add_argument('--data_folder',
                        help='Folder with the required files.')
    parser.add_argument('--result_folder',
                        help='Folder where the results will be written.')
    parser.add_argument('--metrics', nargs='+',
                        help='Metrics used for the quality score.')
    parser.add_argument('--recompute', action='store_true',
                        help='Flag to query Wikidata instead '
                             + 'of using the files.')
    parser.add_argument('--no_gct', action='store_true',
                        help='Flag to specify if translation from Google Cloud'
                        + ' Translation are available.')
    parser.add_argument('--user_agent',
                        help='Specify a user_agent to query Wikidata.',
                        default='')
    args = parser.parse_args()

    if args.recompute and args.user_agent == '':
        raise ValueError('user_agent has not been defined or as an empty'
                         + ' string. .Please follow the rules of MediaWiki to '
                         + 'define your user-agent.')

    main(data_folder=args.data_folder, metric_list=args.metrics,
         results_folder=args.result_folder, recompute=args.recompute,
         user_agent=args.user_agent)
