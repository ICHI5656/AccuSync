'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

interface CustomerCompany {
  id: number
  code: string
  name: string
  is_individual: boolean
}

interface OrderItem {
  id: number
  product_id: number
  product_name: string
  product_sku: string
  qty: number
  unit_price: string
  subtotal_ex_tax: string
  tax_rate: string
  tax_amount: string
  total_in_tax: string
}

interface Order {
  id: number
  order_no: string
  order_date: string
  customer_id: number
  customer_name: string
  customer_code: string
  is_individual: boolean
  issuer_id: number
  issuer_name: string
  source: string
  memo: string | null
  items: OrderItem[]
  total_amount: string
}

interface OrderSummary {
  total_orders: number
  total_amount: string
  customer_count: number
}

export default function OrdersPage() {
  const [customers, setCustomers] = useState<CustomerCompany[]>([])
  const [selectedCustomerId, setSelectedCustomerId] = useState<number | null>(null)
  const [startDate, setStartDate] = useState<string>('')
  const [endDate, setEndDate] = useState<string>('')
  const [orders, setOrders] = useState<Order[]>([])
  const [summary, setSummary] = useState<OrderSummary | null>(null)
  const [loading, setLoading] = useState(false)

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

  // 注文データを取得
  const fetchOrders = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      if (selectedCustomerId) {
        params.append('customer_id', selectedCustomerId.toString())
      }
      if (startDate) {
        params.append('start_date', startDate)
      }
      if (endDate) {
        params.append('end_date', endDate)
      }

      const [ordersRes, summaryRes] = await Promise.all([
        fetch(`http://localhost:8100/api/v1/orders/?${params.toString()}`),
        fetch(`http://localhost:8100/api/v1/orders/summary?${params.toString()}`)
      ])

      if (ordersRes.ok) {
        const ordersData = await ordersRes.json()
        setOrders(ordersData)
      }

      if (summaryRes.ok) {
        const summaryData = await summaryRes.json()
        setSummary(summaryData)
      }
    } catch (error) {
      console.error('Failed to fetch orders:', error)
    } finally {
      setLoading(false)
    }
  }

  // 初回ロード時に全データ取得
  useEffect(() => {
    fetchOrders()
  }, [])

  return (
    <div className="min-h-screen bg-gray-50">
      {/* タブナビゲーション */}
      <div className="bg-white border-b border-line">
        <div className="max-w-7xl mx-auto px-8">
          <div className="flex space-x-8">
            <Link
              href="/imports"
              className="px-4 py-4 text-sm font-medium text-muted hover:text-ink hover:border-b-2 hover:border-accent transition-colors"
            >
              データ取り込み
            </Link>
            <Link
              href="/orders"
              className="px-4 py-4 text-sm font-medium text-accent border-b-2 border-accent"
            >
              注文一覧
            </Link>
          </div>
        </div>
      </div>

      <div className="flex">
        {/* サイドバー */}
        <div className="w-80 bg-white border-r border-line h-screen p-6 overflow-y-auto">
          <h2 className="text-lg font-bold text-ink mb-6">フィルター</h2>

          {/* 取引先選択 */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-ink mb-2">
              取引先会社
            </label>
            <select
              value={selectedCustomerId || ''}
              onChange={(e) => setSelectedCustomerId(e.target.value ? parseInt(e.target.value) : null)}
              className="w-full px-3 py-2 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
            >
              <option value="">すべて</option>
              {customers.map((customer) => (
                <option key={customer.id} value={customer.id}>
                  {customer.name} {customer.is_individual ? '（個人）' : '（法人）'}
                </option>
              ))}
            </select>
          </div>

          {/* 期間設定 */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-ink mb-2">
              開始日
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full px-3 py-2 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>

          <div className="mb-6">
            <label className="block text-sm font-medium text-ink mb-2">
              終了日
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full px-3 py-2 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>

          {/* 検索ボタン */}
          <button
            onClick={fetchOrders}
            disabled={loading}
            className="w-full px-4 py-2 bg-accent text-white rounded-lg hover:bg-accent/90 transition-colors disabled:opacity-50"
          >
            {loading ? '読み込み中...' : '検索'}
          </button>

          {/* サマリー表示 */}
          {summary && (
            <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200">
              <h3 className="text-sm font-semibold text-ink mb-3">集計</h3>
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted">注文件数:</span>
                  <span className="font-semibold text-ink">{summary.total_orders}件</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted">合計金額:</span>
                  <span className="font-semibold text-accent">
                    ¥{parseFloat(summary.total_amount).toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted">取引先数:</span>
                  <span className="font-semibold text-ink">{summary.customer_count}社</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* メインコンテンツ */}
        <div className="flex-1 p-8 overflow-y-auto" style={{ height: 'calc(100vh - 60px)' }}>
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-ink mb-2">注文一覧</h1>
            <p className="text-muted">取り込んだ注文データを表示します</p>
          </div>

          {/* 注文一覧 */}
          {loading ? (
            <div className="text-center py-12">
              <p className="text-muted">読み込み中...</p>
            </div>
          ) : orders.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-xl border border-line">
              <p className="text-muted">注文データがありません</p>
            </div>
          ) : (
            <div className="space-y-4">
              {orders.map((order) => (
                <div key={order.id} className="bg-white rounded-xl border border-line p-6">
                  {/* 注文ヘッダー */}
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-ink">{order.order_no}</h3>
                      <p className="text-sm text-muted">
                        {new Date(order.order_date).toLocaleDateString('ja-JP')} | {order.source}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold text-accent">
                        ¥{parseFloat(order.total_amount).toLocaleString()}
                      </p>
                      <p className="text-xs text-muted">税込</p>
                    </div>
                  </div>

                  {/* 顧客情報 */}
                  <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center space-x-4">
                      <div>
                        <p className="text-xs text-muted">取引先</p>
                        <p className="text-sm font-medium text-ink">{order.customer_name}</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted">コード</p>
                        <p className="text-sm text-muted">{order.customer_code}</p>
                      </div>
                      {order.is_individual && (
                        <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                          個人
                        </span>
                      )}
                    </div>
                  </div>

                  {/* 商品一覧 */}
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-medium text-muted">商品名</th>
                          <th className="px-4 py-2 text-right text-xs font-medium text-muted">数量</th>
                          <th className="px-4 py-2 text-right text-xs font-medium text-muted">単価</th>
                          <th className="px-4 py-2 text-right text-xs font-medium text-muted">小計（税抜）</th>
                          <th className="px-4 py-2 text-right text-xs font-medium text-muted">税率</th>
                          <th className="px-4 py-2 text-right text-xs font-medium text-muted">税額</th>
                          <th className="px-4 py-2 text-right text-xs font-medium text-muted">合計（税込）</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-line">
                        {order.items.map((item) => (
                          <tr key={item.id}>
                            <td className="px-4 py-3 text-ink">{item.product_name}</td>
                            <td className="px-4 py-3 text-right text-ink">{item.qty}</td>
                            <td className="px-4 py-3 text-right text-ink">¥{parseFloat(item.unit_price).toLocaleString()}</td>
                            <td className="px-4 py-3 text-right text-ink">¥{parseFloat(item.subtotal_ex_tax).toLocaleString()}</td>
                            <td className="px-4 py-3 text-right text-muted">{(parseFloat(item.tax_rate) * 100).toFixed(0)}%</td>
                            <td className="px-4 py-3 text-right text-muted">¥{parseFloat(item.tax_amount).toLocaleString()}</td>
                            <td className="px-4 py-3 text-right font-semibold text-accent">¥{parseFloat(item.total_in_tax).toLocaleString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {/* メモ */}
                  {order.memo && (
                    <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <p className="text-xs text-muted mb-1">メモ</p>
                      <p className="text-sm text-ink">{order.memo}</p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
