# Getting Started with BabelMatcher

This project uses Babelnet data to create a model to process text, finding the data related to a lemma, or babelnet id.

## Configuration

The BabelMatcher can run out of babel tokens when processing, because Babelnet has a limited number of available tokens to use in a 24 hours span.
When this happens a: **Waiting, coins were spent !!!!!!**, will appear in the console.

The data use as a test is a csv with the structure if the Padchest data file. It should be a csv with and unnamed column that contains the index, and a **Report** column
that contains the text data to process. 

The BabelMatcher can be used by its own but there are 5 different python programs that show the correct used of this proyect.
This are ( all of these programs save the model into a specific file, and the result is a json file with a specific name, read below ):

* ##### process_by_all_lemmas_with_padchest_data

Process the text with all the data that can be extracted from Babelnet, this mean, using all lemmas found, without disambiguation.

* ##### process_by_first_lemma_with_padchest_data

Process the text with the first lemma found by babelnet using lemmas as query.

* ##### process_by_id_and_tag_list_with_padchest_data

Process the text with a list of ids and tags, this marks the results with the tags but the meaning or process is related to the ids data.

* ##### process_by_id_list_with_padchest_data

Process the text with a list of ids and the first lemma found by the id is the tag to match in the result.

* ##### process_with_saved_model

Process the text using a previously saved model.

---

In the project there is a **config_template.yaml** file that contains the structure and variables used by the above programs. This files needs to
be rename to **config.yaml** so the programs works. The **config_template.yaml** is descriptive of the types values of the variables it should contain.