---
language:
- th
license: apache-2.0
task_categories:
- automatic-speech-recognition
tags:
- audio
- speech-processing
- isan-dialect
pretty_name: Thai Dialect Isan Speech Corpus
size_categories:
- 10k<n<100k
dataset_info:
  features:
  - name: id
    dtype: string
  - name: audio
    struct:
    - name: array
      sequence: float32
    - name: path
      dtype: string
    - name: sampling_rate
      dtype: int64
  - name: raw
    dtype: string
  - name: thai_spelling
    dtype: string
  - name: isan_spelling
    dtype: string
  - name: name
    dtype: string
  - name: district
    dtype: string
  - name: province
    dtype: string
  - name: age
    dtype: string
  - name: gender
    dtype: string
  - name: question_id
    dtype: string
  - name: question
    dtype: string
  - name: duration
    dtype: float64
  splits:
  - name: train
    num_bytes: 19226874522
    num_examples: 9987
  - name: test
    num_bytes: 892537211
    num_examples: 500
  download_size: 8839972206
  dataset_size: 20119411733
configs:
- config_name: default
  data_files:
  - split: train
    path: data/train-*
  - split: test
    path: data/test-*
---

# Dataset Card for Thai Dialect Isan Speech Corpus

## Table of Contents
- [Dataset Description](#dataset-description)
- [Dataset Structure](#dataset-structure)
- [Data Statistics](#data-statistics)
- [Key Features](#key-features)
- [Usage](#usage)
- [Additional Information](#additional-information)

## Dataset Description

This dataset contains audio recordings of **Isan (Northeastern Thai)** speech, paired with rich transcriptions and demographic metadata. It is designed to support Automatic Speech Recognition (ASR), dialect study, and text normalization tasks for the Isan language.

The dataset features spontaneous responses to specific questions, covering two domains (General and Finance), recorded by speakers from different provinces in Northeastern Thailand.

- **Language:** Isan (Northeastern Thai)
- **Total Examples:** 10,487
- **Input:** Audio (WAV)
- **Output:** Transcriptions (Isan spelling, Thai spelling, and Raw annotated format)
- **License:** CC-BY-4.0

## Dataset Structure

### Data Splits

| Split | Examples |
| ----- | :------: |
| Train | 9,987    |
| Test  | 500      |

### Data Fields

Each data point contains the following fields:

- **id** (`string`): A unique identifier for the dataset entry.
- **audio** (`audio`): A dictionary containing the path to the audio file, the decoded audio array, and the sampling rate.
- **raw** (`string`): The raw transcription containing dialect-to-standard annotation tokens.
  - *Format:* `[Isan Word]<Standard Thai Word>`
  - *Example:* `"ข้อย[กะ]<ก็>บ่ค่อยมี[แฮง]<แรง>"`
- **thai_spelling** (`string`): The transcription normalized to Standard Thai spelling.
  - *Example:* `"ข้อยก็บ่ค่อยมีแรง"`
- **isan_spelling** (`string`): The transcription written in Isan spelling (phonetic to the dialect).
  - *Example:* `"ข้อยกะบ่ค่อยมีแฮง"`
- **name** (`string`): The original filename, often containing metadata codes (e.g., `opentyphoon;is;x_061;gen;0049.wav`).
- **district** (`string`): The district (Amphoe) where the speaker resides.
- **province** (`string`): The province (Changwat) where the speaker resides.
- **age** (`int`): The age of the speaker.
- **gender** (`string`): The gender of the speaker. Values include `"m"` (male), `"f"` (female), and `"x"` (not specified).
- **question_id** (`string`): The ID of the prompt question asked to the speaker.
- **question** (`string`): The text of the question asked to the speaker.
- **duration** (`float`): The duration of the audio clip in seconds.

## Key Features

### 1. Rich Annotation Format
The `raw` field provides a unique mapping between Isan dialect and Standard Thai. This is valuable for dialect normalization and translation tasks.
- **Format:** `[dialect spelling]<standard Thai spelling>`
- **Example:** `[เฮา]<เรา>` indicates the speaker said "hao" (Isan) which corresponds to "rao" (Thai for "We/Us").

### 2. Demographic Diversity
The dataset includes speakers from multiple key provinces in the Isan region, allowing for analysis of regional accent variations. Provinces include:
- Khon Kaen
- Udon Thani
- Ubon Ratchathani
- Chaiyaphum
- Roi Et
- Maha Sarakham
- Kalasin
- Nong Bua Lam Phu
- Beung Kan

### 3. Prompted Speech
Recordings are responses to specific questions (found in the `question` field), providing context for the speech. This helps in analyzing semantic understanding and sentiment in the local dialect.

## Usage

### Loading the Dataset

```python
from datasets import load_dataset
import IPython.display as ipd

# Load the dataset
dataset = load_dataset("scb10x/thai-dialect-isan-dataset")

# Select a sample
example = dataset['train'][0]

# Print transcriptions
print(f"Transcript (Isan): {example['isan_spelling']}")
print(f"Transcript (Thai): {example['thai_spelling']}")

# Listen to audio
ipd.Audio(example['audio']['array'], rate=example['audio']['sampling_rate'])