"""Product Type API endpoints - Machine Learning based product type classification"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.services.product_type_learning_service import ProductTypeLearningService
from app.models.product_type_pattern import ProductTypePattern

router = APIRouter()


# Pydantic models
class ProductTypeLearnRequest(BaseModel):
    product_name: str
    product_type: str
    source: str = 'manual'  # 'manual' or 'auto'


class ProductTypePredictRequest(BaseModel):
    product_name: str


class ProductTypePredictResponse(BaseModel):
    product_type: Optional[str]
    confidence: Optional[float]
    detection_method: Optional[str]


class ProductTypePatternResponse(BaseModel):
    id: int
    pattern: str
    product_type: str
    confidence: float
    source: str
    usage_count: int

    class Config:
        from_attributes = True


class ProductTypeStatisticsResponse(BaseModel):
    total_patterns: int
    manual_patterns: int
    auto_patterns: int
    total_usage: int


@router.post("/learn", status_code=status.HTTP_201_CREATED)
async def learn_product_type(
    request: ProductTypeLearnRequest,
    db: Session = Depends(get_db)
):
    """
    商品タイプのパターンを学習

    ユーザーが手動で変更した商品タイプを学習します。
    次回のインポート時に、同じパターンの商品名があれば自動的に商品タイプを適用します。

    例:
    ```json
    {
      "product_name": "手帳型カバー/mirror(刺繍風プリント)",
      "product_type": "手帳型カバー",
      "source": "manual"
    }
    ```
    """
    try:
        learning_service = ProductTypeLearningService(db)
        pattern = learning_service.learn_from_product_name(
            product_name=request.product_name,
            product_type=request.product_type,
            source=request.source
        )

        return {
            "success": True,
            "message": f"Pattern learned: {pattern.pattern} → {pattern.product_type}",
            "pattern": ProductTypePatternResponse.from_orm(pattern)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to learn product type: {str(e)}"
        )


@router.post("/predict", response_model=ProductTypePredictResponse)
async def predict_product_type(
    request: ProductTypePredictRequest,
    db: Session = Depends(get_db)
):
    """
    商品名から商品タイプを予測

    学習済みのパターンを使用して、商品名から商品タイプを予測します。

    例:
    ```json
    {
      "product_name": "手帳型カバー/rose(ローズ柄)"
    }
    ```

    レスポンス:
    ```json
    {
      "product_type": "手帳型カバー",
      "confidence": 0.95,
      "detection_method": "ml_manual"
    }
    ```
    """
    try:
        learning_service = ProductTypeLearningService(db)
        result = learning_service.predict_product_type(request.product_name)

        if result:
            product_type, confidence, method = result
            return ProductTypePredictResponse(
                product_type=product_type,
                confidence=confidence,
                detection_method=method
            )
        else:
            return ProductTypePredictResponse(
                product_type=None,
                confidence=None,
                detection_method=None
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to predict product type: {str(e)}"
        )


@router.get("/patterns", response_model=List[ProductTypePatternResponse])
async def get_all_patterns(db: Session = Depends(get_db)):
    """
    すべての学習パターンを取得

    学習済みのすべての商品タイプパターンを取得します。
    信頼度と使用回数の順にソートされます。
    """
    try:
        learning_service = ProductTypeLearningService(db)
        patterns = learning_service.get_all_patterns()

        return [ProductTypePatternResponse.from_orm(p) for p in patterns]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get patterns: {str(e)}"
        )


@router.get("/patterns/{product_type}", response_model=List[ProductTypePatternResponse])
async def get_patterns_by_type(
    product_type: str,
    db: Session = Depends(get_db)
):
    """特定の商品タイプのパターンを取得"""
    try:
        learning_service = ProductTypeLearningService(db)
        patterns = learning_service.get_patterns_by_type(product_type)

        return [ProductTypePatternResponse.from_orm(p) for p in patterns]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get patterns: {str(e)}"
        )


@router.delete("/patterns/{pattern_id}")
async def delete_pattern(
    pattern_id: int,
    db: Session = Depends(get_db)
):
    """学習パターンを削除"""
    try:
        learning_service = ProductTypeLearningService(db)
        success = learning_service.delete_pattern(pattern_id)

        if success:
            return {"success": True, "message": f"Pattern {pattern_id} deleted"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pattern {pattern_id} not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete pattern: {str(e)}"
        )


@router.get("/statistics", response_model=ProductTypeStatisticsResponse)
async def get_statistics(db: Session = Depends(get_db)):
    """
    学習パターンの統計情報を取得

    - total_patterns: 総パターン数
    - manual_patterns: 手動学習パターン数
    - auto_patterns: 自動学習パターン数
    - total_usage: 総使用回数
    """
    try:
        learning_service = ProductTypeLearningService(db)
        stats = learning_service.get_statistics()

        return ProductTypeStatisticsResponse(**stats)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )
