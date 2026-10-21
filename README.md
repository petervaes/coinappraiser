# CoinAppraiser

CoinAppraiser is an API and command-line MVP for identifying coins from photos
and finding cited price references. The vision model identifies the coin; the
catalog retrieval step can only return prices that are actually present in a
catalog record. It does not invent missing prices or claim that a catalogue
price is a guaranteed sale value.

## Requirements

- Python 3.10+
- An OpenAI API key for photo identification
- A JSON price catalog, either local (the bundled empty catalog by default) or
  hosted at an HTTPS URL such as a GitHub raw-file URL

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Set `OPENAI_API_KEY` and, optionally, `OPENAI_MODEL` and
`COINAPPRAISER_CATALOG_URL` in the local `.env` file. The API and CLI load the
nearest `.env` file automatically and do not override environment variables
that are already set. Keep `.env` local; it is excluded from Git. Copy
`.env.example` to `.env` and edit the values locally:

```dotenv
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-4o-mini
COINAPPRAISER_CATALOG_URL=https://raw.githubusercontent.com/OWNER/REPO/BRANCH/catalog.json
```

The catalog URL must use HTTPS and return JSON in this format:

```json
{
  "records": [
    {
      "id": "numista-example",
      "title": "Example coin",
      "source": "numista",
      "url": "https://en.numista.com/",
      "country": "Example country",
      "denomination": "1 unit",
      "year": 1900,
      "mint": null,
      "metal": "silver",
      "grade": "VF",
      "price": 12.5,
      "currency": "EUR"
    }
  ]
}
```

Use one record per source, coin variant, grade, and price. `source` and `url`
identify the provenance; `price`, `currency`, and `grade` must reflect the
source record. Numista references sort ahead of Lefranc for otherwise equally
matching coins; values from different grade scales are kept separate and are
never averaged.

## Import reviewed source data

Reviewed per-coin source data lives in `catalog/sources/`. Rebuild the app's
catalog JSON after adding/editing source records:

```powershell
coinappraiser-import-catalog
```

The importer validates the source, HTTPS URL, currency, grade, and price, then
writes `catalog/catalog.json`. It does not scrape Numista or Lefranc. The
current `catalog/sources/fr-1-franc-morlon-1935.json` contains the Numista
values supplied for Franc 2014 #219/6 and the Lefranc F.219/6 grade quotations.
Numista shows EUR 12 (F), EUR 15 (VF), and EUR 19 (XF), with a mintage of
1,166,038. The source data does not provide Numista prices for the other
grades. Lefranc quotes EUR 10 (B), EUR 25 (TB), EUR 45 (TTB), EUR 120 (SUP),
EUR 300 (SPL), and EUR 500 (FDC); the e-FRANC page describes its quotations as
2017. These are source quotations, not condition-adjusted offers or guaranteed
sale prices. Source URLs are preserved on every record.

Do not put API keys or other secrets in source data or a public GitHub
repository.

## Run the API

```powershell
uvicorn coinappraiser.api:app --reload
```

Open `http://127.0.0.1:8000/docs` to use `POST /appraisals`. Upload the front
as `obverse` and the back as `reverse`; the reverse is optional. The app sends
both images together to the vision model. Existing clients can keep using the
single `image` field.
`GET /health` is a process health check and does not make external API calls.

The appraisal response puts `numista_value` first: when the coin identity and
photo-assessed Numista grade exactly match a catalog record, it contains that
grade's Numista price. `condition_assessment` reports the estimated grade,
visible wear, rationale, and confidence. If the grade is uncertain or no price
is cataloged for that exact grade, `numista_value` is `null` and
`numista_value_note` explains why. Lefranc prices remain separately listed in
`price_references`; their grade labels are not treated as interchangeable with
Numista grades.

## Run the CLI

```powershell
coinappraiser path\to\front.jpg --reverse path\to\back.jpg
```

The reverse image is optional, so `coinappraiser path\to\coin.jpg` still works.
The command prints the identification and matching price references as JSON.
Both the CLI and API use the same appraisal flow. The combined upload limit is
10 MiB.

## Scope and limitations

- Supported photo formats: JPEG, PNG, WebP, and GIF; maximum upload size:
  10 MiB.
- The initial retrieval uses structured catalog fields and is deliberately
  transparent rather than claiming semantic/vector search. A future RAG
  index can replace this retriever without changing the API response shape.
- Returned prices are references as listed by their source, not an appraisal
  or guaranteed current market value. Coin condition, authenticity, variant,
  and source date affect valuation and need explicit catalog coverage.
- Photo-based condition is a preliminary visual estimate, not professional
  grading. Glare, focus, angle, cleaning, damage, and missing edge views can
  affect it; use both sides and have valuable coins assessed in person.
- Lefranc/Numista content is not bundled. Populate the catalog only from data
  you are permitted to use, with source URLs and condition/currency details.
