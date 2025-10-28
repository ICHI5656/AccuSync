'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

interface Product {
  id: number
  sku: string
  name: string
  default_price: string
  tax_rate: string
  tax_category: string
  unit: string
  is_active: boolean
  created_at: string
  updated_at: string
}

interface PricingRule {
  id: number
  customer_id: number
  customer_name: string
  product_id: number
  product_sku: string
  product_name: string
  price: string
  min_qty: number | null
  start_date: string | null
  end_date: string | null
  priority: number
}

interface ProductFormData {
  sku: string
  name: string
  default_price: string
  tax_rate: string
  tax_category: string
  unit: string
  is_active: boolean
}

interface PricingFormData {
  customer_id: string
  product_id: number
  price: string
  min_qty: string
  start_date: string
  end_date: string
  priority: string
}

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [filterActive, setFilterActive] = useState<boolean | null>(null)

  // Product form state
  const [showProductForm, setShowProductForm] = useState(false)
  const [editingProduct, setEditingProduct] = useState<Product | null>(null)
  const [productFormData, setProductFormData] = useState<ProductFormData>({
    sku: '',
    name: '',
    default_price: '',
    tax_rate: '0.10',
    tax_category: 'standard',
    unit: '個',
    is_active: true
  })

  // Pricing rules state
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null)
  const [pricingRules, setPricingRules] = useState<PricingRule[]>([])
  const [showPricingForm, setShowPricingForm] = useState(false)
  const [pricingFormData, setPricingFormData] = useState<PricingFormData>({
    customer_id: '',
    product_id: 0,
    price: '',
    min_qty: '',
    start_date: '',
    end_date: '',
    priority: '0'
  })

  // Customers for pricing rules
  const [customers, setCustomers] = useState<Array<{id: number, name: string}>>([])

  useEffect(() => {
    loadProducts()
    loadCustomers()
  }, [searchQuery, filterActive])

  const loadProducts = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams()
      if (searchQuery) params.append('search', searchQuery)
      if (filterActive !== null) params.append('is_active', String(filterActive))

      const response = await fetch(`http://localhost:8100/api/v1/products/?${params}`)
      if (response.ok) {
        const data = await response.json()
        setProducts(data)
      }
    } catch (error) {
      console.error('Failed to load products:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadCustomers = async () => {
    try {
      const response = await fetch('http://localhost:8100/api/v1/orders/customers')
      if (response.ok) {
        const data = await response.json()
        setCustomers(data)
      }
    } catch (error) {
      console.error('Failed to load customers:', error)
    }
  }

  const loadPricingRules = async (productId: number) => {
    try {
      const response = await fetch(`http://localhost:8100/api/v1/products/${productId}/pricing`)
      if (response.ok) {
        const data = await response.json()
        setPricingRules(data)
      }
    } catch (error) {
      console.error('Failed to load pricing rules:', error)
    }
  }

  const handleCreateProduct = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const response = await fetch('http://localhost:8100/api/v1/products/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(productFormData)
      })

      if (response.ok) {
        setShowProductForm(false)
        resetProductForm()
        loadProducts()
        alert('商品を作成しました')
      } else {
        const error = await response.json()
        alert(`エラー: ${error.detail}`)
      }
    } catch (error) {
      console.error('Failed to create product:', error)
      alert('商品作成に失敗しました')
    }
  }

  const handleUpdateProduct = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!editingProduct) return

    try {
      const response = await fetch(`http://localhost:8100/api/v1/products/${editingProduct.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(productFormData)
      })

      if (response.ok) {
        setShowProductForm(false)
        setEditingProduct(null)
        resetProductForm()
        loadProducts()
        alert('商品を更新しました')
      } else {
        const error = await response.json()
        alert(`エラー: ${error.detail}`)
      }
    } catch (error) {
      console.error('Failed to update product:', error)
      alert('商品更新に失敗しました')
    }
  }

  const handleDeleteProduct = async (productId: number) => {
    if (!confirm('この商品を無効化しますか？')) return

    try {
      const response = await fetch(`http://localhost:8100/api/v1/products/${productId}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        loadProducts()
        alert('商品を無効化しました')
      } else {
        const error = await response.json()
        alert(`エラー: ${error.detail}`)
      }
    } catch (error) {
      console.error('Failed to delete product:', error)
      alert('商品削除に失敗しました')
    }
  }

  const handleCreatePricingRule = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const response = await fetch('http://localhost:8100/api/v1/products/pricing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_id: parseInt(pricingFormData.customer_id),
          product_id: pricingFormData.product_id,
          price: pricingFormData.price,
          min_qty: pricingFormData.min_qty ? parseInt(pricingFormData.min_qty) : null,
          start_date: pricingFormData.start_date || null,
          end_date: pricingFormData.end_date || null,
          priority: parseInt(pricingFormData.priority)
        })
      })

      if (response.ok) {
        setShowPricingForm(false)
        resetPricingForm()
        if (selectedProduct) {
          loadPricingRules(selectedProduct.id)
        }
        alert('価格ルールを作成しました')
      } else {
        const error = await response.json()
        alert(`エラー: ${error.detail}`)
      }
    } catch (error) {
      console.error('Failed to create pricing rule:', error)
      alert('価格ルール作成に失敗しました')
    }
  }

  const handleDeletePricingRule = async (ruleId: number) => {
    if (!confirm('この価格ルールを削除しますか？')) return

    try {
      const response = await fetch(`http://localhost:8100/api/v1/products/pricing/${ruleId}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        if (selectedProduct) {
          loadPricingRules(selectedProduct.id)
        }
        alert('価格ルールを削除しました')
      } else {
        const error = await response.json()
        alert(`エラー: ${error.detail}`)
      }
    } catch (error) {
      console.error('Failed to delete pricing rule:', error)
      alert('価格ルール削除に失敗しました')
    }
  }

  const openProductForm = (product?: Product) => {
    if (product) {
      setEditingProduct(product)
      setProductFormData({
        sku: product.sku,
        name: product.name,
        default_price: product.default_price,
        tax_rate: product.tax_rate,
        tax_category: product.tax_category,
        unit: product.unit,
        is_active: product.is_active
      })
    } else {
      resetProductForm()
    }
    setShowProductForm(true)
  }

  const resetProductForm = () => {
    setProductFormData({
      sku: '',
      name: '',
      default_price: '',
      tax_rate: '0.10',
      tax_category: 'standard',
      unit: '個',
      is_active: true
    })
    setEditingProduct(null)
  }

  const openPricingForm = (product: Product) => {
    setSelectedProduct(product)
    loadPricingRules(product.id)
    setPricingFormData({
      customer_id: '',
      product_id: product.id,
      price: product.default_price,
      min_qty: '',
      start_date: '',
      end_date: '',
      priority: '0'
    })
    setShowPricingForm(true)
  }

  const resetPricingForm = () => {
    setPricingFormData({
      customer_id: '',
      product_id: 0,
      price: '',
      min_qty: '',
      start_date: '',
      end_date: '',
      priority: '0'
    })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="p-8">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8 flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">商品管理</h1>
              <p className="text-gray-600 mt-2">商品マスタの登録と顧客別価格設定を管理します</p>
            </div>
            <Link
              href="/pricing-matrix"
              className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors font-medium flex items-center space-x-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              <span>会社別卸単価設定</span>
            </Link>
          </div>

          {/* Search and Filter */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <div className="flex items-center space-x-4">
              <div className="flex-1">
                <input
                  type="text"
                  placeholder="商品名またはSKUで検索..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <select
                value={filterActive === null ? 'all' : filterActive ? 'active' : 'inactive'}
                onChange={(e) => setFilterActive(e.target.value === 'all' ? null : e.target.value === 'active')}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">すべて</option>
                <option value="active">有効のみ</option>
                <option value="inactive">無効のみ</option>
              </select>
              <button
                onClick={() => openProductForm()}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                ＋ 新規商品登録
              </button>
            </div>
          </div>

          {/* Products Table */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
            {loading ? (
              <div className="p-8 text-center text-gray-500">読み込み中...</div>
            ) : products.length === 0 ? (
              <div className="p-8 text-center text-gray-500">商品が見つかりません</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">SKU</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">商品名</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">標準単価</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">税率</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">単位</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">状態</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {products.map((product) => (
                      <tr key={product.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{product.sku}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{product.name}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">¥{parseFloat(product.default_price).toLocaleString()}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{(parseFloat(product.tax_rate) * 100).toFixed(0)}%</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{product.unit}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {product.is_active ? (
                            <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">
                              有効
                            </span>
                          ) : (
                            <span className="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-gray-100 text-gray-800">
                              無効
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                          <button
                            onClick={() => openProductForm(product)}
                            className="text-blue-600 hover:text-blue-900"
                          >
                            編集
                          </button>
                          <button
                            onClick={() => openPricingForm(product)}
                            className="text-purple-600 hover:text-purple-900"
                          >
                            価格設定
                          </button>
                          {product.is_active && (
                            <button
                              onClick={() => handleDeleteProduct(product.id)}
                              className="text-red-600 hover:text-red-900"
                            >
                              無効化
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Product Form Modal */}
      {showProductForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-2xl font-bold text-gray-900">
                {editingProduct ? '商品編集' : '新規商品登録'}
              </h2>
            </div>

            <form onSubmit={editingProduct ? handleUpdateProduct : handleCreateProduct} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  商品コード（SKU）<span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  disabled={!!editingProduct}
                  value={productFormData.sku}
                  onChange={(e) => setProductFormData({ ...productFormData, sku: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                  placeholder="例: PROD001"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  商品名<span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={productFormData.name}
                  onChange={(e) => setProductFormData({ ...productFormData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="例: サンプル商品A"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    標準単価<span className="text-red-500">*</span>
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={productFormData.default_price}
                    onChange={(e) => setProductFormData({ ...productFormData, default_price: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="1000"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    税率<span className="text-red-500">*</span>
                  </label>
                  <select
                    value={productFormData.tax_rate}
                    onChange={(e) => setProductFormData({ ...productFormData, tax_rate: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="0.10">10%（標準税率）</option>
                    <option value="0.08">8%（軽減税率）</option>
                    <option value="0.00">0%（非課税）</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    税区分
                  </label>
                  <select
                    value={productFormData.tax_category}
                    onChange={(e) => setProductFormData({ ...productFormData, tax_category: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="standard">標準</option>
                    <option value="reduced">軽減</option>
                    <option value="exempt">非課税</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    単位
                  </label>
                  <input
                    type="text"
                    value={productFormData.unit}
                    onChange={(e) => setProductFormData({ ...productFormData, unit: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="個"
                  />
                </div>
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_active"
                  checked={productFormData.is_active}
                  onChange={(e) => setProductFormData({ ...productFormData, is_active: e.target.checked })}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="is_active" className="ml-2 block text-sm text-gray-900">
                  有効
                </label>
              </div>

              <div className="flex justify-end space-x-3 pt-4 border-t border-gray-200">
                <button
                  type="button"
                  onClick={() => {
                    setShowProductForm(false)
                    resetProductForm()
                  }}
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  キャンセル
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  {editingProduct ? '更新' : '登録'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Pricing Rules Modal */}
      {selectedProduct && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-2xl font-bold text-gray-900">価格設定</h2>
              <p className="text-gray-600 mt-1">
                {selectedProduct.name} ({selectedProduct.sku}) - 標準単価: ¥{parseFloat(selectedProduct.default_price).toLocaleString()}
              </p>
            </div>

            <div className="p-6">
              {/* Add Pricing Rule Button */}
              {!showPricingForm && (
                <button
                  onClick={() => setShowPricingForm(true)}
                  className="mb-4 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                >
                  ＋ 顧客別価格を追加
                </button>
              )}

              {/* Pricing Rule Form */}
              {showPricingForm && (
                <form onSubmit={handleCreatePricingRule} className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">新規価格ルール</h3>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        取引先<span className="text-red-500">*</span>
                      </label>
                      <select
                        required
                        value={pricingFormData.customer_id}
                        onChange={(e) => setPricingFormData({ ...pricingFormData, customer_id: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                      >
                        <option value="">選択してください</option>
                        {customers.map((customer) => (
                          <option key={customer.id} value={customer.id}>{customer.name}</option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        適用単価<span className="text-red-500">*</span>
                      </label>
                      <input
                        type="number"
                        step="0.01"
                        required
                        value={pricingFormData.price}
                        onChange={(e) => setPricingFormData({ ...pricingFormData, price: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                        placeholder="800"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        最小数量（任意）
                      </label>
                      <input
                        type="number"
                        value={pricingFormData.min_qty}
                        onChange={(e) => setPricingFormData({ ...pricingFormData, min_qty: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                        placeholder="10"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        優先度
                      </label>
                      <input
                        type="number"
                        value={pricingFormData.priority}
                        onChange={(e) => setPricingFormData({ ...pricingFormData, priority: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                        placeholder="0"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        適用開始日（任意）
                      </label>
                      <input
                        type="date"
                        value={pricingFormData.start_date}
                        onChange={(e) => setPricingFormData({ ...pricingFormData, start_date: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        適用終了日（任意）
                      </label>
                      <input
                        type="date"
                        value={pricingFormData.end_date}
                        onChange={(e) => setPricingFormData({ ...pricingFormData, end_date: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                      />
                    </div>
                  </div>

                  <div className="flex justify-end space-x-3 mt-4">
                    <button
                      type="button"
                      onClick={() => {
                        setShowPricingForm(false)
                        resetPricingForm()
                      }}
                      className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                    >
                      キャンセル
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                    >
                      追加
                    </button>
                  </div>
                </form>
              )}

              {/* Pricing Rules List */}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">設定済み価格ルール</h3>
                {pricingRules.length === 0 ? (
                  <p className="text-gray-500 text-sm">顧客別価格は設定されていません</p>
                ) : (
                  <div className="space-y-3">
                    {pricingRules.map((rule) => (
                      <div key={rule.id} className="p-4 bg-white border border-gray-200 rounded-lg">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-3">
                              <h4 className="text-base font-semibold text-gray-900">{rule.customer_name}</h4>
                              <span className="text-lg font-bold text-purple-600">
                                ¥{parseFloat(rule.price).toLocaleString()}
                              </span>
                            </div>
                            <div className="mt-2 flex flex-wrap gap-2 text-xs text-gray-600">
                              {rule.min_qty && (
                                <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded">
                                  最小数量: {rule.min_qty}
                                </span>
                              )}
                              {rule.start_date && (
                                <span className="px-2 py-1 bg-green-50 text-green-700 rounded">
                                  開始: {rule.start_date}
                                </span>
                              )}
                              {rule.end_date && (
                                <span className="px-2 py-1 bg-orange-50 text-orange-700 rounded">
                                  終了: {rule.end_date}
                                </span>
                              )}
                              <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded">
                                優先度: {rule.priority}
                              </span>
                            </div>
                          </div>
                          <button
                            onClick={() => handleDeletePricingRule(rule.id)}
                            className="ml-4 text-red-600 hover:text-red-900 text-sm font-medium"
                          >
                            削除
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex justify-end mt-6 pt-4 border-t border-gray-200">
                <button
                  onClick={() => {
                    setSelectedProduct(null)
                    setPricingRules([])
                    setShowPricingForm(false)
                    resetPricingForm()
                  }}
                  className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  閉じる
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
