# HTML Adapted Tree Matching Algorithm:

## Requirements:

- Python > 3.7
- Using pip, install the required dependencies:

    ```$ pip install --user -r requirements.txt```
    
## Setup submodules:

- ```$ git submodule update --init --recursive```
- Install HTML-APTED Requirements

and then run:
```
cd HTML-APTED
gradle wrapper
./grawlew build
cd ..
```

## Run:

There are three different use cases for this project:

### Fawkes Static Template (Offline phase):

To generate Fawkes static template using two different versions of HTML files:

```
python3 treematching/run_apted.py first_html second_html out_path
```
The third argument is the path to the generated static template.

### Fawkes Dynamic Patch (Online phase):
```
python3 treematching/run_apted.py first_html second_html out_path json
```
The third argument is the path to the generated dynamic patch, which is a json file. The last argument must be "json".


### Similarity Analysis (Motivation):
We compute a similarity metric for the two given HTML files as a percentage of shared paths.
```
python3 treematching/similarity.py first_html second_html
```
