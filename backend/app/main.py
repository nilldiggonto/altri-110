from fastapi import FastAPI

app = FastAPI(title="altri API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
