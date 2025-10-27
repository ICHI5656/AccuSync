# 06. セキュリティ対策

- 認証: OIDC / OAuth2.1（PKCE）。2FA対応（TOTP/Authenticator）
- 認可: RBAC（管理者/経理/閲覧） + オブジェクトレベル（IssuerCompany境界）
- 入力検証: CSV/フォームはサーバ側で必須チェック/型/範囲/正規化
- 機微情報: .envとKMS/Parameter Store、機密はログに出力禁止
- PDF改ざん防止: ファイル名にハッシュ、署名付きURL、必要に応じ**PDF署名**（将来拡張）
- 監査: すべてのCRUD/発行操作を `AuditLog` にJSON差分で記録
- OWASP: SQLi/XSS/CSRF/IDOR/SSRF 対策の標準実装
- レート制限 & IP許可リスト（管理画面）
