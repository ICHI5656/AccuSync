'use client'

import { useState, useEffect } from 'react'

interface Job {
  id: number
  filename: string
  file_type: string
  status: string
  total_rows: number | null
  processed_rows: number | null
  error_count: number | null
  warnings: string[]
  errors: string[]
  created_at: string
  updated_at: string
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchJobs()
    const interval = setInterval(fetchJobs, 5000) // 5秒ごとに更新
    return () => clearInterval(interval)
  }, [])

  const fetchJobs = async () => {
    try {
      const response = await fetch('http://localhost:8100/api/v1/imports/jobs')
      const data = await response.json()
      setJobs(data)
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch jobs:', error)
      setLoading(false)
    }
  }

  const handleImportData = async (jobId: number) => {
    try {
      const response = await fetch(`http://localhost:8100/api/v1/imports/jobs/${jobId}/import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: jobId,
          validate_only: false
        })
      })

      const result = await response.json()
      if (result.success) {
        alert(`データインポート成功: ${result.imported_rows}行`)
        fetchJobs()
      } else {
        alert(`エラー: ${result.errors?.join(', ')}`)
      }
    } catch (error) {
      alert(`エラー: ${error}`)
    }
  }

  const handleDeleteJob = async (jobId: number) => {
    if (!confirm('このジョブを削除しますか？')) return

    try {
      await fetch(`http://localhost:8100/api/v1/imports/jobs/${jobId}`, {
        method: 'DELETE'
      })
      fetchJobs()
    } catch (error) {
      alert(`削除エラー: ${error}`)
    }
  }

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-gray-100 text-gray-800',
      processing: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800'
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
      pending: '待機中',
      processing: '処理中',
      completed: '完了',
      failed: '失敗'
    }
    return texts[status] || status
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent mx-auto mb-4"></div>
          <p className="text-muted">読み込み中...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-ink mb-2">インポートジョブ一覧</h1>
          <p className="text-muted">ファイルインポートの処理状況を確認できます</p>
        </div>

        {jobs.length === 0 ? (
          <div className="bg-white rounded-xl border border-line p-12 text-center">
            <svg className="w-16 h-16 mx-auto mb-4 text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-ink font-medium mb-2">ジョブがありません</p>
            <p className="text-sm text-muted">データ取り込みページでファイルをアップロードしてください</p>
          </div>
        ) : (
          <div className="space-y-4">
            {jobs.map(job => (
              <div key={job.id} className="bg-white rounded-xl border border-line p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-lg font-semibold text-ink">{job.filename}</h3>
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusBadge(job.status)}`}>
                        {getStatusText(job.status)}
                      </span>
                    </div>
                    <div className="flex items-center space-x-6 text-sm text-muted">
                      <span>ジョブID: {job.id}</span>
                      <span>形式: {job.file_type.toUpperCase()}</span>
                      {job.total_rows !== null && <span>総行数: {job.total_rows}行</span>}
                      {job.processed_rows !== null && <span>処理済み: {job.processed_rows}行</span>}
                    </div>
                    <div className="mt-2 text-xs text-muted">
                      作成: {new Date(job.created_at).toLocaleString('ja-JP')}
                      {' | '}
                      更新: {new Date(job.updated_at).toLocaleString('ja-JP')}
                    </div>
                  </div>
                  <div className="flex space-x-2">
                    {job.status === 'completed' && (
                      <button
                        onClick={() => handleImportData(job.id)}
                        className="px-4 py-2 bg-accent text-white rounded-lg hover:bg-accent/90 transition-colors text-sm"
                      >
                        DBに保存
                      </button>
                    )}
                    <button
                      onClick={() => handleDeleteJob(job.id)}
                      className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors text-sm"
                    >
                      削除
                    </button>
                  </div>
                </div>

                {job.warnings.length > 0 && (
                  <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
                    <h4 className="text-sm font-semibold text-yellow-800 mb-2">⚠️ 警告</h4>
                    <ul className="text-xs text-yellow-700 space-y-1">
                      {job.warnings.map((warning, i) => (
                        <li key={i}>• {warning}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {job.errors.length > 0 && (
                  <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded">
                    <h4 className="text-sm font-semibold text-red-800 mb-2">❌ エラー</h4>
                    <ul className="text-xs text-red-700 space-y-1">
                      {job.errors.map((error, i) => (
                        <li key={i}>• {error}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
