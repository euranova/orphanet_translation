"""Compute the coverage of Wikidata respect with Orphanet."""
import os

import numpy as np


def compute_coverage(full_onto_df, result_df, result_folder):
    """Compute the coverage and print the results in a file.

    Args:
        full_onto_df (pd.DataFrame): the DataFrame containing the information
            of the ontology.
        result_df (pd.DataFrame): the DataFrame containing the information
            extracted from Wikidata.
        result_folder (str): the folder where the file with the results will
            be created.

    """
    result_df = \
        result_df[result_df.index.isin(full_onto_df.index.values)]
    path_file = os.path.join(result_folder, 'coverage.txt')
    lang_list = [column.replace('label', '') for column in result_df.columns
                 if 'label' in column]
    with open(path_file, 'wt') as result_file:
        for lang in lang_list:
            nb_elem_wikidata = \
                result_df['label'+lang.capitalize()] \
                .replace('', np.nan).count()
            nb_elem_ordo = full_onto_df['goldLabel'+lang.capitalize()] \
                .replace('', np.nan).count()
            result_file.write(f'Coverage in {lang}: \n{nb_elem_ordo} with a'
                              + f' label in Orphanet \n{nb_elem_wikidata} with'
                              + f' a label from Wikidata'
                              + f'\n{nb_elem_wikidata/nb_elem_ordo} of '
                              + f'entities have at least one label '
                              + f'in Wikidata.\n')
