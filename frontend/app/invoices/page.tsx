'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

interface Customer {
  id: number
  name: string
  is_individual: boolean
}

interface Invoice {
  id: number
  invoice_no: string
  customer_id: number
  period_start: string
  period_end: string
  issue_date: string
  due_date: string
  subtotal_ex_tax: number
  tax_amount: number
  total_in_tax: number
  status: string
  created_at: string
}

interface InvoiceCreateRequest {
  customer_id: number
  period_start: string
  period_end: string
  notes?: string
}

export default function InvoicesPage() {
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [customers, setCustomers] = useState<Customer[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateDialog, setShowCreateDialog] = useState(false)
  const [selectedCustomerId, setSelectedCustomerId] = useState<number | null>(null)
  const [periodStart, setPeriodStart] = useState('')
  const [periodEnd, setPeriodEnd] = useState('')
  const [notes, setNotes] = useState('')
  const [creating, setCreating] = useState(false)
  const [statusFilter, setStatusFilter] = useState<string>('all')

  // 請求書一覧を取得
  useEffect(() => {
    fetchInvoices()
    fetchCustomers()
  }, [statusFilter])

  const fetchInvoices = async () => {
    try {
      setLoading(true)
      const statusParam = statusFilter !== 'all' ? `?status_filter=${statusFilter}` : ''
      const response = await fetch(`http://localhost:8100/api/v1/invoices${statusParam}`)
      if (response.ok) {
        const data = await response.json()
        setInvoices(data)
      }
    } catch (error) {
      console.error('Failed to fetch invoices:', error)
    } finally {
      setLoading(false)
    }
  }

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

  // 請求書作成
  const handleCreateInvoice = async () => {
    if (!selectedCustomerId || !periodStart || !periodEnd) {
      alert('取引先と期間を選択してください')
      return
    }

    setCreating(true)

    try {
      const requestData: InvoiceCreateRequest = {
        customer_id: selectedCustomerId,
        period_start: periodStart,
        period_end: periodEnd,
        notes: notes || undefined
      }

      const response = await fetch('http://localhost:8100/api/v1/invoices/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData)
      })

      if (response.ok) {
        const newInvoice = await response.json()
        alert(`請求書を作成しました: ${newInvoice.invoice_no}`)
        setShowCreateDialog(false)
        setSelectedCustomerId(null)
        setPeriodStart('')
        setPeriodEnd('')
        setNotes('')
        fetchInvoices()
      } else {
        const error = await response.json()
        alert(`請求書作成に失敗しました: ${error.detail || '不明なエラー'}`)
      }
    } catch (error) {
      console.error('Failed to create invoice:', error)
      alert('請求書作成中にエラーが発生しました')
    } finally {
      setCreating(false)
    }
  }

  // PDF ダウンロード
  const handleDownloadPDF = async (invoiceId: number, invoiceNo: string) => {
    try {
      const response = await fetch(`http://localhost:8100/api/v1/invoices/${invoiceId}/pdf`)

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${invoiceNo}.pdf`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
      } else {
        const error = await response.json()
        alert(`PDF生成に失敗しました: ${error.detail || '不明なエラー'}`)
      }
    } catch (error) {
      console.error('Failed to download PDF:', error)
      alert('PDF生成中にエラーが発生しました')
    }
  }

  // 請求書削除
  const handleDeleteInvoice = async (invoiceId: number, invoiceNo: string, status: string) => {
    if (status === 'issued' || status === 'paid') {
      alert(`ステータスが「${getStatusText(status)}」の請求書は削除できません`)
      return
    }

    if (!confirm(`請求書 ${invoiceNo} を削除しますか？`)) {
      return
    }

    try {
      const response = await fetch(`http://localhost:8100/api/v1/invoices/${invoiceId}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        alert('請求書を削除しました')
        fetchInvoices()
      } else {
        const error = await response.json()
        alert(`削除に失敗しました: ${error.detail || '不明なエラー'}`)
      }
    } catch (error) {
      console.error('Failed to delete invoice:', error)
      alert('削除中にエラーが発生しました')
    }
  }

  // ステータス表示
  const getStatusText = (status: string) => {
    switch (status) {
      case 'draft': return '下書き'
      case 'issued': return '発行済み'
      case 'paid': return '支払済み'
      case 'void': return '無効'
      default: return status
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft': return 'bg-gray-100 text-gray-800'
      case 'issued': return 'bg-blue-100 text-blue-800'
      case 'paid': return 'bg-green-100 text-green-800'
      case 'void': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  // 顧客名を取得
  const getCustomerName = (customerId: number) => {
    const customer = customers.find(c => c.id === customerId)
    return customer ? customer.name : `顧客ID: ${customerId}`
  }

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
              className="px-4 py-4 text-sm font-medium text-muted hover:text-ink hover:border-b-2 hover:border-accent transition-colors"
            >
              注文一覧
            </Link>
            <Link
              href="/invoices"
              className="px-4 py-4 text-sm font-medium text-accent border-b-2 border-accent"
            >
              請求書
            </Link>
          </div>
        </div>
      </div>

      <div className="p-8">
        <div className="max-w-7xl mx-auto">
          {/* ヘッダー */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-ink mb-2">請求書管理</h1>
              <p className="text-muted">注文データから請求書を作成・管理します</p>
            </div>
            <button
              onClick={() => setShowCreateDialog(true)}
              className="px-6 py-3 bg-accent text-white rounded-lg hover:bg-accent/90 transition-colors font-medium"
            >
              + 請求書作成
            </button>
          </div>

          {/* フィルター */}
          <div className="mb-6 flex space-x-3">
            <button
              onClick={() => setStatusFilter('all')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                statusFilter === 'all'
                  ? 'bg-accent text-white'
                  : 'bg-white text-muted border border-line hover:bg-gray-50'
              }`}
            >
              すべて
            </button>
            <button
              onClick={() => setStatusFilter('draft')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                statusFilter === 'draft'
                  ? 'bg-accent text-white'
                  : 'bg-white text-muted border border-line hover:bg-gray-50'
              }`}
            >
              下書き
            </button>
            <button
              onClick={() => setStatusFilter('issued')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                statusFilter === 'issued'
                  ? 'bg-accent text-white'
                  : 'bg-white text-muted border border-line hover:bg-gray-50'
              }`}
            >
              発行済み
            </button>
            <button
              onClick={() => setStatusFilter('paid')}
              className={`px-4 py-2 rounded-lg transition-colors ${
                statusFilter === 'paid'
                  ? 'bg-accent text-white'
                  : 'bg-white text-muted border border-line hover:bg-gray-50'
              }`}
            >
              支払済み
            </button>
          </div>

          {/* 請求書一覧 */}
          {loading ? (
            <div className="text-center py-12 text-muted">読み込み中...</div>
          ) : invoices.length === 0 ? (
            <div className="bg-white rounded-xl border border-line p-12 text-center">
              <p className="text-muted mb-4">請求書がありません</p>
              <button
                onClick={() => setShowCreateDialog(true)}
                className="px-6 py-2 bg-accent text-white rounded-lg hover:bg-accent/90 transition-colors"
              >
                最初の請求書を作成
              </button>
            </div>
          ) : (
            <div className="grid gap-4">
              {invoices.map((invoice) => (
                <div
                  key={invoice.id}
                  className="bg-white rounded-xl border border-line p-6 hover:shadow-lg transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <h3 className="text-xl font-bold text-ink">{invoice.invoice_no}</h3>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(invoice.status)}`}>
                          {getStatusText(invoice.status)}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 gap-x-8 gap-y-2 text-sm mt-4">
                        <div>
                          <span className="text-muted">取引先:</span>
                          <span className="ml-2 font-medium text-ink">{getCustomerName(invoice.customer_id)}</span>
                        </div>
                        <div>
                          <span className="text-muted">集計期間:</span>
                          <span className="ml-2 text-ink">{invoice.period_start} 〜 {invoice.period_end}</span>
                        </div>
                        <div>
                          <span className="text-muted">発行日:</span>
                          <span className="ml-2 text-ink">{invoice.issue_date}</span>
                        </div>
                        <div>
                          <span className="text-muted">支払期限:</span>
                          <span className="ml-2 text-ink">{invoice.due_date}</span>
                        </div>
                        <div className="col-span-2 mt-2">
                          <span className="text-muted">請求金額:</span>
                          <span className="ml-2 text-2xl font-bold text-accent">
                            ¥{invoice.total_in_tax.toLocaleString()}
                          </span>
                          <span className="ml-2 text-xs text-muted">
                            (税抜: ¥{invoice.subtotal_ex_tax.toLocaleString()} + 税: ¥{invoice.tax_amount.toLocaleString()})
                          </span>
                        </div>
                      </div>
                    </div>
                    <div className="flex flex-col space-y-2 ml-4">
                      <button
                        onClick={() => handleDownloadPDF(invoice.id, invoice.invoice_no)}
                        className="px-4 py-2 bg-accent text-white rounded-lg hover:bg-accent/90 transition-colors text-sm font-medium whitespace-nowrap"
                      >
                        📄 PDF
                      </button>
                      {invoice.status === 'draft' && (
                        <button
                          onClick={() => handleDeleteInvoice(invoice.id, invoice.invoice_no, invoice.status)}
                          className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors text-sm font-medium"
                        >
                          削除
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 請求書作成ダイアログ */}
      {showCreateDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-8 max-w-2xl w-full mx-4 shadow-2xl">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-ink">請求書作成</h2>
              <button
                onClick={() => setShowCreateDialog(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-6">
              {/* 取引先選択 */}
              <div>
                <label className="block text-sm font-medium text-ink mb-2">
                  取引先 <span className="text-red-500">*</span>
                </label>
                <select
                  value={selectedCustomerId || ''}
                  onChange={(e) => setSelectedCustomerId(e.target.value ? parseInt(e.target.value) : null)}
                  className="w-full px-4 py-3 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                >
                  <option value="">取引先を選択...</option>
                  {customers.map((customer) => (
                    <option key={customer.id} value={customer.id}>
                      {customer.name} {customer.is_individual ? '（個人）' : '（法人）'}
                    </option>
                  ))}
                </select>
              </div>

              {/* 集計期間 */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-ink mb-2">
                    期間開始日 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="date"
                    value={periodStart}
                    onChange={(e) => setPeriodStart(e.target.value)}
                    className="w-full px-4 py-3 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-ink mb-2">
                    期間終了日 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="date"
                    value={periodEnd}
                    onChange={(e) => setPeriodEnd(e.target.value)}
                    className="w-full px-4 py-3 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                  />
                </div>
              </div>

              {/* 備考 */}
              <div>
                <label className="block text-sm font-medium text-ink mb-2">備考（任意）</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={3}
                  className="w-full px-4 py-3 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                  placeholder="備考があれば入力..."
                />
              </div>

              {/* 注意事項 */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-700">
                  💡 指定期間内の注文データを集計して請求書を作成します。<br/>
                  請求書番号は自動採番され、支払期限は翌月末に設定されます。
                </p>
              </div>

              {/* ボタン */}
              <div className="flex space-x-3">
                <button
                  onClick={() => setShowCreateDialog(false)}
                  disabled={creating}
                  className="flex-1 px-6 py-3 border border-line rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
                >
                  キャンセル
                </button>
                <button
                  onClick={handleCreateInvoice}
                  disabled={creating || !selectedCustomerId || !periodStart || !periodEnd}
                  className="flex-1 px-6 py-3 bg-accent text-white rounded-lg hover:bg-accent/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                >
                  {creating ? '作成中...' : '請求書を作成'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
