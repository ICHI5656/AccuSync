'use client'

import { useState, useEffect, createContext, useContext } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

interface OrderByDate {
  date: string
  count: number
  quantity: number
}

interface DeviceStats {
  device: string
  count: number
  quantity: number
  by_date: OrderByDate[]
}

interface NotebookTypeStats {
  size_stats: { size: string; count: number; quantity: number }[]
  device_stats: { device: string; count: number; quantity: number }[]
}

interface CustomerCompany {
  id: number
  code: string
  name: string
  is_individual: boolean
}

interface StatsData {
  total_orders: number
  hardcase_stats: DeviceStats[]
  notebook_stats_by_type: { [key: string]: NotebookTypeStats }
}

const StatsContext = createContext<StatsData | null>(null)

export function useStats() {
  const context = useContext(StatsContext)
  return context
}

export default function StatsLayout({ children }: { children: React.ReactNode }) {
  const [stats, setStats] = useState<StatsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [expandedHardcase, setExpandedHardcase] = useState(false)
  const [expandedNotebook, setExpandedNotebook] = useState(false)
  const [customers, setCustomers] = useState<CustomerCompany[]>([])
  const [selectedCustomerId, setSelectedCustomerId] = useState<number | null>(null)
  const pathname = usePathname()

  // 取引先一覧を取得
  useEffect(() => {
    const fetchCustomers = async () => {
      try {
        const response = await fetch('http://localhost:8100/api/v1/settings/customers')
        if (response.ok) {
          const data = await response.json()
          setCustomers(data)
        }
      } catch (error) {
        console.error('Failed to fetch customers:', error)
      }
    }
    fetchCustomers()
  }, [])

  // 統計データを取得
  useEffect(() => {
    const fetchStats = async () => {
      setLoading(true)
      try {
        const params = new URLSearchParams()
        if (selectedCustomerId) {
          params.append('customer_id', selectedCustomerId.toString())
        }

        const url = `http://localhost:8100/api/v1/stats/orders/detailed${params.toString() ? '?' + params.toString() : ''}`
        const response = await fetch(url)
        if (response.ok) {
          const data = await response.json()
          setStats(data)
        } else {
          console.error('API returned status:', response.status)
        }
      } catch (error) {
        console.error('Failed to load stats:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
  }, [selectedCustomerId])

  const isActive = (path: string) => pathname === path

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-24 bg-gray-200 rounded"></div>
            <div className="h-24 bg-gray-200 rounded"></div>
            <div className="h-24 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  if (!stats) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center text-muted">統計データの読み込みに失敗しました</div>
      </div>
    )
  }

  return (
    <StatsContext.Provider value={stats}>
      <div className="flex min-h-screen bg-gray-50">
        {/* サイドバー */}
        <aside className="w-64 bg-white border-r border-line sticky top-0 h-screen overflow-y-auto">
          <div className="p-6">
            <h2 className="text-lg font-bold text-ink mb-6">📊 統計メニュー</h2>

            {/* 取引先選択 */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-ink mb-2">
                取引先会社
              </label>
              <select
                value={selectedCustomerId || ''}
                onChange={(e) => setSelectedCustomerId(e.target.value ? parseInt(e.target.value) : null)}
                className="w-full px-3 py-2 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent text-sm"
              >
                <option value="">すべて</option>
                {customers.map((customer) => (
                  <option key={customer.id} value={customer.id}>
                    {customer.name} {customer.is_individual ? '（個人）' : '（法人）'}
                  </option>
                ))}
              </select>
              <p className="text-xs text-muted mt-1">
                {selectedCustomerId ? '選択した会社の注文のみ表示' : '全会社の注文を表示'}
              </p>
            </div>

            {/* 総注文数サマリー */}
            <div className="mb-6 p-4 bg-gradient-to-r from-accent/10 to-accent/5 rounded-lg border border-accent/20">
              <div className="text-xs text-muted mb-1">総注文数</div>
              <div className="text-2xl font-bold text-accent">{stats.total_orders}件</div>
              {selectedCustomerId && (
                <div className="text-xs text-accent mt-1">
                  {customers.find(c => c.id === selectedCustomerId)?.name || ''}のみ
                </div>
              )}
            </div>

            {/* ナビゲーションメニュー */}
            <nav className="space-y-2">
              <Link
                href="/stats"
                className={`block px-4 py-3 rounded-lg transition-colors ${
                  isActive('/stats')
                    ? 'bg-accent/10 text-accent'
                    : 'hover:bg-accent/10 text-ink hover:text-accent'
                }`}
              >
                <div className="flex items-center text-sm font-medium">
                  <span className="mr-2">📈</span>
                  総計
                </div>
                <div className="text-xs text-muted mt-1 ml-6">全体サマリー</div>
              </Link>

              <Link
                href="/stats/count"
                className={`block px-4 py-3 rounded-lg transition-colors ${
                  isActive('/stats/count')
                    ? 'bg-purple-100 text-purple-600'
                    : 'hover:bg-purple-50 text-ink hover:text-purple-600'
                }`}
              >
                <div className="flex items-center text-sm font-medium">
                  <span className="mr-2">📋</span>
                  件数統計
                </div>
                <div className="text-xs text-muted mt-1 ml-6">注文件数の統計</div>
              </Link>

              <Link
                href="/stats/quantity"
                className={`block px-4 py-3 rounded-lg transition-colors ${
                  isActive('/stats/quantity')
                    ? 'bg-indigo-100 text-indigo-600'
                    : 'hover:bg-indigo-50 text-ink hover:text-indigo-600'
                }`}
              >
                <div className="flex items-center text-sm font-medium">
                  <span className="mr-2">📦</span>
                  個数統計
                </div>
                <div className="text-xs text-muted mt-1 ml-6">商品個数の統計</div>
              </Link>

              <Link
                href="/stats/count-summary"
                className={`block px-4 py-3 rounded-lg transition-colors ${
                  isActive('/stats/count-summary')
                    ? 'bg-orange-100 text-orange-600'
                    : 'hover:bg-orange-50 text-ink hover:text-orange-600'
                }`}
              >
                <div className="flex items-center text-sm font-medium">
                  <span className="mr-2">📊</span>
                  件数サマリー
                </div>
                <div className="text-xs text-muted mt-1 ml-6">件数の概要</div>
              </Link>

              <Link
                href="/stats/quantity-summary"
                className={`block px-4 py-3 rounded-lg transition-colors ${
                  isActive('/stats/quantity-summary')
                    ? 'bg-blue-100 text-blue-600'
                    : 'hover:bg-blue-50 text-ink hover:text-blue-600'
                }`}
              >
                <div className="flex items-center text-sm font-medium">
                  <span className="mr-2">🎯</span>
                  個数サマリー
                </div>
                <div className="text-xs text-muted mt-1 ml-6">個数の概要</div>
              </Link>
            </nav>

            {/* 件数サマリー */}
            <div className="mt-6 pt-6 border-t border-line">
              <h3 className="text-sm font-semibold text-ink mb-3">📋 件数サマリー</h3>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-muted">ハードケース</span>
                  <span className="text-sm font-semibold text-orange-600">
                    {stats.hardcase_stats.reduce((sum, item) => sum + item.count, 0)}件
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-muted">手帳ケース</span>
                  <span className="text-sm font-semibold text-blue-600">
                    {Object.values(stats.notebook_stats_by_type).reduce(
                      (sum, type) => sum + type.size_stats.reduce((s, item) => s + item.count, 0),
                      0
                    )}件
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-muted">総件数</span>
                  <span className="text-sm font-semibold text-accent">
                    {stats.hardcase_stats.reduce((sum, item) => sum + item.count, 0) +
                      Object.values(stats.notebook_stats_by_type).reduce(
                        (sum, type) => sum + type.size_stats.reduce((s, item) => s + item.count, 0),
                        0
                      )}件
                  </span>
                </div>
              </div>
            </div>

            {/* 個数サマリー */}
            <div className="mt-6 pt-6 border-t border-line">
              <h3 className="text-sm font-semibold text-ink mb-3">📦 個数サマリー</h3>
              <div className="space-y-3">
                {/* ハードケース（クリック可能） */}
                <div>
                  <button
                    onClick={() => setExpandedHardcase(!expandedHardcase)}
                    className="w-full flex justify-between items-center hover:bg-orange-50 p-2 rounded transition-colors"
                  >
                    <span className="text-xs text-muted flex items-center">
                      <span className="mr-1">{expandedHardcase ? '▼' : '▶'}</span>
                      ハードケース
                    </span>
                    <span className="text-sm font-semibold text-orange-600">
                      {stats.hardcase_stats.reduce((sum, item) => sum + item.quantity, 0)}個
                    </span>
                  </button>

                  {/* 展開時の機種別表示 */}
                  {expandedHardcase && (
                    <div className="mt-2 ml-4 space-y-1 bg-orange-50 rounded p-2">
                      {stats.hardcase_stats.map((device, index) => (
                        <div key={index} className="flex justify-between text-xs">
                          <span className="text-muted">{device.device}</span>
                          <span className="text-orange-600 font-semibold">{device.quantity}個</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* 手帳ケース（クリック可能） */}
                <div>
                  <button
                    onClick={() => setExpandedNotebook(!expandedNotebook)}
                    className="w-full flex justify-between items-center hover:bg-blue-50 p-2 rounded transition-colors"
                  >
                    <span className="text-xs text-muted flex items-center">
                      <span className="mr-1">{expandedNotebook ? '▼' : '▶'}</span>
                      手帳ケース
                    </span>
                    <span className="text-sm font-semibold text-blue-600">
                      {Object.values(stats.notebook_stats_by_type).reduce(
                        (sum, type) => sum + type.size_stats.reduce((s, item) => s + item.quantity, 0),
                        0
                      )}個
                    </span>
                  </button>

                  {/* 展開時のサイズ別表示 */}
                  {expandedNotebook && (
                    <div className="mt-2 ml-4 space-y-1 bg-blue-50 rounded p-2">
                      {(() => {
                        const sizeMap = Object.values(stats.notebook_stats_by_type)
                          .flatMap(type => type.size_stats)
                          .reduce((acc: { [key: string]: number }, item) => {
                            acc[item.size] = (acc[item.size] || 0) + item.quantity
                            return acc
                          }, {})

                        return Object.entries(sizeMap)
                          .sort(([, a], [, b]) => b - a)
                          .map(([size, quantity]) => (
                            <div key={size} className="flex justify-between text-xs">
                              <span className="text-muted">{size}</span>
                              <span className="text-blue-600 font-semibold">{quantity}個</span>
                            </div>
                          ))
                      })()}
                    </div>
                  )}
                </div>

                {/* 総個数 */}
                <div className="flex justify-between items-center pt-2 border-t border-line">
                  <span className="text-xs text-muted">総個数</span>
                  <span className="text-sm font-semibold text-accent">
                    {stats.total_orders}個
                  </span>
                </div>
              </div>
            </div>
          </div>
        </aside>

        {/* メインコンテンツ */}
        <main className="flex-1 p-8">
          {children}
        </main>
      </div>
    </StatsContext.Provider>
  )
}
