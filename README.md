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
source record. The included catalog has no records, so it will correctly
return no price references until real, appropriately licensed catalog data is
added. Do not put API keys or other secrets in the catalog or a public GitHub
repository.

## Run the API

```powershell
uvicorn coinappraiser.api:app --reload
```

Open `http://127.0.0.1:8000/docs` to use `POST /appraisals` with a coin photo.
`GET /health` is a process health check and does not make external API calls.

## Run the CLI

```powershell
coinappraiser path\to\coin.jpg
```

The command prints the identification and matching price references as JSON.
Both the CLI and API use the same appraisal flow.

## Scope and limitations

- Supported photo formats: JPEG, PNG, WebP, and GIF; maximum upload size:
  10 MiB.
- The initial retrieval uses structured catalog fields and is deliberately
  transparent rather than claiming semantic/vector search. A future RAG
  index can replace this retriever without changing the API response shape.
- Returned prices are references as listed by their source, not an appraisal
  or guaranteed current market value. Coin condition, authenticity, variant,
  and source date affect valuation and need explicit catalog coverage.
- Lefranc/Numista content is not bundled. Populate the catalog only from data
  you are permitted to use, with source URLs and condition/currency details.
