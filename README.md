# Defect Prediction

[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](./CODE_OF_CONDUCT.md)


## Mission

Software defect prediction (SDP) is a technique for improving software quality and reducing software testing costs through the creation of multiple categorization or classification models utilizing various machine learning approaches.
SDP is part of the software development life cycle in which we predict the fault using a Machine Learning (ML) approach with historical data.
The objective is to have information for prioritization in regression testing, technical debt attention and automation testing backlog. For developers can be useful for approaching in peer reviews.

## Getting Started

A quick introduction of the minimal setup you need to start.

- Install extensions Python, Jupiter for Visual Studio Code (or your IDE).
- Verify your permissions to access through API at the source code (GitHub, Azure DevOps,etc) and test management tool (e.g. Jira or Azure)
- Clone the project
```powershell
git clone https://github.com/software-defect-prediction.git
```
Or download the ZIP from GitHub, extract it, and navigate to the extracted folder.
- Create a virtual environment 
```powershell
python -m venv venv
```
- Activate it
```powershell
venv\Scripts\activate
```
- Install dependencies 
```powershell
install -r requirements.txt
```


## Further information

### Datasets:
  **Code metrics**---> Reflect internal information about the structure of the source code. Usually 3 dimensions: complexity (e.g., McCabe Cyclomatic), volume (e.g., lines of code), and object-oriented (e.g., a coupling between object classes)
  **Process metrics**: Reflect practices in the process of code generation. (1) the number of files in each commit, (2) the number of added lines of code, (3) the number of deleted lines of code, (4) the number of active developers, and (5) the number of distinct developers, etc.
  **Human metrics**: Reflect the roles behind the process. Ownership metrics (minors authors and major authors). Here, also is possible to define different levels of expertise or dynamics in the teams.

### Examples of datasets in code metrics:
#### Code metrics (McCabe)
  - Loc: Line count of code 
  - v(g): cyclomatic complexity
  - ev(g): essential complexity
  - iv(g): design complexity

#### Code metrics (Halstead)
  - N: Total operators + operands
  - V: volume
  - L: program lenght
  - D: difficulty
  - I: intelligence
  - E: effort to write the program
  - B: Delivered bugs
  - T: time estimator
  - IOCode: line count of code
  - IOComment: count of lines of comments
  - IOBlank: cout of blank lines
  - IOCodeAndComment: lines of code and comments

#### Others metrics
  - uniqOp: unique operators
  - uniqOpnd: unique operands
  - totalOp: total operators
  - total Opnd: total operands
  - branchCount: flow of graph
  - Def: module has defects or not


### Models

You can change the models of Machine Learning in `notebooks\05_training_model_defect_prediction.ipynb`. Currently the program uses

* K-means for clustering
* Catboost , Decision Tree, and Random Forest (RF) as ML algorithms
* LIME as technique explanation
* Differential Evolutionary Optimization Decision tree

### Dataset configuration

In the file commit_set_prediction you must to include the range of commits that you want to include for prediction. For exmaple, if you have a release or version, you need to include there only the commits done during the range of the time that you want to predict. 

Specific example: I want to predict a release which is from 15 July until 3rd October
So, it means that the file commit_set_prediction only has commits between this range.

The training of the model must have been done with data before 15 of July in this example (FILE azure_data.csv)

The commits extraction from azure will be saved in a file named: 

> _azure_data.csv


The metrics extraction will be saved in a file named:

> _metrics_code.csv


### Steps of execution

Here's a brief intro about what a developer must do in order to start developing
the project further:

```shell
git clone https://github.com/software-defect-prediction.git
cd notebooks/
```
--> Configure your user, variables, password and repositories in the file: `config.ipynb`. You can use the file `config_example.ipynb` as a guide, first modify it and then change the name of the file and remove the word "example".

--> We recommend to use the internal execution in Visual Studio Code with the play button inside each notebook/cell, following the order indicated below. Else, you will need to execute the next commands (which are slower, 25% +), having activated the virtual environment:

```powershell
venv\Scripts\activate
```

1. Dataset extraction: to execute the 3 extractions (configure your project values on this point, see below - pending to develop extraction of issues or bugs)

```shell
cd notebooks
python -m papermill 01_extraction_azure_commits.ipynb output.ipynb
```

```shell
cd notebooks
python -m papermill 02_extraction_code_metrics.ipynb output.ipynb
```

2. Dataset pre-processing: to execute 04_preprocess_training_model.ipynb

```shell
cd notebooks
python -m papermill 04_preprocess_training_model.ipynb output.ipynb
```

3. Training model: to execute 05_training_model_defect_prediction.ipynb

```shell
cd notebooks
python -m papermill 05_training_model_defect_prediction.ipynb output.ipynb
```

7. Review the results of the evaluation model, metrics and explainability

8. Perform prediction 06_prediction_execution.ipynb

```shell
cd notebooks
python -m papermill 06_prediction_execution.ipynb output.ipynb
```

9. Check again the results and explainability technique implemented

> _Execute the notebooks in the order established inside the project_. The file with the final predictions will be saved as data/predictions/files_defects_predicted.csv

> _Check the explainability generated in notebooks/explainability folder_


## Getting help

For any doubt or issue, contact to bivianap@gmail.com
For future, teams channel or inbox will be created according to the demand


## Getting Involved

**Want to contribute?** Great! We try to make it easy, and all contributions, even the smaller ones, are more than welcome. This includes bug reports, fixes, documentation, examples...
But first, read our [Contribution Guide](./CONTRIBUTING.md).


## Releases

This project follows the [Semantic Versioning](https://semver.org/spec/v2.0.0.html) to release versions of
this repository. The [changelog](./CHANGELOG.md) file contains a curated, chronologically ordered list of notable
changes for each version of this project. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Realising a new version only requires to push a new tag following the `v[0-9]+.[0-9]+.[0-9]+` pattern
(e.g: `v0.1.0`, `v0.1.1`...).

The [publish-release.yml](.github/workflows/publish-release.yml) workflow manages the release life cycle based on the
commits pushed into the repository. Based on [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/#summary)
the workflow will create a new major release including new features (`feat:`),
or a minor release fixing issues (`fix:`). This workflow is based on [Release Please](https://github.com/googleapis/release-please)
to automate the creation of the release, including the update of the ChangeLog file.
