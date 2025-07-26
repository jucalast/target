from fastapi import APIRouter

router = APIRouter()

@router.get("/analysis")
def get_analysis():
    return [{"id": 1, "result": "Sample analysis"}]
