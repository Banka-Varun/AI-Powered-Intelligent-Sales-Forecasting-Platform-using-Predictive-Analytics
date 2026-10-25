# SalesGenie: Milestone 1 backend

Start here. This is a separate, clean backend deliverable based on the setup and task plan supplied in chat. Extract it into a NEW folder; do not overwrite your original project or its `.env`. It does not contain anyone's API keys or database password.

## What this delivers

Working FastAPI lead management: create, list/search/filter, read, edit, delete, CSV import, email duplicate protection, validation and persistence. `/docs` is an interactive testing page, not the product frontend.

This is the backend portion of Milestone 1, NOT the complete team milestone. AI/company analysis, lead-intelligence scoring and Streamlit UI belong to other workstreams and are not implemented here. No Gemini subscription or key is needed to run these lead APIs.

The lead fields and stages are provisional because no agreed API contract or database schema was supplied. Ask the team to approve them before merging. This does not implement the full eight-table project schema.

## Your stack, in plain language

| Tool | Purpose |
|---|---|
| Python 3.10+ | Language for backend code |
| FastAPI | Receives API requests and supplies `/docs` |
| Pydantic | Validates names, email addresses and stages |
| SQLAlchemy | Reads and writes database records |
| PostgreSQL with psycopg | Stores the real application data |
| Uvicorn | Runs the API server |
| Pytest and HTTPX | Check API behaviour automatically |

JWT and role-based access control are NOT implemented. This is a local learning/demo version. Use the provided localhost command; do not expose it publicly until authentication and authorization are added with the team. `create_all` creates missing tables but does not migrate existing tables.

## Run on Windows using CMD

1. Extract the ZIP to a new folder. Open that folder in File Explorer, click its address bar, type `cmd`, press Enter. Make sure `dir` shows `requirements.txt`.
2. Run these commands one at a time:

```bat
python --version
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
copy .env.example .env
notepad .env
```

3. In `.env`, set `DB_PASSWORD` to your local PostgreSQL password. Keep `DB_USER`, `DB_NAME`, host and port consistent with pgAdmin. If your password contains `#` or spaces, enclose the value in double quotes. Never commit `.env`.
4. In pgAdmin, connect to your local PostgreSQL server. If `salesgenie` does not exist, right-click Databases, select Create > Database, enter `salesgenie` and save. If it exists already, reuse it only if its `leads` table matches this schema; otherwise use a separate database such as `salesgenie_backend_demo` and change `DB_NAME` accordingly. Do not delete existing team tables.
5. Start the server:

```bat
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

6. Keep that terminal open. Open http://127.0.0.1:8000/docs in your browser. Stop the server with Ctrl+C.

### If PostgreSQL setup blocks practice

For practice ONLY, add this line to `.env`:

```text
DATABASE_URL=sqlite:///./practice.db
```

This creates a local SQLite file automatically. It is not PostgreSQL; describe it honestly in a demo. Remove the line to return to PostgreSQL. Data does not transfer between the two databases automatically.

## Your first demonstration

1. In `/docs`, open `GET /health`, click Try it out, then Execute. Expect `database: connected`.
2. Open `POST /leads`, click Try it out, and replace the example with:

```json
{"name":"Varun Demo","email":"varun@example.com","company":"Demo Stores","phone":null,"stage":"new"}
```

3. Execute. Expect HTTP 201 and an `id`. Note that ID.
4. Execute `GET /leads`. Your saved lead should appear in `items`.
5. Use `PATCH /leads/{lead_id}` with that ID and `{"stage":"qualified"}`. Expect the changed stage.
6. Repeat the same POST. Expect 409 for duplicate email. Uppercase versions of the same email also count as duplicates.
7. Use `POST /leads/import` to upload `sample_leads.csv`. In an otherwise empty database (or one with only the Varun Demo lead), expect 2 imported, 1 duplicate and 1 rejected. Uploading it again imports 0 because the valid emails already exist.
8. Restart the server and list leads again to show persistence. Show the same records in pgAdmin if using PostgreSQL.
9. Delete your demo lead by ID if desired. Expect 204 with no response body.

## Understand the code before evaluation

- `main.py` creates the app.
- `backend/schemas.py` defines accepted request fields. Bad data produces 422 before database writes.
- `backend/app.py` receives requests, uses a database session, commits changes and returns responses.
- `backend/models.py` defines the lead table and unique email constraint.
- `backend/database.py` reads local settings and connects to the selected database.
- `tests/test_leads.py` exercises complete HTTP requests against an isolated test database.

Example flow: frontend sends POST /leads -> Pydantic checks the data -> SQLAlchemy inserts a lead -> database commits -> FastAPI returns the saved record. A failed duplicate update rolls back rather than partly changing the record.

## Run tests

```bat
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Tests use temporary SQLite databases and do not touch your PostgreSQL records. See `TEST_RESULTS.md` for what was actually verified during preparation. Check `/health` and the demo steps on YOUR PostgreSQL instance before claiming that integration works.

## Personal repository and group repository

You develop the feature ONCE. Your personal repo records your work. The group repo receives the same feature through a branch/PR after the team agrees on folder layout and fields. Keep the team's shared repo as the authoritative integrated project after that.

For the FIRST upload to your personal repo, upload this project's source files, including the `backend`, `tests`, and `docs` folders, `main.py`, requirements files, sample CSV, README, `.gitignore` and `.env.example`. Do not upload the ZIP as your source code. Do not upload `.env`, `venv`, `practice.db`, caches or your original connection script containing a password.

If the personal repo already has code, use a branch and inspect the differences before replacing files. You can use a separate local folder for this deliverable. Do not run `git init` inside another repository or overwrite its `.git` folder.

For the group repo:

1. Clone the group repo to a separate folder, or pull its latest main branch if already cloned and clean.
2. Create a branch such as `varun/milestone1-backend`.
3. Agree on where this backend belongs. The supplied import paths assume `backend` and `main.py` are in the project root. If the group already has those names, integrate into their structure rather than copying over them blindly.
4. Add only your agreed source changes. Review `git diff` and `git status`; check that no credentials are staged.
5. Commit an accurate message, push the branch and open a pull request. Describe features, tests, provisional fields and the missing auth/AI integration.
6. Ask a teammate to review. Once merged, others pull the updated project.

No repository was changed or pushed by this package. Exact commands depend on your existing repositories and branches. Keep genuine commits as you understand, test and adapt the work; do not backdate commits or claim unperformed work.

## Coordination and evaluation

Send Vaishnavi `docs/API_CONTRACT.md`. She can call these routes from Streamlit while you run the backend. Each teammate can run a local copy; `127.0.0.1` always means their own computer, not yours. A future shared deployment needs authentication and agreed hosting.

Ask the database owner to approve the table/fields and introduce migrations. Ask Rani how her analysis function accepts and returns lead data. No AI endpoints are faked in this deliverable. Ask Vinay to run the test suite and demo cases.

For your individual evidence, keep a working demo, your actual commits/PR, test output and a short explanation of the request-to-database flow. State exactly what you implemented, tested, adapted and still need to integrate. Follow the mentor's rules on assistance and attribution. Individual marking does not automatically require you to build all six modules.

## Common errors

- Connection refused: start PostgreSQL and check host/port in `.env`.
- Database does not exist: create the named database in pgAdmin.
- Password authentication failed: correct the local credentials; never paste them into a public Issue.
- Port 8000 in use: stop your earlier server, or use `--port 8001` and open that port's `/docs`.
- Module not found: activate the venv and install requirements from this folder.
- Existing table differs: use a separate demo database or agree on a migration. Restarting does not alter existing columns.

Official references: https://fastapi.tiangolo.com/tutorial/sql-databases/ and https://fastapi.tiangolo.com/tutorial/request-files/.
