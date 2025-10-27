# 10. デプロイ

- ローカル: Docker Compose（web/api/db/redis/minio）
- 本番: AWS（ECS/Fargate or EKS）、RDS for PostgreSQL、ElastiCache、S3、ALB、ACM
- CI/CD: GitHub Actions（lint/test/build/migrate/deploy）
- バックアップ: RDSスナップショット、S3バージョニング
- 監視: CloudWatch + APM（OpenTelemetry/OTel）
