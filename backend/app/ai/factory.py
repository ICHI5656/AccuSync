"""AI Provider Factory - AIプロバイダーのファクトリー"""

from typing import Dict, Any

from app.ai.base import AIProvider
from app.ai.openai_provider import OpenAIProvider
from app.ai.claude_provider import ClaudeProvider
from app.core.config import settings


class AIProviderFactory:
    """AIプロバイダーファクトリー

    設定に基づいて適切なAIプロバイダーを生成します
    """

    @staticmethod
    def create(provider_name: str = None, config: Dict[str, Any] = None) -> AIProvider:
        """AIプロバイダーを生成

        Args:
            provider_name: プロバイダー名（openai, claude, google_document_ai）
            config: プロバイダー設定（オプション）

        Returns:
            AIProvider instance

        Raises:
            ValueError: 未サポートのプロバイダーの場合
        """
        if provider_name is None:
            provider_name = settings.AI_PROVIDER

        if config is None:
            # Load config from settings
            ai_config = settings.load_ai_config()
            provider_config = ai_config.get("providers", {}).get(provider_name, {})
        else:
            provider_config = config

        providers = {
            "openai": OpenAIProvider,
            "claude": ClaudeProvider,
            # "google_document_ai": GoogleDocumentAIProvider,  # TODO: 実装予定
        }

        provider_class = providers.get(provider_name)
        if provider_class is None:
            raise ValueError(f"Unsupported AI provider: {provider_name}")

        return provider_class(provider_config)

    @staticmethod
    def is_enabled(feature_name: str) -> bool:
        """指定された機能が有効かチェック

        Args:
            feature_name: 機能名

        Returns:
            有効な場合True
        """
        ai_config = settings.load_ai_config()
        features = ai_config.get("features", {})

        return features.get(feature_name, {}).get("enabled", False)
