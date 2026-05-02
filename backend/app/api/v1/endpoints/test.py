from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/test", tags=["test"])
@router.get("/t")
async def get_recipe():
    try:
        return {"test": "success"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))