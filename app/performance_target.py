from fastapi import FastAPI


app = FastAPI(title="TestForge Performance Target")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "testforge"}


@app.get("/products")
def products() -> dict[str, object]:
    items = [
        {"id": 1, "name": "Backpack"},
        {"id": 2, "name": "Bike Light"},
        {"id": 3, "name": "T-Shirt"},
    ]
    return {"items": items, "count": len(items)}
