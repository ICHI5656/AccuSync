'use client'

import { useStats } from '../layout'

export default function CountStatsPage() {
  const stats = useStats()

  if (!stats) {
    return null
  }

  return (
    <>
      {/* ヘッダー */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-ink mb-2">📋 件数統計</h1>
        <p className="text-muted">注文件数の詳細統計</p>
      </div>

      {/* ハードケース件数統計 */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-ink mb-4 flex items-center">
          <span className="mr-2">📱</span>
          ハードケース
        </h3>
        <div className="space-y-3">
          {stats.hardcase_stats.map((device, index) => (
            <div key={index} className="bg-white rounded-lg border border-line p-4 shadow-sm">
              <div className="flex justify-between items-center">
                <span className="text-sm text-ink font-medium">{device.device}</span>
                <span className="text-lg text-orange-600 font-bold">{device.count}件</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 手帳ケース件数統計 */}
      {Object.entries(stats.notebook_stats_by_type).map(([notebookType, typeStats], index) => (
        <div key={index} className="mb-8">
          <h3 className="text-lg font-semibold text-ink mb-4 flex items-center">
            <span className="mr-2">📘</span>
            手帳ケース（{notebookType}）
          </h3>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h4 className="text-sm font-semibold text-muted mb-3">📐 手帳サイズ</h4>
              <div className="space-y-3">
                {typeStats.size_stats.map((item, sizeIndex) => (
                  <div
                    key={sizeIndex}
                    className="bg-white rounded-lg border border-line p-4 shadow-sm"
                  >
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-ink font-medium">{item.size}</span>
                      <span className="text-lg text-blue-600 font-bold">{item.count}件</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h4 className="text-sm font-semibold text-muted mb-3">📱 機種別</h4>
              <div className="space-y-3">
                {typeStats.device_stats.map((item, deviceIndex) => (
                  <div
                    key={deviceIndex}
                    className="bg-white rounded-lg border border-line p-4 shadow-sm"
                  >
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-ink font-medium">{item.device}</span>
                      <span className="text-lg text-green-600 font-bold">{item.count}件</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      ))}
    </>
  )
}
