"""Test class Scorer."""

import numpy as np
from operator import add
import pandas as pd

from orphanet_translation import scorer


def test_end_to_end():
    """Test end to end for Scorer."""
    columns = ['labelEn', 'altEn', 'goldLabelEn', 'goldAltEn']
    values = [['test', 'test1|test2', 'test', 'test2|test1'],
              ['disease', 'disease',  'disease', 'flu']]

    input_df = pd.DataFrame(values, columns=columns)
    scorer_tool = scorer.Scorer(['jaccard', 'jaro'])
    output_df = scorer_tool.score(input_df)

    new_columns = ['scoreJaccardEnLabel', 'scoreJaccardEnBest_label',
                   'scoreJaccardEnMean_best_label',
                   'scoreJaccardEnMax_best_label', 'scoreJaroEnLabel',
                   'scoreJaroEnBest_label', 'scoreJaroEnMean_best_label',
                   'scoreJaroEnMax_best_label']
    new_values = [[1, 1, 1, 1, 1, 1, 1, 1], [1, 1, 0.5, 1, 1, 1, 0.5, 1]]
    new_values = list(map(add, values, new_values))
    expected_df = pd.DataFrame(new_values, columns=columns+new_columns)
    assert(output_df.iloc[1].equals(expected_df.iloc[1]))
