'use client'

export default function InvoicesPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="p-8">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">📄 請求書管理</h1>
            <p className="text-gray-600 mt-2">請求書の作成・管理機能</p>
          </div>

          {/* Coming Soon Card */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12">
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-purple-100 mb-6">
                <svg
                  className="w-10 h-10 text-purple-600"
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

              <h2 className="text-2xl font-bold text-gray-900 mb-3">
                🚧 今後実装予定
              </h2>
              <p className="text-gray-600 mb-8 max-w-2xl mx-auto">
                請求書作成・管理機能は現在開発中です。
                <br />
                以下の機能を実装予定です。
              </p>

              {/* Planned Features */}
              <div className="grid md:grid-cols-2 gap-4 max-w-3xl mx-auto text-left">
                <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="flex items-start">
                    <svg
                      className="w-5 h-5 text-green-600 mr-3 mt-0.5 flex-shrink-0"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-1">
                        請求書PDF生成
                      </h3>
                      <p className="text-sm text-gray-600">
                        注文データから自動で請求書PDFを作成
                      </p>
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="flex items-start">
                    <svg
                      className="w-5 h-5 text-green-600 mr-3 mt-0.5 flex-shrink-0"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-1">
                        納品書PDF生成
                      </h3>
                      <p className="text-sm text-gray-600">
                        美しいソフトグリーンデザインの納品書
                      </p>
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="flex items-start">
                    <svg
                      className="w-5 h-5 text-green-600 mr-3 mt-0.5 flex-shrink-0"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-1">
                        インボイス制度対応
                      </h3>
                      <p className="text-sm text-gray-600">
                        適格請求書登録番号の記載
                      </p>
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="flex items-start">
                    <svg
                      className="w-5 h-5 text-green-600 mr-3 mt-0.5 flex-shrink-0"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-1">
                        請求書一覧・検索
                      </h3>
                      <p className="text-sm text-gray-600">
                        期間・取引先での絞り込み機能
                      </p>
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="flex items-start">
                    <svg
                      className="w-5 h-5 text-green-600 mr-3 mt-0.5 flex-shrink-0"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-1">
                        メール送信機能
                      </h3>
                      <p className="text-sm text-gray-600">
                        請求書をメールで直接送信
                      </p>
                    </div>
                  </div>
                </div>

                <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="flex items-start">
                    <svg
                      className="w-5 h-5 text-green-600 mr-3 mt-0.5 flex-shrink-0"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    <div>
                      <h3 className="font-semibold text-gray-900 mb-1">
                        入金管理
                      </h3>
                      <p className="text-sm text-gray-600">
                        請求・入金ステータスの追跡
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Current Workaround */}
              <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg max-w-2xl mx-auto">
                <div className="flex items-start">
                  <svg
                    className="w-5 h-5 text-blue-600 mr-3 mt-0.5 flex-shrink-0"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  <div className="text-left">
                    <h3 className="font-semibold text-blue-900 mb-1">
                      現在の利用方法
                    </h3>
                    <p className="text-sm text-blue-800">
                      注文データは「注文一覧」から確認できます。
                      <br />
                      請求書作成が必要な場合は、注文データをCSVエクスポートして外部ツールをご利用ください。
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
