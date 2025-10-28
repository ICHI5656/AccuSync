'use client'

import { useState, useEffect } from 'react'

interface Customer {
  id: number
  name: string
  code: string | null
  is_individual: boolean
  postal_code: string | null
  address: string | null
  billing_address: string | null
  phone: string | null
  email: string | null
  contact_name: string | null
  contact_email: string | null
  payment_terms: string | null
  closing_day: number | null
  payment_day: number | null
  payment_month_offset: number | null
  tax_mode: string | null
  notes: string | null
  created_at: string | null
  updated_at: string | null
}

interface CustomerFormData {
  name: string
  code: string
  is_individual: boolean
  postal_code: string
  address: string
  billing_address: string
  phone: string
  email: string
  contact_name: string
  contact_email: string
  payment_terms: string
  closing_day: number | null
  payment_day: number | null
  payment_month_offset: number
  tax_mode: string
  notes: string
}

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterType, setFilterType] = useState<'all' | 'company' | 'individual'>('all')
  const [showForm, setShowForm] = useState(false)
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null)
  const [formData, setFormData] = useState<CustomerFormData>({
    name: '',
    code: '',
    is_individual: false,
    postal_code: '',
    address: '',
    billing_address: '',
    phone: '',
    email: '',
    contact_name: '',
    contact_email: '',
    payment_terms: '',
    closing_day: null,
    payment_day: null,
    payment_month_offset: 1,
    tax_mode: 'inclusive',
    notes: ''
  })

  useEffect(() => {
    fetchCustomers()
  }, [filterType])

  const fetchCustomers = async () => {
    try {
      setLoading(true)
      let url = 'http://localhost:8100/api/v1/customers/?limit=1000'
      if (filterType !== 'all') {
        url += `&is_individual=${filterType === 'individual'}`
      }
      const response = await fetch(url)
      if (response.ok) {
        const data = await response.json()
        setCustomers(data)
      }
    } catch (error) {
      console.error('Failed to fetch customers:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const url = editingCustomer
        ? `http://localhost:8100/api/v1/customers/${editingCustomer.id}`
        : 'http://localhost:8100/api/v1/customers/'

      const response = await fetch(url, {
        method: editingCustomer ? 'PUT' : 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      })

      if (response.ok) {
        await fetchCustomers()
        resetForm()
        setShowForm(false)
      } else {
        const error = await response.json()
        alert(error.detail || '保存に失敗しました')
      }
    } catch (error) {
      console.error('Failed to save customer:', error)
      alert('保存に失敗しました')
    }
  }

  const handleEdit = (customer: Customer) => {
    setEditingCustomer(customer)
    setFormData({
      name: customer.name,
      code: customer.code || '',
      is_individual: customer.is_individual,
      postal_code: customer.postal_code || '',
      address: customer.address || '',
      billing_address: customer.billing_address || '',
      phone: customer.phone || '',
      email: customer.email || '',
      contact_name: customer.contact_name || '',
      contact_email: customer.contact_email || '',
      payment_terms: customer.payment_terms || '',
      closing_day: customer.closing_day,
      payment_day: customer.payment_day,
      payment_month_offset: customer.payment_month_offset || 1,
      tax_mode: customer.tax_mode || 'inclusive',
      notes: customer.notes || ''
    })
    setShowForm(true)
  }

  const handleDelete = async (customerId: number) => {
    if (!confirm('この取引先を削除してもよろしいですか？')) return

    try {
      const response = await fetch(`http://localhost:8100/api/v1/customers/${customerId}`, {
        method: 'DELETE',
      })

      if (response.ok) {
        await fetchCustomers()
      } else {
        alert('削除に失敗しました')
      }
    } catch (error) {
      console.error('Failed to delete customer:', error)
      alert('削除に失敗しました')
    }
  }

  const resetForm = () => {
    setEditingCustomer(null)
    setFormData({
      name: '',
      code: '',
      is_individual: false,
      postal_code: '',
      address: '',
      billing_address: '',
      phone: '',
      email: '',
      contact_name: '',
      contact_email: '',
      payment_terms: '',
      closing_day: null,
      payment_day: null,
      payment_month_offset: 1,
      tax_mode: 'inclusive',
      notes: ''
    })
  }

  const filteredCustomers = customers.filter(customer =>
    customer.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="min-h-screen bg-surface">
      <div className="container mx-auto px-6 py-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-ink">取引先会社管理</h1>
          <button
            onClick={() => { resetForm(); setShowForm(true) }}
            className="bg-accent text-white px-4 py-2 rounded-lg hover:bg-accent/90 transition-colors"
          >
            + 新規登録
          </button>
        </div>

        {/* Search & Filter */}
        <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
          <div className="flex gap-4">
            <input
              type="text"
              placeholder="取引先名で検索..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="flex-1 px-4 py-2 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
            />
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value as any)}
              className="px-4 py-2 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
            >
              <option value="all">すべて</option>
              <option value="company">法人のみ</option>
              <option value="individual">個人のみ</option>
            </select>
          </div>
        </div>

        {/* Form Modal */}
        {showForm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <h2 className="text-2xl font-bold text-ink mb-6">
                  {editingCustomer ? '取引先編集' : '取引先新規登録'}
                </h2>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-ink mb-2">
                      会社名・個人名 *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="w-full px-4 py-2 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-ink mb-2">
                        顧客コード
                      </label>
                      <input
                        type="text"
                        value={formData.code}
                        onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                        className="w-full px-4 py-2 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-ink mb-2">
                        種別
                      </label>
                      <select
                        value={formData.is_individual ? 'individual' : 'company'}
                        onChange={(e) => setFormData({ ...formData, is_individual: e.target.value === 'individual' })}
                        className="w-full px-4 py-2 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                      >
                        <option value="company">法人</option>
                        <option value="individual">個人</option>
                      </select>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-ink mb-2">
                        郵便番号
                      </label>
                      <input
                        type="text"
                        value={formData.postal_code}
                        onChange={(e) => setFormData({ ...formData, postal_code: e.target.value })}
                        className="w-full px-4 py-2 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                        placeholder="123-4567"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-ink mb-2">
                        電話番号
                      </label>
                      <input
                        type="text"
                        value={formData.phone}
                        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                        className="w-full px-4 py-2 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                        placeholder="06-1234-5678"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-ink mb-2">
                      住所
                    </label>
                    <input
                      type="text"
                      value={formData.address}
                      onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                      className="w-full px-4 py-2 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-ink mb-2">
                      請求先住所（住所と異なる場合）
                    </label>
                    <input
                      type="text"
                      value={formData.billing_address}
                      onChange={(e) => setFormData({ ...formData, billing_address: e.target.value })}
                      className="w-full px-4 py-2 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-ink mb-2">
                        メールアドレス
                      </label>
                      <input
                        type="email"
                        value={formData.email}
                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                        className="w-full px-4 py-2 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-ink mb-2">
                        担当者名
                      </label>
                      <input
                        type="text"
                        value={formData.contact_name}
                        onChange={(e) => setFormData({ ...formData, contact_name: e.target.value })}
                        className="w-full px-4 py-2 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-ink mb-2">
                      担当者メールアドレス
                    </label>
                    <input
                      type="email"
                      value={formData.contact_email}
                      onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
                      className="w-full px-4 py-2 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-ink mb-2">
                        支払条件
                      </label>
                      <input
                        type="text"
                        value={formData.payment_terms}
                        onChange={(e) => setFormData({ ...formData, payment_terms: e.target.value })}
                        className="w-full px-4 py-2 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                        placeholder="例: 月末締め翌月末払い"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-ink mb-2">
                        税込/税抜
                      </label>
                      <select
                        value={formData.tax_mode}
                        onChange={(e) => setFormData({ ...formData, tax_mode: e.target.value })}
                        className="w-full px-4 py-2 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                      >
                        <option value="inclusive">税込</option>
                        <option value="exclusive">税抜</option>
                      </select>
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-ink mb-2">
                        締め日（0=月末）
                      </label>
                      <select
                        value={formData.closing_day ?? ''}
                        onChange={(e) => setFormData({ ...formData, closing_day: e.target.value ? parseInt(e.target.value) : null })}
                        className="w-full px-4 py-2 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                      >
                        <option value="">未設定</option>
                        <option value="0">月末</option>
                        {Array.from({length: 31}, (_, i) => i + 1).map(day => (
                          <option key={day} value={day}>{day}日</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-ink mb-2">
                        支払い日（0=月末）
                      </label>
                      <select
                        value={formData.payment_day ?? ''}
                        onChange={(e) => setFormData({ ...formData, payment_day: e.target.value ? parseInt(e.target.value) : null })}
                        className="w-full px-4 py-2 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                      >
                        <option value="">未設定</option>
                        <option value="0">月末</option>
                        {Array.from({length: 31}, (_, i) => i + 1).map(day => (
                          <option key={day} value={day}>{day}日</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-ink mb-2">
                        支払い月
                      </label>
                      <select
                        value={formData.payment_month_offset}
                        onChange={(e) => setFormData({ ...formData, payment_month_offset: parseInt(e.target.value) })}
                        className="w-full px-4 py-2 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                      >
                        <option value="0">当月</option>
                        <option value="1">翌月</option>
                        <option value="2">翌々月</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-ink mb-2">
                      備考
                    </label>
                    <textarea
                      value={formData.notes}
                      onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                      className="w-full px-4 py-2 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                      rows={3}
                    />
                  </div>

                  <div className="flex gap-3 pt-4">
                    <button
                      type="submit"
                      className="flex-1 bg-accent text-white px-4 py-2 rounded-lg hover:bg-accent/90 transition-colors"
                    >
                      保存
                    </button>
                    <button
                      type="button"
                      onClick={() => { setShowForm(false); resetForm() }}
                      className="flex-1 bg-gray-200 text-ink px-4 py-2 rounded-lg hover:bg-gray-300 transition-colors"
                    >
                      キャンセル
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}

        {/* Customers List */}
        {loading ? (
          <div className="bg-white rounded-lg shadow-sm p-8 text-center text-muted">
            読み込み中...
          </div>
        ) : filteredCustomers.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm p-8 text-center text-muted">
            取引先が登録されていません
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-sm overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-line">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    顧客コード
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    会社名・個人名
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    種別
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    電話番号
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-muted uppercase tracking-wider">
                    メール
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-muted uppercase tracking-wider">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-line">
                {filteredCustomers.map((customer) => (
                  <tr key={customer.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-muted">
                      {customer.code || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-ink">
                      {customer.name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-muted">
                      <span className={`inline-flex px-2 py-1 text-xs rounded-full ${
                        customer.is_individual
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-green-100 text-green-800'
                      }`}>
                        {customer.is_individual ? '個人' : '法人'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-muted">
                      {customer.phone || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-muted">
                      {customer.email || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => handleEdit(customer)}
                        className="text-accent hover:text-accent/80 mr-4"
                      >
                        編集
                      </button>
                      <button
                        onClick={() => handleDelete(customer.id)}
                        className="text-red-600 hover:text-red-800"
                      >
                        削除
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Summary */}
        <div className="mt-4 text-sm text-muted">
          全{filteredCustomers.length}件
        </div>
      </div>
    </div>
  )
}
