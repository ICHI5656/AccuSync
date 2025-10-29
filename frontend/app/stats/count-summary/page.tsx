'use client'

import { useStats } from '../layout'

export default function CountSummaryPage() {
  const stats = useStats()

  if (!stats) {
    return null
  }

  return (
    <>
      {/* ヘッダー */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-ink mb-2">📊 件数サマリー</h1>
        <p className="text-muted">件数統計の概要</p>
      </div>

      {/* サマリーカード */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* ハードケース件数 */}
        <div className="bg-orange-50 rounded-lg border border-orange-200 p-6">
          <h3 className="text-lg font-semibold text-orange-700 mb-4 flex items-center">
            <span className="mr-2">📱</span>
            ハードケース件数
          </h3>
          <div className="text-4xl font-bold text-orange-600 mb-6">
            {stats.hardcase_stats.reduce((sum, item) => sum + item.count, 0)}件
          </div>
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-muted mb-2">機種別トップ5</h4>
            {stats.hardcase_stats
              .sort((a, b) => b.count - a.count)
              .slice(0, 5)
              .map((device, index) => (
                <div key={index} className="flex justify-between items-center bg-white p-2 rounded">
                  <span className="text-sm text-ink">{device.device}</span>
                  <span className="text-sm font-semibold text-orange-600">{device.count}件</span>
                </div>
              ))}
          </div>
        </div>

        {/* 手帳ケース件数 */}
        <div className="bg-blue-50 rounded-lg border border-blue-200 p-6">
          <h3 className="text-lg font-semibold text-blue-700 mb-4 flex items-center">
            <span className="mr-2">📘</span>
            手帳ケース件数
          </h3>
          <div className="text-4xl font-bold text-blue-600 mb-6">
            {Object.values(stats.notebook_stats_by_type).reduce(
              (sum, type) => sum + type.size_stats.reduce((s, item) => s + item.count, 0),
              0
            )}件
          </div>
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-muted mb-2">種類別</h4>
            {Object.entries(stats.notebook_stats_by_type).map(([type, typeStats], index) => (
              <div key={index} className="flex justify-between items-center bg-white p-2 rounded">
                <span className="text-sm text-ink">{type}</span>
                <span className="text-sm font-semibold text-blue-600">
                  {typeStats.size_stats.reduce((sum, item) => sum + item.count, 0)}件
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 総件数 */}
      <div className="mt-6 bg-accent/10 rounded-lg border border-accent/20 p-6">
        <div className="flex justify-between items-center">
          <h3 className="text-2xl font-semibold text-accent">総件数</h3>
          <div className="text-5xl font-bold text-accent">
            {stats.hardcase_stats.reduce((sum, item) => sum + item.count, 0) +
              Object.values(stats.notebook_stats_by_type).reduce(
                (sum, type) => sum + type.size_stats.reduce((s, item) => s + item.count, 0),
                0
              )}件
          </div>
        </div>
      </div>
    </>
  )
}
