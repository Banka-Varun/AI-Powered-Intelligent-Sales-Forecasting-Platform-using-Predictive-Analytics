from contextlib import asynccontextmanager
import csv
import io
import logging
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
from fastapi import Depends, FastAPI, HTTPException, Query, Response, UploadFile
from pydantic import ValidationError
from sqlalchemy import func, or_, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from backend.database import Base, configured_url, make_engine
from backend.models import Lead
from backend.schemas import ImportResult, LeadCreate, LeadPage, LeadRead, LeadUpdate, Stage

logger = logging.getLogger(__name__)
MAX_BYTES = 2 * 1024 * 1024
MAX_ROWS = 1000


def create_app(database_url=None):
    engine = make_engine(
        database_url if database_url is not None else configured_url()
    )

    @asynccontextmanager
    async def lifespan(app):
        try:
            Base.metadata.create_all(engine)
        except SQLAlchemyError:
            raise RuntimeError(
                "Database unavailable. Check .env and your database."
            ) from None

        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(
        title="SalesGenie Lead Management API",
        version="0.1.0",
        lifespan=lifespan,
        description="SalesGenie API for lead management, CSV import, and customer data validation.",
        docs_url=None,
    )

    @app.get("/docs", include_in_schema=False)
    def custom_docs():
        page = get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title="SalesGenie API",
            swagger_ui_parameters={"defaultModelsExpandDepth": -1},
        )
        html = page.body.decode("utf-8")
        css = """
        <style>
            .swagger-ui a[href$="/openapi.json"] {
                display: none !important;
            }
        </style>
        """
        return HTMLResponse(html.replace("</head>", css + "</head>"))


    def get_db():
        with Session(engine) as session:
            yield session

    @app.exception_handler(SQLAlchemyError)
    async def database_error(request, exc):
        from fastapi.responses import JSONResponse
       
        logger.error('Database operation failed: %s', type(exc).__name__)
        return JSONResponse(status_code=503, content={'detail': 'Database operation failed. Check the database connection.'})

    def commit(db):
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(409, 'Email already exists or a database constraint was violated.') from None

    def find_lead(db, lead_id):
        lead = db.get(Lead, lead_id)
        if lead is None:
            raise HTTPException(404, 'Lead not found.')
        return lead

    @app.get('/health', tags=['Health'])
    def health(db: Session = Depends(get_db)):
        db.execute(text('SELECT 1'))
        return {'status': 'ok', 'database': 'connected'}

    @app.post('/leads', response_model=LeadRead, status_code=201, tags=['Leads'])
    def add_lead(data: LeadCreate, db: Session = Depends(get_db)):
        lead = Lead(**data.model_dump())
        db.add(lead)
        commit(db)
        db.refresh(lead)
        return lead

    @app.get('/leads', response_model=LeadPage, tags=['Leads'])
    def list_leads(q: str | None = Query(None, max_length=120), stage: Stage | None = None,
                   offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
                   db: Session = Depends(get_db)):
        filters = []
        if q and q.strip():
            term = q.strip().lower()
            filters.append(or_(*(func.lower(column).contains(term, autoescape=True)
                                 for column in (Lead.name, Lead.email, Lead.company))))
        if stage:
            filters.append(Lead.stage == stage)
        total = db.scalar(select(func.count()).select_from(Lead).where(*filters))
        items = db.scalars(select(Lead).where(*filters).order_by(Lead.id).offset(offset).limit(limit)).all()
        return {'items': items, 'total': total, 'offset': offset, 'limit': limit}

    @app.post('/leads/import', response_model=ImportResult, tags=['Leads'])
    def import_csv(file: UploadFile, db: Session = Depends(get_db)):
        """Valid rows are saved together. Invalid/duplicate rows are reported and skipped."""
        try:
            raw = file.file.read(MAX_BYTES + 1)
        finally:
            file.file.close()
        if len(raw) > MAX_BYTES:
            raise HTTPException(413, 'CSV must be no larger than 2 MiB.')
        try:
            reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')), strict=True)
            headers = reader.fieldnames
            allowed = {'name', 'email', 'company', 'phone', 'stage'}
            if (not headers or len(set(headers)) != len(headers)
                    or not {'name', 'email', 'company'} <= set(headers)
                    or not set(headers) <= allowed):
                raise HTTPException(400, 'CSV needs unique headers name,email,company; optional phone,stage only.')
            rows = []
            for row in reader:
                rows.append(row)
                if len(rows) > MAX_ROWS:
                    raise HTTPException(413, 'CSV must contain at most 1000 data rows.')
        except (UnicodeDecodeError, csv.Error):
            raise HTTPException(400, 'CSV must be valid UTF-8 CSV.') from None
        if not rows:
            raise HTTPException(400, 'CSV has no data rows.')

        result = {'imported': 0, 'duplicates': 0, 'rejected': 0, 'issues': []}
        seen = set()
        for number, row in enumerate(rows, start=2):
            if None in row or any(value is None for value in row.values()):
                result['rejected'] += 1
                result['issues'].append({'row': number, 'reason': 'Wrong number of columns.'})
                continue
            if not row.get('stage', '').strip():
                row.pop('stage', None)
            if not row.get('phone', '').strip():
                row['phone'] = None
            try:
                data = LeadCreate.model_validate(row)
            except ValidationError as exc:
                result['rejected'] += 1
                fields = ', '.join(str(e['loc'][0]) for e in exc.errors())
                result['issues'].append({'row': number, 'reason': f'Invalid fields: {fields}.'})
                continue
            email = str(data.email)
            if email in seen or db.scalar(select(Lead.id).where(Lead.email == email).execution_options(autoflush=False)) is not None:
                result['duplicates'] += 1
                result['issues'].append({'row': number, 'reason': 'Duplicate email.'})
                continue
            seen.add(email)
            # Defer flush until commit so a concurrent duplicate rolls back this batch cleanly.
            with db.no_autoflush:
                db.add(Lead(**data.model_dump()))
            result['imported'] += 1
        commit(db)
        return result

    @app.get('/leads/{lead_id}', response_model=LeadRead, tags=['Leads'])
    def get_lead(lead_id: int, db: Session = Depends(get_db)):
        return find_lead(db, lead_id)

    @app.patch('/leads/{lead_id}', response_model=LeadRead, tags=['Leads'])
    def update_lead(lead_id: int, data: LeadUpdate, db: Session = Depends(get_db)):
        lead = find_lead(db, lead_id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(lead, key, value)
        commit(db)
        db.refresh(lead)
        return lead

    @app.delete('/leads/{lead_id}', status_code=204, tags=['Leads'])
    def delete_lead(lead_id: int, db: Session = Depends(get_db)):
        db.delete(find_lead(db, lead_id))
        commit(db)
        return Response(status_code=204)

    return app
