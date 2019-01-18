# WikiCleaner

WikiCleaner is a simple script for extracting plain texts from Wikipedia articles, preserving hyperlink information.

## Dependencies

- joblib
- logzero
- tqdm

## Output format

**Note:** the actual output file is in JSON Lines format, where each line contains an object for an article.

Each output object is a Cirrussearch object extended with `sections` object.
`sections` is a tuple of heading name(s) and its processed body text.
Hyperlinks in the original text are replaced with `/(<link destination>/<anchor text>)/`.

```
{
  "title": "Éclair",
  "pageid": 1980219,
  "wikidata_id": "Q273426",
  ...,
  "sections": [
    [
      [],
      "An éclair is an oblong /(Pastry/pastry)/ made with /(Choux pastry/choux)/ dough filled with a cream and topped with chocolate icing. The /(Dough/dough)/,
which is the same as that used for /(Profiterole/profiterole)/, is typically piped into an oblong shape with a /(Pastry bag/pastry bag)/ and baked until it is cr
isp and hollow inside. Once cool, the pastry is then filled with a vanilla-, coffee- or chocolate-flavoured /(Custard/custard)/ (crème pâtissière), or with /(Whi
pped cream/whipped cream)/, or /(Chiboust cream/chiboust cream)/; and then iced with /(Fondant icing/fondant)/ icing."
    ],
    [
      [
        "Etymology"
      ],
      "The word comes from French éclair 'flash of lightning', so named because it is eaten quickly (in a flash)."
    ],
    ...,
    [
      [
        "External links"
      ],
      "A brief éclair history"
    ]
  ]
}
```

## Usage

1. Download a Wikipedia Cirrussearch dump file from [here](https://dumps.wikimedia.org/other/cirrussearch/).
    - You'll need a dump file which has a name like `XXwiki-YYYYMMDD-cirrussearch-content.json.gz`

2. Extract article information from the downloaded dump file

```
$ python extract_articles.py enwiki-20180903-cirrussearch-content.json.gz enwiki-20180903-articles.pickle
```

3. Process article texts and output in JSON format

```
$ zcat enwiki-20180903-cirrussearch-content.json.gz|python clean.py - - enwiki-20180903-articles.pickle > enwiki-20180903-clean.json
```

If you're processing an non-English version of Wikipedia, it is required to specify alias names for `File` (namsespace: 6) and `Category` (namespace: 14) in Wikipedia so that links to files and categories are correctly recognized.
    ```
    $ zcat jawiki-20180903-cirrussearch-content.json.gz|python clean.py - - jawiki-20180903-articles.pickle --ns6 ファイル 画像 --ns14 カテゴリ > jawiki-20180903-clean.json
    ```
