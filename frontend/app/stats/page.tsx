'use client'

import { useStats } from './layout'

export default function TotalStatsPage() {
  const stats = useStats()

  if (!stats) {
    return null
  }

  return (
    <>
      {/* ヘッダー */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-ink mb-2">📈 総計</h1>
        <p className="text-muted">全体サマリー情報</p>
      </div>

      {/* 総計セクション */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* ハードケース総計 */}
        <div className="bg-orange-50 rounded-lg border border-orange-200 p-6">
          <h3 className="text-lg font-semibold text-orange-700 mb-4 flex items-center">
            <span className="mr-2">📱</span>
            ハードケース総計
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted">件数</span>
              <span className="text-xl font-bold text-orange-600">
                {stats.hardcase_stats.reduce((sum, item) => sum + item.count, 0)}件
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted">個数</span>
              <span className="text-xl font-bold text-orange-600">
                {stats.hardcase_stats.reduce((sum, item) => sum + item.quantity, 0)}個
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted">機種数</span>
              <span className="text-xl font-bold text-orange-600">
                {stats.hardcase_stats.length}種類
              </span>
            </div>
          </div>
        </div>

        {/* 手帳ケース総計 */}
        <div className="bg-blue-50 rounded-lg border border-blue-200 p-6">
          <h3 className="text-lg font-semibold text-blue-700 mb-4 flex items-center">
            <span className="mr-2">📘</span>
            手帳ケース総計
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted">件数</span>
              <span className="text-xl font-bold text-blue-600">
                {Object.values(stats.notebook_stats_by_type).reduce(
                  (sum, type) => sum + type.size_stats.reduce((s, item) => s + item.count, 0),
                  0
                )}件
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted">個数</span>
              <span className="text-xl font-bold text-blue-600">
                {Object.values(stats.notebook_stats_by_type).reduce(
                  (sum, type) => sum + type.size_stats.reduce((s, item) => s + item.quantity, 0),
                  0
                )}個
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted">手帳種類</span>
              <span className="text-xl font-bold text-blue-600">
                {Object.keys(stats.notebook_stats_by_type).length}種類
              </span>
            </div>
          </div>
        </div>

        {/* 全体総計 */}
        <div className="bg-accent/10 rounded-lg border border-accent/20 p-6">
          <h3 className="text-lg font-semibold text-accent mb-4 flex items-center">
            <span className="mr-2">🎯</span>
            全体総計
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted">総件数</span>
              <span className="text-xl font-bold text-accent">
                {stats.hardcase_stats.reduce((sum, item) => sum + item.count, 0) +
                  Object.values(stats.notebook_stats_by_type).reduce(
                    (sum, type) => sum + type.size_stats.reduce((s, item) => s + item.count, 0),
                    0
                  )}件
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted">総個数</span>
              <span className="text-xl font-bold text-accent">
                {stats.total_orders}個
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted">総機種数</span>
              <span className="text-xl font-bold text-accent">
                {stats.hardcase_stats.length +
                  Object.values(stats.notebook_stats_by_type).reduce(
                    (sum, type) => sum + type.device_stats.length,
                    0
                  )}種類
              </span>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
