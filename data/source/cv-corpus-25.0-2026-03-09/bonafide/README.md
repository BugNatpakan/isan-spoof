# *ไทย* &mdash; Thai (`th`)

This datasheet is for cv-corpus-25.0-2026-03-09 of the Mozilla Common Voice *Scripted Speech* dataset for Thai [ไทย - `th`]. The dataset contains 366508 clips representing 426.9 hours of recorded speech (173.27 hours validated) from 7987 speakers, recorded from a text corpus of 186,192 sentences.

## Language

### Accents

| Code | Accent | Clips | Speakers |
|---|---|---|---|
| - |  | 10,720 (2.9%) | 59 (0.7%) |

## Demographic information

The dataset includes the following self-declared age and gender distributions. A coverage summary is shown below each table.

### Gender

Self-declared gender information. The table shows clip and speaker counts with percentages. Speakers who did not declare a gender are listed as Unspecified. A dash (-) indicates zero.

| Code | Gender | Clips | Speakers |
|---|---|---|---|
| male_masculine | Male, masculine | 154,100 (42.0%) | 642 (8.0%) |
| female_feminine | Female, feminine | 61,443 (16.8%) | 573 (7.2%) |
| transgender | Transgender | 20 (0.0%) | 1 (0.0%) |
| non-binary | Non-binary | - | - |
| do_not_wish_to_say | Prefer not to say | 5 (0.0%) | 1 (0.0%) |
| - | Unspecified | 150,940 (41.2%) | 7,500 (93.9%) |

*Gender declared: 215,568 of 366,508 clips (58.8%), 487 of 7,987 speakers (6.1%)*

### Age

Self-declared age information. The table shows clip and speaker counts with percentages. Speakers who did not declare an age are listed as Unspecified. A dash (-) indicates zero.

| Code | Age | Clips | Speakers |
|---|---|---|---|
| teens | Teens | 15,326 (4.2%) | 229 (2.9%) |
| twenties | Twenties | 89,695 (24.5%) | 737 (9.2%) |
| thirties | Thirties | 27,071 (7.4%) | 225 (2.8%) |
| fourties | Fourties | 14,221 (3.9%) | 83 (1.0%) |
| fifties | Fifties | 73,141 (20.0%) | 22 (0.3%) |
| sixties | Sixties | 80 (0.0%) | 1 (0.0%) |
| seventies | Seventies | - | - |
| eighties | Eighties | 84 (0.0%) | 1 (0.0%) |
| nineties | Nineties | - | - |
| - | Unspecified | 146,890 (40.1%) | 7,469 (93.5%) |

*Age declared: 219,618 of 366,508 clips (59.9%), 518 of 7,987 speakers (6.5%)*

## Data splits for modelling

**Clip buckets**

| Bucket | Clips |
|---|---|
| Validated | 148,765 (40.6%) |
| Invalidated | 9,360 (2.6%) |
| Other | 208,383 (56.9%) |

**Training splits**

| Split | Clips |
|---|---|
| Train | 32,977 (22.2%) |
| Dev | 11,059 (7.4%) |
| Test | 11,059 (7.4%) |

*Training split coverage: 55,095 of 148,765 validated clips (37.0%)*

The dataset contains 148765 validated, 9360 invalidated, and 208383 unresolved clips. The average clip duration is 4.193 seconds.

## Text corpus

**Validated sentences:** 64,491

| Category | Count |
|---|---|
| Unvalidated sentences | 121,701 |
| Pending sentences | 121,534 |
| Rejected sentences | 167 |
| Reported sentences | 4,312 |

The corpus contains 186,192 sentences: 64,491 validated and 121,701 unvalidated (121,534 pending review, 167 rejected), with 4,312 reported for review.

### Sample

There follows a randomly selected sample of five sentences from the corpus.

1. *กรุณาใส่ยากลับเข้าไปในกล่องที่สอดคล้องกันหลังการใช้งาน*
2. *ใช่ สัตว์ประหลาดนั่นแหละ ถ้ามีใครรู้ว่าจะพบตัวมันที่ไหน*
3. *ฉัน ไม่เคยเดิมพันถึงครึ่งเลย ! คนอื่นกล่าวขึ้น*
4. *ยามเขาเดินผ่านบ้านขณะที่ครอบครัวออตโตไม่อยู่*
5. *การมีบ้านและห้องของตัวเอง*

### Sources

| Source | Sentences |
|---|---|
| sentence-collector | 63,597 (98.6%) |
| Other | 894 (1.4%) |

### Fields

#### Clips

Each row of a `tsv` file represents a single audio clip, and contains the following information:

- `client_id` - hashed UUID of a given user
- `path` - relative path of the audio file
- `text` - supposed transcription of the audio
- `up_votes` - number of people who said audio matches the text
- `down_votes` - number of people who said audio does not match text
- `age` - age of the speaker[^1]
- `gender` - gender of the speaker[^1]
- `accents` - accents of the speaker[^1]
- `variant` - variant of the language[^1]
- `segment` - if sentence belongs to a custom dataset segment, it will be listed here
- `prompt_upvotes` - number of upvotes the sentence prompt received
- `prompt_reports` - number of reports the sentence prompt received
- `is_edited` - whether the clip's transcription has been edited

[^1]: For a full list of age, gender, and accent options, see the [demographics spec](https://github.com/common-voice/common-voice/blob/main/web/src/stores/demographics.ts). These will only be reported if the speaker opted in to provide that information.

#### `validated_sentences.tsv`

The `validated_sentences.tsv` file contains one row per validated sentence in the text corpus:

- `sentence_id` - unique identifier for the sentence
- `sentence` - the sentence text
- `variant` - the variant of the language
- `sentence_domain` - the domain(s) the sentence belongs to
- `source` - the source the sentence was collected from
- `is_used` - whether the sentence is still in circulation for recording
- `clips_count` - number of clips recorded for this sentence

#### `unvalidated_sentences.tsv`

The `unvalidated_sentences.tsv` file contains one row per unvalidated sentence in the text corpus:

- `sentence_id` - unique identifier for the sentence
- `sentence` - the sentence text
- `variant` - the variant of the language
- `sentence_domain` - the domain(s) the sentence belongs to
- `source` - the source the sentence was collected from
- `up_votes` - number of upvotes the sentence received
- `down_votes` - number of downvotes the sentence received
- `status` - current status of the sentence (`pending` or `rejected`)

## Get involved

### Community links

- [Common Voice translators on Pontoon](https://pontoon.mozilla.org/th/common-voice/contributors/)
- [Common Voice Communities](https://github.com/common-voice/common-voice/blob/main/docs/COMMUNITIES.md)

### Discussions

- [Common Voice on Matrix](https://chat.mozilla.org/#/room/#common-voice:mozilla.org)
- [Common Voice on Discourse](https://discourse.mozilla.org/t/about-common-voice-readme-first/17218)
- [Common Voice on Discord](https://discord.gg/9QTj9zwn)
- [Common Voice on Telegram](https://t.me/mozilla_common_voice)

### Contribute

- [Speak](https://commonvoice.mozilla.org/th/speak)
- [Write](https://commonvoice.mozilla.org/th/write)
- [Listen](https://commonvoice.mozilla.org/th/listen)
- [Review](https://commonvoice.mozilla.org/th/review)

## Licence

This dataset is released under the [Creative Commons Zero (CC-0)](https://creativecommons.org/public-domain/cc0/) licence. By downloading this data you agree to not determine the identity of speakers in the dataset.
