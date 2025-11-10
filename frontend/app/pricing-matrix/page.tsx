'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

interface Customer {
  id: number
  name: string
  code: string
  is_individual: boolean
}

interface Product {
  id: number
  sku: string
  name: string
  default_price: string
}

interface PricingRule {
  id: number
  customer_id: number
  product_id?: number
  product_type_keyword?: string
  price: string
  priority: number
}

interface PriceCell {
  ruleId?: number
  price: string
  isEditing: boolean
}

export default function PricingMatrixPage() {
  const [customers, setCustomers] = useState<Customer[]>([])
  const [products, setProducts] = useState<Product[]>([])
  const [pricingRules, setPricingRules] = useState<PricingRule[]>([])
  const [priceMatrix, setPriceMatrix] = useState<{[key: string]: PriceCell}>({})
  const [loading, setLoading] = useState(true)
  const [editingProductType, setEditingProductType] = useState<{[key: number]: string}>({})
  const [editingProductTypeMode, setEditingProductTypeMode] = useState<{[key: number]: boolean}>({})

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [customersRes, productsRes, rulesRes] = await Promise.all([
        fetch('http://localhost:8100/api/v1/settings/customers'),
        fetch('http://localhost:8100/api/v1/products/?limit=1000'),
        fetch('http://localhost:8100/api/v1/pricing-rules/')
      ])

      if (customersRes.ok) setCustomers(await customersRes.json())
      if (productsRes.ok) {
        const rawProducts = await productsRes.json()
        // Decimal型をString型に変換
        const productsWithStringPrices = rawProducts.map((p: any) => ({
          ...p,
          default_price: String(p.default_price)
        }))
        setProducts(productsWithStringPrices)
      }
      if (rulesRes.ok) {
        const rawRules = await rulesRes.json()
        // Decimal型をString型に変換
        const rulesWithStringPrices = rawRules.map((r: any) => ({
          ...r,
          price: String(r.price)
        }))
        setPricingRules(rulesWithStringPrices)

        // 価格マトリクスを構築
        const matrix: {[key: string]: PriceCell} = {}
        rulesWithStringPrices.forEach((rule: PricingRule) => {
          const key = `${rule.customer_id}-${rule.product_type_keyword || rule.product_id}`
          matrix[key] = {
            ruleId: rule.id,
            price: String(rule.price),
            isEditing: false
          }
        })
        setPriceMatrix(matrix)
      }
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }

  const getPrice = (customerId: number, productKey: string): PriceCell => {
    const key = `${customerId}-${productKey}`
    return priceMatrix[key] || { price: '', isEditing: false }
  }

  const updatePrice = (customerId: number, productKey: string, price: string) => {
    const key = `${customerId}-${productKey}`
    setPriceMatrix(prev => ({
      ...prev,
      [key]: { ...prev[key], price, isEditing: true }
    }))
  }

  const savePrice = async (customerId: number, product: Product) => {
    const key = `${customerId}-${product.name}`
    const cell = priceMatrix[key]

    if (!cell || !cell.price) {
      alert('価格を入力してください')
      return
    }

    try {
      // 既存のルールがある場合は更新、ない場合は新規作成
      if (cell.ruleId) {
        // 更新（PUT）
        const response = await fetch(`http://localhost:8100/api/v1/pricing-rules/${cell.ruleId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            price: parseFloat(cell.price),
            priority: 0
          })
        })

        if (response.ok) {
          alert('更新しました')
          loadData() // リロード
        } else {
          const error = await response.json()
          alert(`更新に失敗: ${error.detail || JSON.stringify(error)}`)
        }
      } else {
        // 新規作成（POST）
        const response = await fetch('http://localhost:8100/api/v1/pricing-rules/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            customer_id: customerId,
            product_type_keyword: product.name,
            price: parseFloat(cell.price),
            priority: 0
          })
        })

        if (response.ok) {
          alert('保存しました')
          loadData() // リロード
        } else {
          const error = await response.json()
          alert(`保存に失敗: ${error.detail || JSON.stringify(error)}`)
        }
      }
    } catch (error) {
      console.error('Failed to save price:', error)
      alert('保存に失敗しました')
    }
  }

  const deletePrice = async (ruleId: number) => {
    if (!confirm('この価格設定を削除しますか？')) return

    try {
      const response = await fetch(`http://localhost:8100/api/v1/pricing-rules/${ruleId}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        alert('削除しました')
        loadData()
      } else {
        alert('削除に失敗しました')
      }
    } catch (error) {
      console.error('Failed to delete price:', error)
      alert('削除に失敗しました')
    }
  }

  const startEditingProductType = (productId: number, currentName: string) => {
    setEditingProductTypeMode(prev => ({ ...prev, [productId]: true }))
    setEditingProductType(prev => ({ ...prev, [productId]: currentName }))
  }

  const cancelEditingProductType = (productId: number) => {
    setEditingProductTypeMode(prev => ({ ...prev, [productId]: false }))
    setEditingProductType(prev => ({ ...prev, [productId]: '' }))
  }

  const saveProductType = async (product: Product) => {
    const newProductType = editingProductType[product.id]

    if (!newProductType || newProductType.trim() === '') {
      alert('商品タイプを入力してください')
      return
    }

    if (newProductType === product.name) {
      // 変更がない場合は編集モード解除のみ
      cancelEditingProductType(product.id)
      return
    }

    try {
      // 1. 商品タイプ学習APIで学習させる
      const learnResponse = await fetch('http://localhost:8100/api/v1/product-types/learn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_name: product.name,
          product_type: newProductType,
          source: 'manual'
        })
      })

      if (!learnResponse.ok) {
        throw new Error('商品タイプの学習に失敗しました')
      }

      // 2. 商品マスタの商品名を更新
      const updateResponse = await fetch(`http://localhost:8100/api/v1/products/${product.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sku: product.sku,
          name: newProductType,
          default_price: parseFloat(product.default_price)
        })
      })

      if (!updateResponse.ok) {
        throw new Error('商品情報の更新に失敗しました')
      }

      alert('商品タイプを更新し、学習しました。次回から適用されます。')

      // 編集モード解除とデータリロード
      cancelEditingProductType(product.id)
      loadData()
    } catch (error) {
      console.error('Failed to save product type:', error)
      alert(`保存に失敗: ${error}`)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <p className="text-muted">読み込み中...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-line">
        <div className="max-w-7xl mx-auto px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-ink">会社別卸単価設定</h1>
              <p className="text-muted mt-1">商品タイプごとに会社別の卸単価を設定します</p>
            </div>
            <Link
              href="/products"
              className="px-4 py-2 border border-line rounded-lg hover:bg-gray-50 transition-colors"
            >
              商品管理に戻る
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-8 py-8">
        <div className="bg-white rounded-xl border border-line p-6">
          <div className="mb-4">
            <h2 className="text-lg font-bold text-ink mb-2">価格マトリクス</h2>
            <p className="text-sm text-muted">
              各セルをクリックして価格を入力し、「保存」ボタンで確定します
            </p>
            <p className="text-sm text-muted mt-1">
              💡 商品タイプ列の「✏️ 編集」ボタンで商品タイプを変更できます。変更すると自動的に学習され、次回のインポートから適用されます。
            </p>
          </div>

          {/* 価格マトリクステーブル */}
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="bg-gray-50">
                  <th className="px-4 py-3 text-left font-semibold text-ink border-r border-line sticky left-0 bg-gray-50 z-10">
                    商品タイプ
                  </th>
                  {customers.map((customer) => (
                    <th key={customer.id} className="px-4 py-3 text-center font-semibold text-ink border-r border-line whitespace-nowrap">
                      <div className="flex flex-col">
                        <span>{customer.name}</span>
                        <span className="text-xs text-muted font-normal">
                          {customer.is_individual ? '（個人）' : '（法人）'}
                        </span>
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {products.map((product) => (
                  <tr key={product.id} className="border-t border-line hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-ink border-r border-line sticky left-0 bg-white">
                      {editingProductTypeMode[product.id] ? (
                        <div className="flex items-center space-x-2">
                          <input
                            type="text"
                            value={editingProductType[product.id] || product.name}
                            onChange={(e) => setEditingProductType(prev => ({ ...prev, [product.id]: e.target.value }))}
                            className="px-2 py-1 text-sm border border-line rounded focus:outline-none focus:ring-2 focus:ring-accent"
                            placeholder="商品タイプ"
                          />
                          <button
                            onClick={() => saveProductType(product)}
                            className="px-2 py-1 text-xs bg-accent text-white rounded hover:bg-accent/90 transition-colors"
                            title="保存して学習"
                          >
                            保存
                          </button>
                          <button
                            onClick={() => cancelEditingProductType(product.id)}
                            className="px-2 py-1 text-xs bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
                            title="キャンセル"
                          >
                            キャンセル
                          </button>
                        </div>
                      ) : (
                        <div className="flex items-center justify-between">
                          <div>
                            <div className="whitespace-nowrap">{product.name}</div>
                            <div className="text-xs text-muted mt-1">
                              標準: ¥{parseFloat(product.default_price).toLocaleString()}
                            </div>
                          </div>
                          <button
                            onClick={() => startEditingProductType(product.id, product.name)}
                            className="ml-2 px-2 py-1 text-xs border border-line rounded hover:bg-gray-100 transition-colors"
                            title="商品タイプを編集"
                          >
                            ✏️ 編集
                          </button>
                        </div>
                      )}
                    </td>
                    {customers.map((customer) => {
                      const cell = getPrice(customer.id, product.name)
                      return (
                        <td key={customer.id} className="px-2 py-2 border-r border-line text-center">
                          <div className="flex items-center justify-center space-x-2">
                            <input
                              type="number"
                              value={cell.price}
                              onChange={(e) => updatePrice(customer.id, product.name, e.target.value)}
                              placeholder="未設定"
                              className="w-24 px-2 py-1 text-sm border border-line rounded focus:outline-none focus:ring-2 focus:ring-accent text-center"
                            />
                            {cell.price && (
                              <div className="flex space-x-1">
                                <button
                                  onClick={() => savePrice(customer.id, product)}
                                  className="px-2 py-1 text-xs bg-accent text-white rounded hover:bg-accent/90 transition-colors"
                                  title="保存"
                                >
                                  保存
                                </button>
                                {cell.ruleId && (
                                  <button
                                    onClick={() => deletePrice(cell.ruleId!)}
                                    className="px-2 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
                                    title="削除"
                                  >
                                    削除
                                  </button>
                                )}
                              </div>
                            )}
                          </div>
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {products.length === 0 && (
            <div className="text-center py-12">
              <p className="text-muted">商品が登録されていません</p>
              <Link
                href="/products"
                className="mt-4 inline-block px-4 py-2 bg-accent text-white rounded-lg hover:bg-accent/90 transition-colors"
              >
                商品を登録する
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
