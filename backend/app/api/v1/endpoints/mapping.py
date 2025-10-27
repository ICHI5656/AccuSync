"""
Mapping API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.models.mapping_template import MappingTemplate
from app.constants.mapping_fields import (
    STANDARD_FIELDS,
    get_required_fields,
    get_optional_fields,
    get_all_field_keys
)


router = APIRouter()


class FieldInfo(BaseModel):
    """フィールド情報"""
    key: str
    label: str
    required: bool
    description: str
    aliases: List[str]


class MappingFieldsResponse(BaseModel):
    """マッピングフィールド一覧レスポンス"""
    required_fields: List[FieldInfo]
    optional_fields: List[FieldInfo]


class MappingTemplateCreate(BaseModel):
    """マッピングテンプレート作成リクエスト"""
    template_name: str = Field(..., min_length=1, max_length=100, description="テンプレート名")
    description: Optional[str] = Field(None, max_length=500, description="説明")
    file_pattern: Optional[str] = Field(None, max_length=200, description="ファイル名パターン")
    file_type: Optional[str] = Field(None, description="ファイルタイプ")
    column_mapping: dict = Field(..., description="列マッピング設定")
    is_default: bool = Field(False, description="デフォルトテンプレートフラグ")


class MappingTemplateResponse(BaseModel):
    """マッピングテンプレートレスポンス"""
    id: int
    template_name: str
    description: str | None
    file_pattern: str | None
    file_type: str | None
    column_mapping: dict
    is_default: bool
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


@router.get("/fields", response_model=MappingFieldsResponse)
async def get_mapping_fields():
    """
    利用可能なマッピングフィールド一覧を取得
    """
    required_keys = get_required_fields()
    optional_keys = get_optional_fields()

    required_fields = [
        FieldInfo(
            key=key,
            label=STANDARD_FIELDS[key]["label"],
            required=True,
            description=STANDARD_FIELDS[key]["description"],
            aliases=STANDARD_FIELDS[key]["aliases"]
        )
        for key in required_keys
    ]

    optional_fields = [
        FieldInfo(
            key=key,
            label=STANDARD_FIELDS[key]["label"],
            required=False,
            description=STANDARD_FIELDS[key]["description"],
            aliases=STANDARD_FIELDS[key]["aliases"]
        )
        for key in optional_keys
    ]

    return MappingFieldsResponse(
        required_fields=required_fields,
        optional_fields=optional_fields
    )


@router.get("/templates", response_model=List[MappingTemplateResponse])
async def list_templates(
    db: Session = Depends(get_db),
    is_active: Optional[bool] = None
):
    """
    マッピングテンプレート一覧を取得
    """
    try:
        query = db.query(MappingTemplate)

        if is_active is not None:
            query = query.filter(MappingTemplate.is_active == is_active)

        templates = query.order_by(
            MappingTemplate.is_default.desc(),
            MappingTemplate.created_at.desc()
        ).all()

        return [
            MappingTemplateResponse(
                id=t.id,
                template_name=t.template_name,
                description=t.description,
                file_pattern=t.file_pattern,
                file_type=t.file_type,
                column_mapping=t.column_mapping,
                is_default=t.is_default,
                is_active=t.is_active,
                created_at=t.created_at.isoformat() if t.created_at else "",
                updated_at=t.updated_at.isoformat() if t.updated_at else ""
            )
            for t in templates
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve templates: {str(e)}"
        )


@router.get("/templates/{template_id}", response_model=MappingTemplateResponse)
async def get_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """
    特定のマッピングテンプレートを取得
    """
    try:
        template = db.query(MappingTemplate).filter(
            MappingTemplate.id == template_id
        ).first()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template {template_id} not found"
            )

        return MappingTemplateResponse(
            id=template.id,
            template_name=template.template_name,
            description=template.description,
            file_pattern=template.file_pattern,
            file_type=template.file_type,
            column_mapping=template.column_mapping,
            is_default=template.is_default,
            is_active=template.is_active,
            created_at=template.created_at.isoformat() if template.created_at else "",
            updated_at=template.updated_at.isoformat() if template.updated_at else ""
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve template: {str(e)}"
        )


@router.post("/templates", response_model=MappingTemplateResponse)
async def create_template(
    request: MappingTemplateCreate,
    db: Session = Depends(get_db)
):
    """
    新しいマッピングテンプレートを作成
    """
    try:
        # テンプレート名の重複チェック
        existing = db.query(MappingTemplate).filter(
            MappingTemplate.template_name == request.template_name
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Template '{request.template_name}' already exists"
            )

        # デフォルトテンプレートの場合、既存のデフォルトを解除
        if request.is_default:
            db.query(MappingTemplate).filter(
                MappingTemplate.is_default == True
            ).update({"is_default": False})

        # 新しいテンプレート作成
        template = MappingTemplate(
            template_name=request.template_name,
            description=request.description,
            file_pattern=request.file_pattern,
            file_type=request.file_type,
            column_mapping=request.column_mapping,
            is_default=request.is_default,
            is_active=True
        )

        db.add(template)
        db.commit()
        db.refresh(template)

        return MappingTemplateResponse(
            id=template.id,
            template_name=template.template_name,
            description=template.description,
            file_pattern=template.file_pattern,
            file_type=template.file_type,
            column_mapping=template.column_mapping,
            is_default=template.is_default,
            is_active=template.is_active,
            created_at=template.created_at.isoformat() if template.created_at else "",
            updated_at=template.updated_at.isoformat() if template.updated_at else ""
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create template: {str(e)}"
        )


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """
    マッピングテンプレートを削除
    """
    try:
        template = db.query(MappingTemplate).filter(
            MappingTemplate.id == template_id
        ).first()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template {template_id} not found"
            )

        db.delete(template)
        db.commit()

        return {"success": True, "message": f"Template {template_id} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete template: {str(e)}"
        )
