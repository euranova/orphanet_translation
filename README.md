# Orphanet translation

This code replicates the experiments in the paper ["Multilingual enrichment of disease biomedical ontologies"](https://arxiv.org/abs/2004.03181).
This work use the data from [Orphanet](http://www.orphadata.org). The data is composed fo desease instances associated to many labels in various laguages (Czech, Dutch, English, French, German, Italian, Polish, Portuguese, and, Spanish). 
The experiments uses these labels to evaluate and compare the translations quality of the entities: 
  1. when extracted from Wikidata with the methods described in the paper (code available [wikidata_property_extraction](https://github.com/euranova/wikidata_property_extraction))
  2. when the English labels of Orphanet are translated in the other languages available with Google Cloud Translation.  

The translations available in Orphanet are used as the groundtruth translations to evaluate the two methods. 

In Orphanet and Wikidata disease entities have several labels, one of them being tagged as the _preferred label_. 
For Google Cloud Translation, the _preferred label_ is the translation of the English _preferred label_ in Orphanet.

To compare the quality of these translations, we use several metrics:
 * __Quality score__: in the paper the Jaro distance was used, in the code you can precise
the metric you want (the list is available in [Options](#options)). 
We define for each language 4 metrics which are the mean over all entities of the following entity-wise metrics :
   * __label__: compares the translated preferred label of each entity with the _gold_ preferred translation,
     it asseses the similarities of the preferred translation only, 
   * __best_label__: compares all the obtained tranlsations with the gold preferred translation,
     it evaluates if the gold preferred translation is present in the set of the translations of all the entity's labels,
   * __mean_best_label__: mean of the evaluation of all the obtained translations with all the gold translations, 
     this score can be seen as a completeness score, it evaluates the ability of finding 
     all the gold translation in all the obtained tranlsations,
   * __max_best_label__: max of the evaluation of all the obtained translations with all the gold translations, 
     this score evaluates if there is at least one label in common between the gold translation and the obtained translation.
 * __Coverage__: the percentage of the ontology that is available in the source (Wikidata) for a given language.
 * __Synonyms__: the average number of synonyms per entity in the source for a given language.


The data to replication the experiment of the paper is available
[here](https://drive.google.com/file/d/17LWGJNIWtto_LodQn0fJfx72ZT20ttJh/view?usp=sharing).
It contains entities from orphadata and wikidata at the time of the publication, and translations from the 
Google cloud translation service for these entities.


## Install the required librairies

To install the required librairies you need python 3:

```bash
pip install -r requirements.txt
```

## Compute results from the paper

To replicate the results in the paper, download the data, put the data in a folder named 'data', install the package in 'requirements.txt', and then:

```bash
python orphanet_translation/compute_results.py --data_folder data --result_folder results --metrics jaro --user_agent "Please define a user agent"
```

The results will be in the folder *results*, there will be 4 subfolders, for each different comparison:
* wikidata_first_only: score with the first-order links only
* wikidata_second_only: score with the second-order links only
* wikidata_full: score with the second and first-order links
* gct: score with Google Cloud Translation

## Compute results for the current state of Wikidata and Orphanet

It is also possible to test on current data, you can download the latest version of ordo [here](http://www.orphadata.org/cgi-bin/rare_free.html), by clicking on 'Cross-referencing of rare diseases'.

Put them into a folder 'data' and then:

```bash
python orphanet_translation/compute_results.py --data_folder data --result_folder results --metrics jaro --recompute --no_gct --user_agent Please specify a user agent
```

The user_agent should be created following the [Wikimedia guidelines](https://meta.wikimedia.org/wiki/User-Agent_policy).

**WARNING**: As of now, the package Wikidata_property_extraction is not optimized and the queries to Wikidata takes a long time and can lead to a 24-hour IP ban to the Wikimedia services.

The results will be in the same fashion than the other command, but the subfolder *gct* will not exist.

## Options

The function compute_results.py in orphanet_translation has several options:

* data_folder: the folder with the data inside. Usage example: --data_folder data. Compulsory.
* result_folder: the folder where the results will be stored, doesn't have to exist. Usage example: --result_folder result. Compulsory.
* metrics: the name of the metrics used, have to be a value in ['jaro_wrinkler', 'jaro', 'strcmp95', 'needleman_wunsch', 'gotoh',  'tversky', 'overlap', 'tanimoto', 'cosine', 'monge_elkan', 'ratcliff_obershelp', 'identity'], more information can be found in the [textdistance package](https://github.com/life4/textdistance). Usage example: '--metrics jaro identity', to compute the results with the Jaro and the identity metrics. Compulsory.
* recompute: Flag to specify if the data from Wikidata should be recomputed or not. --recompute if Wikidata data has to be downloaded or nothing if not.
* no_gct: Flag to specify if GCT data is available. --no_gct if no data for Google Cloud Translation is available, nothing if available.
* user_agent: Compulsory if --recompute is specified. The user-agent of the requests, has to comply to the [Wikimedia guidelines](https://meta.wikimedia.org/wiki/User-Agent_policy).

## Exploring the results

The script will print the results in text files which will be in different folder depending on how the entities were extracted :

* wikidata_first_only: this folder contains the results when the entities are extracted by using only first-order links between Wikidata and Orphanet.
* wikidata_second_only: this folder contains the results when the entities are extracted by using only second-order links between Wikidata and Orphanet.
* wikidata_full: this folder contains the results when the entities are extracted by using first and second-order links between Wikidata and Orphanet.
* gct (when available): this folder contains the results when the entities are extracted by translating the English labels of Orphanet.

Then in each of these folders, there will be text files with the results of the different metrics:
* coverage.txt: this file contains the result for the coverage, there are three lines for each language:
  * The first one is the number of entities in Orphanet for the language
  * The second is the number of entities obtained for the language with the specific enrichment method
  * The third is the percentage of Orphanet entities available in the enrichment method
* synonyms.txt: this file contains the average number of labels available for the entities in each language, there are 3 lines per language:
  * The first one is the average number of labels in the entire Orphanet in the language
  * The second one is the average number of labels in the Orphanet subset that have at least one label extracted
  * The third is the average number of labels obtained with the enrichment method
* method_name.txt: for each distance metric specified in the command to launch the script there will be a file. These files will be composed of 4 lines for each language which are the 4 metrics explained in the introduction.

## Citation

If you use these results please cite this paper:

```bibtex
@inproceedings{bouscarrat:hal-02531140,
  TITLE = {{Multilingual enrichment of disease biomedical ontologies}},
  AUTHOR = {Bouscarrat, L{\'e}o and Bonnefoy, Antoine and Capponi, C{\'e}cile and Ramisch, Carlos},
  URL = {https://hal.archives-ouvertes.fr/hal-02531140},
  BOOKTITLE = {{2nd workshop on MultilingualBIO: Multilingual Biomedical Text Processing}},
  ADDRESS = {Marseille, France},
  YEAR = {2020},
  MONTH = May,
  KEYWORDS = {wikidata ; ontology ; translation ; biomedical},
  PDF = {https://hal.archives-ouvertes.fr/hal-02531140/file/enrichment_ontology%20%281%29.pdf},
  HAL_ID = {hal-02531140},
  HAL_VERSION = {v1},
}
```