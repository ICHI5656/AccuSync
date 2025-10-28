'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'

interface Customer {
  id: number
  name: string
  closing_day: number | null
  payment_day: number | null
  payment_month_offset: number
}

export default function Home() {
  const [closingDayCustomers, setClosingDayCustomers] = useState<Customer[]>([])
  const [paymentDayCustomers, setPaymentDayCustomers] = useState<Customer[]>([])
  const [showClosingModal, setShowClosingModal] = useState(false)
  const [showPaymentModal, setShowPaymentModal] = useState(false)

  useEffect(() => {
    checkNotifications()
  }, [])

  const checkNotifications = async () => {
    try {
      const response = await fetch('http://localhost:8100/api/v1/customers/')
      if (!response.ok) return

      const customers: Customer[] = await response.json()
      const today = new Date()
      const todayDay = today.getDate()
      const isMonthEnd = todayDay === new Date(today.getFullYear(), today.getMonth() + 1, 0).getDate()

      // 締め日チェック
      const closingMatches = customers.filter(c => {
        if (c.closing_day === null) return false
        if (c.closing_day === 0) return isMonthEnd
        return c.closing_day === todayDay
      })

      // 支払い日チェック
      const paymentMatches = customers.filter(c => {
        if (c.payment_day === null) return false
        if (c.payment_day === 0) return isMonthEnd
        return c.payment_day === todayDay
      })

      if (closingMatches.length > 0) {
        setClosingDayCustomers(closingMatches)
        setShowClosingModal(true)
      }

      if (paymentMatches.length > 0) {
        setPaymentDayCustomers(paymentMatches)
        setShowPaymentModal(true)
      }
    } catch (error) {
      console.error('通知チェックエラー:', error)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-white to-[#f0f7f4]">
      {/* 締め日通知モーダル */}
      {showClosingModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-8 max-w-md w-full mx-4 shadow-2xl">
            <div className="flex items-center mb-4">
              <div className="w-12 h-12 rounded-full bg-accent/10 flex items-center justify-center mr-4">
                <svg className="w-6 h-6 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-2xl font-bold text-ink">📅 本日は締め日です</h3>
            </div>
            <p className="text-muted mb-4">以下の取引先の請求書を作成してください：</p>
            <div className="space-y-2 mb-6 max-h-60 overflow-y-auto">
              {closingDayCustomers.map(customer => (
                <div key={customer.id} className="p-3 bg-accent/5 rounded-lg">
                  <p className="font-semibold text-ink">{customer.name}</p>
                  <p className="text-sm text-muted">
                    締め日: {customer.closing_day === 0 ? '月末' : `${customer.closing_day}日`}
                  </p>
                </div>
              ))}
            </div>
            <button
              onClick={() => setShowClosingModal(false)}
              className="w-full bg-accent text-white py-3 rounded-lg font-semibold hover:bg-accent/90 transition-colors"
            >
              確認しました
            </button>
          </div>
        </div>
      )}

      {/* 支払い日通知モーダル */}
      {showPaymentModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-8 max-w-md w-full mx-4 shadow-2xl">
            <div className="flex items-center mb-4">
              <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center mr-4">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
              <h3 className="text-2xl font-bold text-ink">💰 本日は支払い日です</h3>
            </div>
            <p className="text-muted mb-4">以下の取引先からの入金を確認してください：</p>
            <div className="space-y-2 mb-6 max-h-60 overflow-y-auto">
              {paymentDayCustomers.map(customer => (
                <div key={customer.id} className="p-3 bg-green-50 rounded-lg">
                  <p className="font-semibold text-ink">{customer.name}</p>
                  <p className="text-sm text-muted">
                    支払い日: {customer.payment_day === 0 ? '月末' : `${customer.payment_day}日`}
                  </p>
                </div>
              ))}
            </div>
            <button
              onClick={() => setShowPaymentModal(false)}
              className="w-full bg-green-600 text-white py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors"
            >
              確認しました
            </button>
          </div>
        </div>
      )}

      <div className="max-w-4xl mx-auto px-6 py-16 text-center">
        {/* ロゴ部分 */}
        <div className="mb-8">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-3xl bg-accent/10 mb-4">
            <svg
              className="w-10 h-10 text-accent"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
          </div>
          <h1 className="text-5xl font-bold text-ink mb-4">
            AccuSync
            <span className="text-accent">（あきゅシンク）</span>
          </h1>
          <p className="text-xl text-muted">
            AI駆動の次世代請求書作成システム
          </p>
        </div>

        {/* 使い方ガイド */}
        <div className="mb-12 bg-white rounded-2xl p-6 shadow-md border border-line text-left">
          <h2 className="text-2xl font-bold mb-4 text-center">基本的な使い方</h2>
          <div className="space-y-3">
            <div className="flex items-start">
              <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-accent text-white font-bold mr-3 flex-shrink-0">1</span>
              <div>
                <p className="font-semibold">ファイルをアップロード</p>
                <p className="text-sm text-muted">CSV、Excel、PDF、TXTファイルをドラッグ&ドロップ</p>
              </div>
            </div>
            <div className="flex items-start">
              <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-accent text-white font-bold mr-3 flex-shrink-0">2</span>
              <div>
                <p className="font-semibold">プレビューで確認</p>
                <p className="text-sm text-muted">AIが自動解析したデータを事前確認</p>
              </div>
            </div>
            <div className="flex items-start">
              <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-accent text-white font-bold mr-3 flex-shrink-0">3</span>
              <div>
                <p className="font-semibold">インポート実行</p>
                <p className="text-sm text-muted">AIによる自動マッピングとデータ品質チェック</p>
              </div>
            </div>
            <div className="flex items-start">
              <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-accent text-white font-bold mr-3 flex-shrink-0">4</span>
              <div>
                <p className="font-semibold">DBに保存</p>
                <p className="text-sm text-muted">顧客・商品・注文データを自動的にデータベースに蓄積</p>
              </div>
            </div>
          </div>
        </div>

        {/* クイックアクセスボタン */}
        <div className="mb-12 grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Link
            href="/imports"
            className="group bg-white rounded-2xl p-8 shadow-md border-2 border-line hover:border-accent hover:shadow-lg transition-all"
          >
            <div className="w-16 h-16 rounded-xl bg-accent/10 flex items-center justify-center mb-4 mx-auto group-hover:bg-accent/20 transition-colors">
              <svg className="w-8 h-8 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <h3 className="font-bold text-xl mb-2">データ取り込み</h3>
            <p className="text-sm text-muted">ファイルアップロードとプレビュー</p>
          </Link>

          <Link
            href="/jobs"
            className="group bg-white rounded-2xl p-8 shadow-md border-2 border-line hover:border-accent hover:shadow-lg transition-all"
          >
            <div className="w-16 h-16 rounded-xl bg-accent/10 flex items-center justify-center mb-4 mx-auto group-hover:bg-accent/20 transition-colors">
              <svg className="w-8 h-8 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
            </div>
            <h3 className="font-bold text-xl mb-2">ジョブ一覧</h3>
            <p className="text-sm text-muted">処理状況確認とDB保存</p>
          </Link>

          <Link
            href="/products"
            className="group bg-white rounded-2xl p-8 shadow-md border-2 border-line hover:border-accent hover:shadow-lg transition-all"
          >
            <div className="w-16 h-16 rounded-xl bg-accent/10 flex items-center justify-center mb-4 mx-auto group-hover:bg-accent/20 transition-colors">
              <svg className="w-8 h-8 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
              </svg>
            </div>
            <h3 className="font-bold text-xl mb-2">商品管理</h3>
            <p className="text-sm text-muted">商品登録と顧客別価格設定</p>
          </Link>

          <Link
            href="/pricing-matrix"
            className="group bg-white rounded-2xl p-8 shadow-md border-2 border-line hover:border-purple-600 hover:shadow-lg transition-all"
          >
            <div className="w-16 h-16 rounded-xl bg-purple-100 flex items-center justify-center mb-4 mx-auto group-hover:bg-purple-200 transition-colors">
              <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </div>
            <h3 className="font-bold text-xl mb-2">会社別卸単価</h3>
            <p className="text-sm text-muted">顧客ごとの価格設定マトリクス</p>
          </Link>
        </div>

        {/* 機能カード */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          <div className="bg-white rounded-2xl p-6 shadow-md border border-line hover:shadow-lg transition-shadow">
            <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center mb-4 mx-auto">
              <svg className="w-6 h-6 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
            </div>
            <h3 className="font-bold text-lg mb-2">多様な形式に対応</h3>
            <p className="text-sm text-muted">CSV、Excel、PDF、TXT、画像から自動でデータを抽出</p>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-md border border-line hover:shadow-lg transition-shadow">
            <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center mb-4 mx-auto">
              <svg className="w-6 h-6 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <h3 className="font-bold text-lg mb-2">AI自動処理</h3>
            <p className="text-sm text-muted">OpenAI/Claudeで賢くデータを理解し、自動マッピング</p>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-md border border-line hover:shadow-lg transition-shadow">
            <div className="w-12 h-12 rounded-xl bg-accent/10 flex items-center justify-center mb-4 mx-auto">
              <svg className="w-6 h-6 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="font-bold text-lg mb-2">美しい帳票出力</h3>
            <p className="text-sm text-muted">ソフトグリーン基調の請求書・納品書PDFを自動生成</p>
          </div>
        </div>

        {/* システム機能 */}
        <div className="bg-white rounded-2xl p-8 shadow-md border border-line">
          <h2 className="text-2xl font-bold mb-6">実装済み機能</h2>
          <div className="grid md:grid-cols-2 gap-4 text-left">
            <div className="flex items-center justify-between p-4 bg-accent/5 rounded-xl">
              <span className="font-semibold">ファイルパース</span>
              <span className="px-3 py-1 bg-accent text-white text-sm rounded-full">✓ 完了</span>
            </div>
            <div className="flex items-center justify-between p-4 bg-accent/5 rounded-xl">
              <span className="font-semibold">AI自動マッピング</span>
              <span className="px-3 py-1 bg-accent text-white text-sm rounded-full">✓ 完了</span>
            </div>
            <div className="flex items-center justify-between p-4 bg-accent/5 rounded-xl">
              <span className="font-semibold">データ品質チェック</span>
              <span className="px-3 py-1 bg-accent text-white text-sm rounded-full">✓ 完了</span>
            </div>
            <div className="flex items-center justify-between p-4 bg-accent/5 rounded-xl">
              <span className="font-semibold">DB自動保存</span>
              <span className="px-3 py-1 bg-accent text-white text-sm rounded-full">✓ 完了</span>
            </div>
            <div className="flex items-center justify-between p-4 bg-accent/5 rounded-xl">
              <span className="font-semibold">顧客データ蓄積</span>
              <span className="px-3 py-1 bg-accent text-white text-sm rounded-full">✓ 完了</span>
            </div>
            <div className="flex items-center justify-between p-4 bg-accent/5 rounded-xl">
              <span className="font-semibold">商品データ蓄積</span>
              <span className="px-3 py-1 bg-accent text-white text-sm rounded-full">✓ 完了</span>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t border-line">
            <a
              href="http://localhost:8100/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center px-6 py-3 bg-accent text-white rounded-xl font-semibold hover:bg-accent/90 transition-colors"
            >
              API ドキュメントを見る
              <svg className="w-5 h-5 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </a>
          </div>
        </div>

        {/* フッター */}
        <div className="mt-12 text-sm text-muted">
          <p>AccuSync v0.1.0 - Development Mode</p>
          <p className="mt-2">
            Frontend: <code className="px-2 py-1 bg-line rounded">localhost:3100</code> |
            Backend: <code className="px-2 py-1 bg-line rounded ml-2">localhost:8100</code>
          </p>
        </div>
      </div>
    </div>
  )
}
