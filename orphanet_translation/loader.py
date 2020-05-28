"""Loading functions to load the files."""

import json
import os
import re

import numpy as np
import pandas as pd

LANG_LIST = ['cs', 'de', 'en', 'es', 'fr', 'it', 'nl', 'pl', 'pt']


def _get_value(dict_disease):
    dict_disease = {key: value['value'] for key, value in dict_disease.items()}
    return dict_disease


def _json_to_pandas(json_text):
    json_text = [_get_value(elem) for elem in json_text['results']['bindings']]
    return pd.DataFrame(json_text)


def _empty_elem_wikidata(elem):
    pattern = re.compile('Q[0-9]+')
    # This pattern is a default identifier of WikiData when the label does
    # not exist for this entity in a given language
    if type(elem) != str or pattern.match(elem):
        return np.nan
    return elem


def _merge_same_ordo_id(wikidata_df):
    wikidata_df = wikidata_df.replace({'': '|', np.nan: '|'})
    wikidata_df = \
        wikidata_df.groupby('value_property').agg(lambda x: '|'.join(x))
    wikidata_df = wikidata_df.applymap(lambda r: re.sub(r'\|+', '|', r))
    wikidata_df = wikidata_df.applymap(lambda r: re.sub(r'\|$', '', r))
    wikidata_df = wikidata_df.applymap(lambda r: re.sub(r'^\|', '', r))
    wikidata_df = wikidata_df.replace({'|': np.nan})
    wikidata_df = wikidata_df.applymap(
        lambda r: '|'.join(list(set(r.split('|')))) if r else np.nan
    )
    return wikidata_df


def load_wikidata_data(data_folder='data'):
    """Loader WikiData data.

    Args:
        data_folder (str, optional): Folder where the data is.
            Defaults to 'data'.

    Returns:
        pd.DataFrame: The results in a DataFrame.

    """
    wiki_df = pd.DataFrame(columns=['disease', 'id_ordo'])
    for lang in LANG_LIST:
        path = os.path.join(data_folder, lang + '_query_ordo.json')
        with open(path, encoding='utf-8') as json_file:
            json_lang = json.load(json_file)
        wiki_lang_df = _json_to_pandas(json_lang)
        wiki_df = pd.merge(wiki_df, wiki_lang_df, on=['disease', 'id_ordo'],
                           how='outer')
    wiki_df = wiki_df.applymap(_empty_elem_wikidata)
    wiki_df.rename(columns={'id_ordo': 'value_property'}, inplace=True)
    wiki_df = _merge_same_ordo_id(wiki_df)
    return wiki_df


def _get_synonyms_ordo(elem):
    if type(elem) == list:
        elem = elem[0]
        if type(elem) == dict and 'Synonym' in elem.keys():
            syn_list = []
            for synonym in elem['Synonym']:
                syn_list.append(synonym['label'])
            return '|'.join(syn_list)
        else:
            return ''
    else:
        return ''


def _get_name_ordo(elem):
    if type(elem) == list:
        elem = elem[0]
        if 'label' in elem.keys():
            return elem['label']
        else:
            return ''
    else:
        return ''


def _get_ordo_lang(lang, data_folder):
    path = os.path.join(data_folder, lang+'_product1.json')
    df = pd.read_json(path)
    ordo_df = pd.DataFrame(df.iloc[0]['JDBOR']['DisorderList'][0]['Disorder'])
    del df
    ordo_df = ordo_df[['OrphaNumber', 'Name', 'SynonymList']]
    ordo_df = ordo_df.rename(columns={'Name': 'Name_'+lang,
                                      'SynonymList': 'SynonymList_'+lang})
    ordo_df = ordo_df.set_index('OrphaNumber').sort_index()
    syn_ordo_df = pd.DataFrame()
    syn_ordo_df['goldLabel'+lang.capitalize()] = \
        ordo_df['Name_'+lang].apply(_get_name_ordo)
    syn_ordo_df['goldAlt'+lang.capitalize()] = \
        ordo_df['SynonymList_'+lang].apply(_get_synonyms_ordo)
    return syn_ordo_df


def load_ordo_data(data_folder='data'):
    """Loader ordo data.

    Args:
        data_folder (str, optional): Folder where the data is.
            Defaults to 'data'.

    Returns:
        pd.DataFrame: The results in a DataFrame.

    """
    ordo_lang_df = pd.DataFrame()
    ordo_translation = pd.DataFrame()

    for lang in LANG_LIST:
        ordo_lang_df = pd.merge(ordo_lang_df,
                                _get_ordo_lang(lang, data_folder),
                                left_index=True, right_index=True, how='outer')

    ordo_translation = pd.merge(ordo_lang_df, ordo_translation,
                                left_index=True, right_index=True, how='outer')
    ordo_translation.fillna('', inplace=True)
    return ordo_translation


def load_gct_data(data_folder='data'):
    """Load Google Cloud Translate data.

    Args:
        data_folder (str, optional): Folder where the data is.
            Defaults to 'data'.

    Returns:
        pd.DataFrame: The results in a DataFrame.

    """
    path = os.path.join(data_folder, 'gct_translation.json')
    gct_df = pd.read_json(path)
    columns = gct_df.columns
    columns_needed = [column.replace('gct', '') for column in columns
                      if 'gct' in column[:3]]
    gct_df = gct_df[columns]
    gct_df.fillna('', inplace=True)
    return gct_df


def load_external_onto_wikidata_data(data_folder='data'):
    """Load the external ontologies entities in Wikidata from JSON.

    Args:
        data_folder (str, optional): Folder with JSON files.
            Defaults to 'data'.

    Returns:
        dict: dictionnary with the DataFrames for each external ontology.
            Ontologies available: [UMLS, ICD10CM, MeSH, ICD10, MedDRA, OMIM]

    """
    # JSON with labels and altLabels
    second_order_df = \
        pd.read_json(os.path.join(data_folder, 'second_order_disease.json'))

    onto_list = ['id_UMLS', 'id_ICD10CM', 'id_MeSH', 'id_ICD10',
                 'id_MedDRA', 'id_OMIM']

    wiki_onto_dict = {}
    for id_onto in onto_list:
        path_file = os.path.join(data_folder, id_onto+'.json')
        with open(path_file, 'r') as json_file:
            wiki_onto_df = pd.read_json(json_file)
        join_columns = \
            wiki_onto_df.columns.intersection(second_order_df.columns)
        wiki_onto_df = pd.merge(wiki_onto_df, second_order_df,
                                on=join_columns.tolist())
        wiki_onto_dict[id_onto] = wiki_onto_df
    return wiki_onto_dict


def _get_external_refs(row):
    dict_ref_list = []
    if row['ExternalReferenceList'][0]['count'] != '0':
        for elem in row['ExternalReferenceList'][0]['ExternalReference']:
            ref_dict = {}
            ref_dict['id'] = elem['id']
            ref_dict['source'] = elem['Source']
            ref_dict['reference'] = elem['Reference']
            dict_ref_list.append(ref_dict)
    return dict_ref_list


def load_ordo_external_references(data_folder='data'):
    """Load the external references found in ordo.

    Args:
        data_folder (str, optional): Folder with JSON files.
            Defaults to 'data'.

    Returns:
        pd.DataFrame: DataFrame with the external references. Three columns.
            - id: the orphanet id.
            - reference: the id in the external ontology.
            - source: the name of the external ontology.

    """
    path_file = os.path.join(data_folder, 'en_product1.json')
    with open(path_file, 'r') as json_file:
        json_file = json.load(json_file)
    ordo_full_df = pd.DataFrame(
        json_file['JDBOR'][0]['DisorderList'][0]['Disorder']
    )
    reference_df = \
        ordo_full_df['ExternalReferenceList'][0][0]['ExternalReference']
    # We need to extract the external reference in a more readable format.
    ordo_full_df['external_refs'] = ordo_full_df.apply(_get_external_refs,
                                                       axis=1)

    # We then want a DataFrame with one reference per line.
    dict_ref = {}

    for _, row in ordo_full_df.iterrows():
        id_disease = row['OrphaNumber']
        dict_ref[id_disease] = pd.DataFrame(row['external_refs'])

    xref_ordo_df = \
        pd.concat(dict_ref.values(), keys=dict_ref.keys(), sort=True)

    xref_ordo_df.drop('id', axis=1, inplace=True)
    xref_ordo_df.reset_index(level=0, inplace=True)

    xref_ordo_df.rename(columns={'level_0': 'value_property',
                                 'reference': 'id_auxiliary',
                                 'source': 'name_auxiliary'}, inplace=True)
    return xref_ordo_df
