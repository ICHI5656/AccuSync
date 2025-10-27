'use client'

import { useState, useEffect } from 'react'

interface DatabaseStats {
  companies: number
  individuals: number
  products: number
  orders: number
  connection_status: string
}

interface IssuerInfo {
  id: number
  name: string
  brand_name: string | null
  tax_id: string | null
  address: string | null
  tel: string | null
  email: string | null
  bank_info: string | null
  invoice_notes: string | null
}

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('ai')
  const [dbStats, setDbStats] = useState<DatabaseStats | null>(null)
  const [issuerInfo, setIssuerInfo] = useState<IssuerInfo | null>(null)

  useEffect(() => {
    if (activeTab === 'database') {
      fetchDatabaseStats()
    } else if (activeTab === 'issuer') {
      fetchIssuerInfo()
    }
  }, [activeTab])

  const fetchDatabaseStats = async () => {
    try {
      const response = await fetch('http://localhost:8100/api/v1/settings/stats')
      const data = await response.json()
      setDbStats(data)
    } catch (error) {
      console.error('Failed to fetch database stats:', error)
    }
  }

  const fetchIssuerInfo = async () => {
    try {
      const response = await fetch('http://localhost:8100/api/v1/settings/issuer')
      const data = await response.json()
      setIssuerInfo(data)
    } catch (error) {
      console.error('Failed to fetch issuer info:', error)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-white to-[#f0f7f4] py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-ink">システム設定</h1>
          <p className="mt-2 text-muted">AccuSyncの各種設定を確認・変更できます</p>
        </div>

        {/* タブナビゲーション */}
        <div className="bg-white rounded-t-2xl border border-line">
          <div className="flex border-b border-line">
            <button
              onClick={() => setActiveTab('ai')}
              className={`px-6 py-4 font-semibold transition-colors ${
                activeTab === 'ai'
                  ? 'text-accent border-b-2 border-accent'
                  : 'text-muted hover:text-ink'
              }`}
            >
              AI設定
            </button>
            <button
              onClick={() => setActiveTab('issuer')}
              className={`px-6 py-4 font-semibold transition-colors ${
                activeTab === 'issuer'
                  ? 'text-accent border-b-2 border-accent'
                  : 'text-muted hover:text-ink'
              }`}
            >
              請求者情報
            </button>
            <button
              onClick={() => setActiveTab('import')}
              className={`px-6 py-4 font-semibold transition-colors ${
                activeTab === 'import'
                  ? 'text-accent border-b-2 border-accent'
                  : 'text-muted hover:text-ink'
              }`}
            >
              インポート設定
            </button>
            <button
              onClick={() => setActiveTab('database')}
              className={`px-6 py-4 font-semibold transition-colors ${
                activeTab === 'database'
                  ? 'text-accent border-b-2 border-accent'
                  : 'text-muted hover:text-ink'
              }`}
            >
              データベース
            </button>
          </div>

          {/* タブコンテンツ */}
          <div className="p-8">
            {activeTab === 'ai' && <AISettings />}
            {activeTab === 'issuer' && <IssuerSettings issuerInfo={issuerInfo} onUpdate={fetchIssuerInfo} />}
            {activeTab === 'import' && <ImportSettings />}
            {activeTab === 'database' && <DatabaseSettings dbStats={dbStats} onRefresh={fetchDatabaseStats} />}
          </div>
        </div>
      </div>
    </div>
  )
}

function AISettings() {
  const [aiSettings, setAiSettings] = useState<{
    ai_provider: string
    has_api_key: boolean
    auto_mapping_enabled: boolean
    quality_check_enabled: boolean
    confidence_threshold: number
  } | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAISettings()
  }, [])

  const fetchAISettings = async () => {
    try {
      setLoading(true)
      const response = await fetch('http://localhost:8100/api/v1/settings/ai')
      if (response.ok) {
        const data = await response.json()
        setAiSettings(data)
      }
    } catch (error) {
      console.error('Failed to fetch AI settings:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="text-center py-8 text-muted">読み込み中...</div>
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold mb-4">AI設定</h2>
        <p className="text-sm text-muted mb-6">
          データ抽出、自動マッピング、品質チェックに使用するAIの設定
        </p>
      </div>

      {/* 設定状況の表示 */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
        <div className="flex items-start space-x-3">
          <svg className="w-5 h-5 text-blue-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div className="flex-1">
            <p className="text-sm font-semibold text-blue-900">環境変数で管理されています</p>
            <p className="text-xs text-blue-700 mt-1">
              AI設定は環境変数（.envファイル）で管理されています。設定を変更する場合は、.envファイルを編集してコンテナを再起動してください。
            </p>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-ink mb-2">
            AIプロバイダー
          </label>
          <div className="flex items-center space-x-3">
            <select
              value={aiSettings?.ai_provider || 'openai'}
              disabled
              className="w-full max-w-md px-4 py-2 border border-line rounded-lg bg-gray-50 text-muted"
            >
              <option value="openai">OpenAI (GPT-4o)</option>
              <option value="claude">Anthropic (Claude)</option>
            </select>
            <span className={`px-3 py-1 text-xs rounded-full font-semibold ${
              aiSettings?.has_api_key
                ? 'bg-green-100 text-green-700'
                : 'bg-red-100 text-red-700'
            }`}>
              {aiSettings?.has_api_key ? '✓ APIキー設定済み' : '✗ APIキー未設定'}
            </span>
          </div>
          <p className="mt-1 text-xs text-muted">
            環境変数: AI_PROVIDER={aiSettings?.ai_provider}
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-ink mb-2">
            APIキー状況
          </label>
          <div className="p-3 bg-gray-50 border border-line rounded-lg">
            <p className="text-sm text-muted">
              {aiSettings?.has_api_key ? (
                <>
                  <span className="text-green-600 font-semibold">✓ 設定済み</span>
                  <br />
                  <span className="text-xs">
                    環境変数: {aiSettings.ai_provider === 'openai' ? 'OPENAI_API_KEY' : 'ANTHROPIC_API_KEY'}
                  </span>
                </>
              ) : (
                <>
                  <span className="text-red-600 font-semibold">✗ 未設定</span>
                  <br />
                  <span className="text-xs">
                    .envファイルに {aiSettings?.ai_provider === 'openai' ? 'OPENAI_API_KEY' : 'ANTHROPIC_API_KEY'} を設定してください
                  </span>
                </>
              )}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <input
            type="checkbox"
            id="auto-mapping"
            checked={aiSettings?.auto_mapping_enabled ?? true}
            disabled
            className="w-4 h-4 text-accent rounded focus:ring-2 focus:ring-accent opacity-50"
          />
          <label htmlFor="auto-mapping" className="text-sm font-medium text-ink">
            自動マッピング機能を有効化
          </label>
        </div>

        <div className="flex items-center space-x-3">
          <input
            type="checkbox"
            id="quality-check"
            checked={aiSettings?.quality_check_enabled ?? true}
            disabled
            className="w-4 h-4 text-accent rounded focus:ring-2 focus:ring-accent opacity-50"
          />
          <label htmlFor="quality-check" className="text-sm font-medium text-ink">
            データ品質チェックを有効化
          </label>
        </div>

        <div>
          <label className="block text-sm font-medium text-ink mb-2">
            信頼度閾値
          </label>
          <input
            type="number"
            min="0"
            max="1"
            step="0.1"
            value={aiSettings?.confidence_threshold ?? 0.8}
            disabled
            className="w-32 px-4 py-2 border border-line rounded-lg bg-gray-50 text-muted"
          />
          <p className="mt-1 text-xs text-muted">
            0.0 〜 1.0（現在: {aiSettings?.confidence_threshold ?? 0.8}）
          </p>
        </div>
      </div>

      <div className="pt-4 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <h3 className="text-sm font-semibold text-yellow-900 mb-2">設定変更方法</h3>
        <ol className="text-xs text-yellow-800 space-y-1 list-decimal list-inside">
          <li>.envファイルを編集（AI_PROVIDER, OPENAI_API_KEY, ANTHROPIC_API_KEYなど）</li>
          <li>docker-compose restart api celery_worker を実行</li>
          <li>このページをリロードして設定を確認</li>
        </ol>
      </div>
    </div>
  )
}

function IssuerSettings({ issuerInfo, onUpdate }: { issuerInfo: IssuerInfo | null, onUpdate: () => void }) {
  const [formData, setFormData] = useState({
    name: '',
    brand_name: '',
    tax_id: '',
    address: '',
    tel: '',
    email: '',
    bank_info: '',
    invoice_notes: ''
  })
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (issuerInfo) {
      setFormData({
        name: issuerInfo.name || '',
        brand_name: issuerInfo.brand_name || '',
        tax_id: issuerInfo.tax_id || '',
        address: issuerInfo.address || '',
        tel: issuerInfo.tel || '',
        email: issuerInfo.email || '',
        bank_info: issuerInfo.bank_info || '',
        invoice_notes: issuerInfo.invoice_notes || ''
      })
    }
  }, [issuerInfo])

  const handleSave = async () => {
    setSaving(true)
    try {
      const response = await fetch('http://localhost:8100/api/v1/settings/issuer', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      })

      if (response.ok) {
        alert('請求者情報を保存しました')
        onUpdate()
      } else {
        alert('保存に失敗しました')
      }
    } catch (error) {
      console.error('Save error:', error)
      alert('保存に失敗しました')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold mb-4">請求者情報</h2>
        <p className="text-sm text-muted mb-6">
          請求書に表示される自社情報の設定
        </p>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-ink mb-2">
            会社名 <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            placeholder="株式会社〇〇"
            className="w-full max-w-md px-4 py-2 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-ink mb-2">
            適格請求書登録番号
          </label>
          <input
            type="text"
            value={formData.tax_id}
            onChange={(e) => setFormData({ ...formData, tax_id: e.target.value })}
            placeholder="T1234567890123"
            className="w-full max-w-md px-4 py-2 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-ink mb-2">
            所在地
          </label>
          <textarea
            rows={3}
            value={formData.address}
            onChange={(e) => setFormData({ ...formData, address: e.target.value })}
            placeholder="〒123-4567&#10;東京都〇〇区〇〇 1-2-3"
            className="w-full max-w-md px-4 py-2 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-ink mb-2">
            電話番号
          </label>
          <input
            type="tel"
            value={formData.tel}
            onChange={(e) => setFormData({ ...formData, tel: e.target.value })}
            placeholder="03-1234-5678"
            className="w-full max-w-md px-4 py-2 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-ink mb-2">
            メールアドレス
          </label>
          <input
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            placeholder="info@example.com"
            className="w-full max-w-md px-4 py-2 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-ink mb-2">
            振込先情報
          </label>
          <textarea
            rows={4}
            value={formData.bank_info}
            onChange={(e) => setFormData({ ...formData, bank_info: e.target.value })}
            placeholder="銀行名: 〇〇銀行&#10;支店名: 〇〇支店&#10;口座種別: 普通&#10;口座番号: 1234567&#10;口座名義: カ）〇〇"
            className="w-full max-w-md px-4 py-2 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
          />
        </div>
      </div>

      <div className="pt-4">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-2 bg-accent text-white rounded-lg font-semibold hover:bg-accent/90 transition-colors disabled:opacity-50"
        >
          {saving ? '保存中...' : '設定を保存'}
        </button>
      </div>
    </div>
  )
}

function ImportSettings() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold mb-4">インポート設定</h2>
        <p className="text-sm text-muted mb-6">
          ファイル取り込み時の自動処理設定
        </p>
      </div>

      <div className="space-y-4">
        <div className="flex items-center space-x-3">
          <input
            type="checkbox"
            id="auto-register-customer"
            className="w-4 h-4 text-accent rounded focus:ring-2 focus:ring-accent"
            defaultChecked
          />
          <label htmlFor="auto-register-customer" className="text-sm font-medium text-ink">
            取引先会社を自動登録
          </label>
        </div>

        <div className="flex items-center space-x-3">
          <input
            type="checkbox"
            id="auto-register-individual"
            className="w-4 h-4 text-accent rounded focus:ring-2 focus:ring-accent"
            defaultChecked
          />
          <label htmlFor="auto-register-individual" className="text-sm font-medium text-ink">
            個人顧客を自動登録
          </label>
        </div>

        <div className="flex items-center space-x-3">
          <input
            type="checkbox"
            id="auto-register-product"
            className="w-4 h-4 text-accent rounded focus:ring-2 focus:ring-accent"
            defaultChecked
          />
          <label htmlFor="auto-register-product" className="text-sm font-medium text-ink">
            商品を自動登録
          </label>
        </div>

        <div className="flex items-center space-x-3">
          <input
            type="checkbox"
            id="ai-judge-type"
            className="w-4 h-4 text-accent rounded focus:ring-2 focus:ring-accent"
            defaultChecked
          />
          <label htmlFor="ai-judge-type" className="text-sm font-medium text-ink">
            AIで会社・個人を自動判定
          </label>
        </div>

        <div>
          <label className="block text-sm font-medium text-ink mb-2">
            デフォルト文字エンコーディング
          </label>
          <select className="w-full max-w-md px-4 py-2 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent">
            <option value="auto">自動検出</option>
            <option value="utf-8">UTF-8</option>
            <option value="shift-jis">Shift-JIS</option>
            <option value="euc-jp">EUC-JP</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-ink mb-2">
            対応ファイル形式
          </label>
          <div className="space-y-2">
            <div className="flex items-center space-x-3">
              <input type="checkbox" id="csv" className="w-4 h-4 text-accent rounded" defaultChecked disabled />
              <label htmlFor="csv" className="text-sm text-muted">CSV (.csv)</label>
            </div>
            <div className="flex items-center space-x-3">
              <input type="checkbox" id="excel" className="w-4 h-4 text-accent rounded" defaultChecked disabled />
              <label htmlFor="excel" className="text-sm text-muted">Excel (.xlsx, .xls)</label>
            </div>
            <div className="flex items-center space-x-3">
              <input type="checkbox" id="pdf" className="w-4 h-4 text-accent rounded" defaultChecked disabled />
              <label htmlFor="pdf" className="text-sm text-muted">PDF (.pdf)</label>
            </div>
            <div className="flex items-center space-x-3">
              <input type="checkbox" id="txt" className="w-4 h-4 text-accent rounded" defaultChecked disabled />
              <label htmlFor="txt" className="text-sm text-muted">テキスト (.txt)</label>
            </div>
          </div>
        </div>
      </div>

      <div className="pt-4">
        <button className="px-6 py-2 bg-accent text-white rounded-lg font-semibold hover:bg-accent/90 transition-colors">
          設定を保存
        </button>
      </div>
    </div>
  )
}

function DatabaseSettings({ dbStats, onRefresh }: { dbStats: DatabaseStats | null, onRefresh: () => void }) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold mb-4">データベース状況</h2>
        <p className="text-sm text-muted mb-6">
          データベースの接続状態とデータ統計
        </p>
      </div>

      <div className="bg-accent/5 rounded-xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <span className="font-semibold">接続状態</span>
          <span className={`px-3 py-1 text-sm rounded-full font-semibold ${
            dbStats?.connection_status === 'connected'
              ? 'bg-green-100 text-green-700'
              : 'bg-red-100 text-red-700'
          }`}>
            {dbStats?.connection_status === 'connected' ? '✓ 接続中' : '✗ 切断'}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="font-semibold">データベース</span>
          <span className="text-muted">PostgreSQL 16</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="font-semibold">ホスト</span>
          <span className="text-muted">db:5432</span>
        </div>
      </div>

      <div>
        <h3 className="font-semibold mb-4">データ統計</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white border border-line rounded-xl p-4">
            <div className="text-2xl font-bold text-accent">{dbStats?.companies ?? '-'}</div>
            <div className="text-sm text-muted mt-1">取引先会社</div>
          </div>
          <div className="bg-white border border-line rounded-xl p-4">
            <div className="text-2xl font-bold text-accent">{dbStats?.individuals ?? '-'}</div>
            <div className="text-sm text-muted mt-1">個人顧客</div>
          </div>
          <div className="bg-white border border-line rounded-xl p-4">
            <div className="text-2xl font-bold text-accent">{dbStats?.products ?? '-'}</div>
            <div className="text-sm text-muted mt-1">商品</div>
          </div>
          <div className="bg-white border border-line rounded-xl p-4">
            <div className="text-2xl font-bold text-accent">{dbStats?.orders ?? '-'}</div>
            <div className="text-sm text-muted mt-1">注文</div>
          </div>
        </div>
      </div>

      <div className="pt-4">
        <button
          onClick={onRefresh}
          className="px-6 py-2 bg-muted/20 text-ink rounded-lg font-semibold hover:bg-muted/30 transition-colors"
        >
          統計を更新
        </button>
      </div>
    </div>
  )
}
