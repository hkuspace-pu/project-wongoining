# A Machine Learning Approach for Identifying Psychological Triggers in Suspicious Emails

## Project Overview

This project develops a machine learning-based system for identifying psychological triggers in suspicious emails. Rather than acting as a first-layer phishing detector that simply determines whether an email is safe or unsafe, the system is designed as a second-stage awareness support tool. It analyses email text and predicts the psychological manipulation strategies used in the message, such as urgency, scarcity, authority, fear, social proof, reciprocity, and liking.

The purpose of the project is to support general email users, especially non-expert users, by helping them understand how suspicious emails attempt to influence their judgement. The final prototype presents trigger confidence scores, short explanations, and protective guidance through a Streamlit-based web interface.

## Project Artefacts

- Deployed Streamlit application: https://phishing-trigger-analyser.streamlit.app/
- Demonstration video: 
- Final report: included in the submitted ePortfolio package
- Poster: included in the submitted ePortfolio package

## Dataset Sources

The dataset was constructed from three publicly available sources:

1. monkey.org Phishing Archive  
   https://monkey.org/~jose/phishing/  
   Used archives from 2022, 2023, and 2024.

2. Hugging Face Phishing Dataset  
   https://huggingface.co/datasets/ealvaradob/phishing-dataset

3. University of Twente Phishing Validation Emails Dataset  
   https://research.utwente.nl/en/datasets/phishing-validation-emails-dataset/

The `.mbox` archives were converted into CSV format using a custom extraction pipeline. The following repository was referenced during early processing:

- mbox-to-csv: https://github.com/jarrodparkes/mbox-to-csv

## Dataset Preparation

The source datasets were standardised into a unified two-column format:

- `Email Text`
- `Email Type`

The preprocessing pipeline included:

- extraction of email body content from `.mbox` files
- conversion of HTML content to plain text
- whitespace normalisation
- URL removal
- email address removal
- domain artefact removal
- duplicate removal
- manual filtering of incomplete or out-of-scope records

The final clean dataset used for model training contained **977 phishing and scam emails**.

## Annotation Scheme

Each email was manually labelled using two dimensions.

### Email Type

The email type categories were:

- `Phishing Email`
- `Scam Email`
- `Marketing Spam`
- `Spam Other`

Only records labelled as `Phishing Email` or `Scam Email` were retained for final model training, because the project focuses on psychological manipulation within suspicious and deceptive email contexts.

### Psychological Trigger Labels

Each retained email was annotated using a multi-label format across seven psychological trigger categories:

- `Urgency`
- `Scarcity`
- `Authority`
- `Fear`
- `Social Proof`
- `Reciprocity`
- `Liking`

A single email may contain multiple triggers simultaneously.

## Model Development

The task was formulated as a multi-label text classification problem. The project compared several approaches:

- rule-based keyword matching
- traditional machine learning models using TF-IDF and One-vs-Rest classification
- DistilBERT
- RoBERTa

Five-fold MultilabelStratifiedKFold cross-validation was used as the primary evaluation method. Macro F1 was selected as the main metric due to class imbalance across the psychological trigger categories.

## Final Model

The final selected model was **RoBERTa original configuration, learning rate = 2e-5**.

It achieved the strongest cross-validated performance:

- Cross-validated Macro F1: **0.7388 ± 0.0105**

SVM also performed strongly as a traditional machine learning baseline, but RoBERTa was selected because it achieved stronger generalisation and was better aligned with the semantic nature of psychological trigger detection.

## Streamlit Prototype

The prototype allows users to input suspicious email text and receive:

- predicted psychological triggers
- per-trigger confidence scores
- short explanations of each detected trigger
- protective guidance for safer decision-making

The prototype is intended to support phishing awareness, not to replace enterprise email filtering systems or binary phishing classifiers.

## Installation and Local Execution

Clone the repository:

    git clone https://github.com/hkuspace-pu/project-wongoining.git
    cd project-wongoining

Install dependencies:

    pip install -r requirements.txt

Run the Streamlit application:

    streamlit run app.py

## Project Structure

    project-wongoining/
    │
    ├── app.py
    ├── requirements.txt
    ├── README.md
    ├── notebooks/
    ├── data/
    ├── models/
    └── outputs/

The exact folder structure may vary depending on the submitted version of the repository.

## Disclaimer

This prototype is developed for academic research and demonstration purposes. It should not be used as a standalone phishing detection or security decision system. Users should verify suspicious emails through official channels and avoid clicking untrusted links or opening unexpected attachments.
The deployed prototype loads the trained RoBERTa model for inference. The model repository is kept private during submission and is accessed by the deployment environment using a secure token.