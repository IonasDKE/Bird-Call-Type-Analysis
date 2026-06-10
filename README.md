# Call Analytics Dashboard

## Overview

This project provides an interactive dashboard for analyzing bird vocalisation . The workflow consists of:

1. Preprocessing the raw data.
2. Enriching the metadata using a call type classifier.
3. Launching the dashboard for visualization and analysis.

## Project Structure

```text
project/
│
├── dashboard.py
├── utils.py
├── setup.ipynb
├── Call_Type_classifier.ipynb
│
├── preprocessed_data/
│   └── (generated files)
│
└── README.md
```

### File Descriptions

#### `dashboard.py`

Main application file that generates and runs the dashboard.

#### `utils.py`

Contains helper functions and utilities used by `dashboard.py`.

#### `setup.ipynb`

Notebook responsible for preprocessing the raw data. Running this notebook creates the processed datasets and saves them in the `preprocessed_data/` folder.

#### `Call_Type_classifier.ipynb`

Notebook containing the workflow for classifying call types and adding a new call type column to the metadata dataset.

## Running the Project

### Step 1: Preprocess the Data

Open and run all cells in:

```text
setup.ipynb
```

This notebook processes the raw data and creates the required files inside:

```text
preprocessed_data/
```

### Step 2: Generate Call Type Labels

Open and run all cells in:

```text
Call_Type_classifier.ipynb
```

This notebook classifies call types and adds the resulting call type column to the metadata dataset.

### Step 3: Launch the Dashboard

Run the dashboard application:

```bash
python dashboard.py
```

The dashboard will load the processed datasets from the `preprocessed_data/` directory and display the available analytics and visualizations.

## Workflow Summary

```text
Raw Data
    │
    ▼
setup.ipynb
    │
    ▼
preprocessed_data/
    │
    ▼
Call_Type_classifier.ipynb
    │
    ▼
Updated Metadata
    │
    ▼
dashboard.py
    │
    ▼
Interactive Dashboard
```

## Notes

* Ensure that `setup.ipynb` is executed before running the dashboard or that you already have the preprocessed_data folder.