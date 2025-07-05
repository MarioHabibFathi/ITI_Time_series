from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from src.eda import TimeSeriesEDA
from src.file_ops import save_dataset, increment_filename, DATA_DIR, delete_dataset, rename_dataset, file_size_limit
import io
from monitoring.metrics import start_metrics_collection
import logging
from prometheus_fastapi_instrumentator import Instrumentator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app)

@app.on_event("startup")
def startup_event():
    start_metrics_collection()

@app.get("/health")
def health_check():
    return {"status": "OK"}



@app.post("/eda/basic")
async def eda_basic(file: UploadFile = File(...)):
    content = await file.read()
    eda = TimeSeriesEDA(content, file.filename)
    return eda.basic_info()

@app.post("/eda/suggest-cast")
async def suggest_cast(file: UploadFile = File(...), column: str = Form(...)):
    content = await file.read()
    eda = TimeSeriesEDA(content, file.filename)
    return {"suggested_type": eda.suggest_cast_type(column)}

@app.post("/eda/try-cast")
async def try_cast(file: UploadFile = File(...), column: str = Form(...), dtype: str = Form(...)):
    content = await file.read()
    eda = TimeSeriesEDA(content, file.filename)
    return eda.try_cast_column(column, dtype)

@app.post("/eda/drop-non-convertible")
async def drop_non_convertible(file: UploadFile = File(...), column: str = Form(...), dtype: str = Form(...)):
    content = await file.read()
    eda = TimeSeriesEDA(content, file.filename)
    return eda.drop_non_convertible_rows(column, dtype)

@app.post("/eda/preview-resample")
async def preview_resample(file: UploadFile = File(...), datetime_col: str = Form(...), freq: str = Form(...)):
    content = await file.read()
    eda = TimeSeriesEDA(content, file.filename)
    return eda.preview_resample(datetime_col, freq)

@app.post("/eda/seasonal-decompose")
async def seasonal_decompose(file: UploadFile = File(...), datetime_col: str = Form(...), target_col: str = Form(...), freq: int = Form(...)):
    content = await file.read()
    eda = TimeSeriesEDA(content, file.filename)
    img_base64 = eda.seasonal_decomposition(datetime_col, target_col, freq)
    return {"image_base64": img_base64}

@app.post("/eda/download-cleaned")
async def download_cleaned(file: UploadFile = File(...)):
    content = await file.read()
    eda = TimeSeriesEDA(content, file.filename)
    csv_bytes = eda.save_cleaned_csv()
    return StreamingResponse(io.BytesIO(csv_bytes), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={file.filename}"})

@app.post("/eda/schema")
async def schema_overview(file: UploadFile = File(...)):
    content = await file.read()
    eda = TimeSeriesEDA(content, file.filename)
    return eda.schema_overview()

@app.post("/eda/suggest-types")
async def suggest_types(file: UploadFile = File(...)):
    content = await file.read()
    eda = TimeSeriesEDA(content, file.filename)
    return eda.suggest_types_for_all()

@app.post("/eda/column-nulls")
async def column_nulls(file: UploadFile = File(...), column: str = Form(...)):
    content = await file.read()
    eda = TimeSeriesEDA(content, file.filename)
    return eda.column_nulls(column)

@app.post("/eda/drop-column")
async def drop_column(file: UploadFile = File(...), column: str = Form(...)):
    content = await file.read()
    eda = TimeSeriesEDA(content, file.filename)
    return eda.drop_column(column)

@app.post("/eda/drop-rows-with-null")
async def drop_rows_with_null(file: UploadFile = File(...), column: str = Form(...)):
    content = await file.read()
    eda = TimeSeriesEDA(content, file.filename)
    return eda.drop_rows_with_null(column)

@app.post("/upload/check_file")
async def check_file(filename: str = Form(...)):
    file_path = DATA_DIR / filename
    return {
        "exists": file_path.exists(),
        "suggested_increment": str(increment_filename(file_path).name) if file_path.exists() else filename
    }


@app.post("/upload/save_file")
async def upload_file(file: UploadFile = File(...), filename: str = Form(...), mode: str = Form("error")):
    try:
        save_dataset(file.file, filename, mode=mode)
        return {"status": "success", "filename": filename}
    except FileExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload/increment_name")
async def get_incremented_filename(filename: str = Form(...)):
    file_path = DATA_DIR / filename
    if file_path.exists():
        return {"new_name": str(increment_filename(file_path).name)}
    else:
        return {"new_name": filename}
    
@app.get("/datasets/list")
async def list_datasets():
    files = [f.name for f in DATA_DIR.glob("*.csv")]
    return JSONResponse(content={"datasets": files})

@app.delete("/datasets/delete")
async def delete_file(filename: str = Form(...)):
    logger.info(f"Delete requested for '{filename}'")
    try:
        delete_dataset(filename)
        return {"status": "deleted", "filename": filename}
    except FileNotFoundError as e:
        logger.warning(str(e))
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/datasets/rename")
async def rename_file(old_filename: str = Form(...), new_filename: str = Form(...)):
    logger.info(f"Rename '{old_filename}' → '{new_filename}'")
    try:
        rename_dataset(old_filename, new_filename)
        return {"status": "renamed", "from": old_filename, "to": new_filename}
    except (FileNotFoundError, FileExistsError) as e:
        logger.warning(str(e))
        raise HTTPException(status_code=409, detail=str(e))

@app.post("/upload/validate-size")
async def validate_file_size(file: UploadFile = File(...), max_mb: int = Form(10)):
    try:
        file_size_limit(file, max_mb=max_mb)
        return {"status": "valid"}
    except ValueError as e:
        logger.warning(str(e))
        raise HTTPException(status_code=413, detail=str(e))
