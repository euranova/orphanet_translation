"""Compute the mean number of labels."""
import os

import numpy as np


def _get_nb_labels_apply(row, column_label, column_alt):
    all_labels = []
    nb_labels = 0
    label = row[column_label]
    alt = row[column_alt]
    if label != '' and label is not None:
        nb_labels = 1
        all_labels += [label]
        if alt != '' and alt is not None:
            nb_labels += len(alt.split('|'))
            all_labels += alt.split('|')
    return len(list(set(all_labels)))


def count_synonyms(results_df, result_folder):
    """Count the number of synonyms.

    Args:
        results_df (pd.DataFrame): DataFrame with the translated
            and the gold labels.
        result_folder (str): Folder where the results will be written.

    """
    path_file = os.path.join(result_folder, 'synonyms.txt')
    lang_list = [column.replace('label', '') for column in results_df.columns
                 if 'label' in column]
    with open(path_file, 'wt') as result_file:
        for lang in lang_list:
            lang_cap = lang.capitalize()
            gold_label = 'goldLabel' + lang_cap
            gold_alt = 'goldAlt' + lang_cap
            wiki_label = 'label' + lang_cap
            wiki_alt = 'alt' + lang_cap

            nb_labels_full = results_df.apply(
                lambda row: _get_nb_labels_apply(row, gold_label, gold_alt),
                axis=1
            )
            nb_labels_full = nb_labels_full.replace({0: np.nan})
            result_file.write(
                f'Average on the entire ontology in {lang}: '
                + f'{nb_labels_full.mean()}\n')

            lang_elem_df = results_df[results_df['label'+lang_cap] != '']

            nb_labels_gold = lang_elem_df.apply(
                lambda row: _get_nb_labels_apply(row, gold_label, gold_alt),
                axis=1
            )
            nb_labels_gold = nb_labels_gold.replace({0: np.nan})
            result_file.write(
                f'Average on the ontology on the subset with Wikidata labels'
                + f' in {lang}: {nb_labels_gold.mean()}\n')

            nb_labels_wiki = lang_elem_df.apply(
                lambda row: _get_nb_labels_apply(row, wiki_label, wiki_alt),
                axis=1
            )
            result_file.write(
                f'Average on Wikidata in {lang}: '
                + f'{nb_labels_wiki.mean()}\n')
