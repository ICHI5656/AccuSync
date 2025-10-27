"""Base AI Provider Interface - AIプロバイダーの抽象基底クラス"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class FileDetectionResult(BaseModel):
    """ファイル形式検出結果"""
    file_type: str  # csv, excel, pdf, txt, image
    confidence: float
    metadata: Optional[Dict[str, Any]] = None


class DataExtractionResult(BaseModel):
    """データ抽出結果"""
    success: bool
    data: List[Dict[str, Any]]  # 抽出されたデータの配列
    confidence: float
    errors: Optional[List[str]] = None


class MappingResult(BaseModel):
    """マッピング結果"""
    success: bool
    mapping: Dict[str, str]  # {column_name: target_field}
    confidence: float
    suggestions: Optional[Dict[str, List[str]]] = None


class QualityCheckResult(BaseModel):
    """データ品質チェック結果"""
    success: bool
    issues: List[Dict[str, Any]]  # 検出された問題
    suggestions: List[Dict[str, Any]]  # 修正提案
    enhanced_data: Optional[List[Dict[str, Any]]] = None  # 補完後のデータ


class CustomerTypeResult(BaseModel):
    """顧客タイプ判定結果"""
    is_individual: bool  # True: 個人, False: 会社
    confidence: float
    reason: str  # 判定理由
    metadata: Optional[Dict[str, Any]] = None


class AIProvider(ABC):
    """AIプロバイダーの抽象基底クラス

    すべてのAIプロバイダーはこのインターフェースを実装します
    """

    def __init__(self, config: Dict[str, Any]):
        """初期化

        Args:
            config: プロバイダー設定
        """
        self.config = config

    @abstractmethod
    async def detect_file_format(
        self,
        file_content: bytes,
        file_name: str,
        file_extension: Optional[str] = None
    ) -> FileDetectionResult:
        """ファイル形式を自動検出

        Args:
            file_content: ファイルの内容（バイト列）
            file_name: ファイル名
            file_extension: ファイル拡張子（オプション）

        Returns:
            ファイル検出結果
        """
        pass

    @abstractmethod
    async def extract_data(
        self,
        content: str,
        file_type: str,
        extract_fields: List[str]
    ) -> DataExtractionResult:
        """非構造化データから情報を抽出

        Args:
            content: 抽出元のテキストコンテンツ
            file_type: ファイルタイプ
            extract_fields: 抽出するフィールドのリスト

        Returns:
            データ抽出結果
        """
        pass

    @abstractmethod
    async def auto_map_columns(
        self,
        column_names: List[str],
        target_fields: List[str],
        sample_data: Optional[List[Dict[str, Any]]] = None
    ) -> MappingResult:
        """列名を自動的にフィールドにマッピング

        Args:
            column_names: CSV/Excelの列名リスト
            target_fields: 対象フィールド名リスト
            sample_data: サンプルデータ（オプション）

        Returns:
            マッピング結果
        """
        pass

    @abstractmethod
    async def check_data_quality(
        self,
        data: List[Dict[str, Any]],
        rules: Optional[Dict[str, Any]] = None
    ) -> QualityCheckResult:
        """データ品質チェックと補完

        Args:
            data: チェック対象のデータ
            rules: チェックルール（オプション）

        Returns:
            品質チェック結果
        """
        pass

    @abstractmethod
    async def classify_customer_type(
        self,
        customer_name: str,
        additional_info: Optional[Dict[str, Any]] = None
    ) -> CustomerTypeResult:
        """顧客名から会社か個人かを判定

        Args:
            customer_name: 顧客名
            additional_info: 追加情報（住所、電話番号など）

        Returns:
            顧客タイプ判定結果
        """
        pass
