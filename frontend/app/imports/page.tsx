'use client'

import { useState, useCallback, useEffect } from 'react'
import { useDropzone } from 'react-dropzone'
import Link from 'next/link'

interface ColumnMapping {
  [standardField: string]: string  // standardField -> sourceColumn
}

interface FieldInfo {
  key: string
  label: string
  required: boolean
  description: string
  aliases: string[]
}

interface MappingTemplate {
  id: number
  template_name: string
  description: string | null
  file_pattern: string | null
  file_type: string | null
  column_mapping: ColumnMapping
  is_default: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

interface IssuerCompany {
  id: number
  name: string
  brand_name: string | null
  tax_id: string | null
  address: string | null
  tel: string | null
  email: string | null
}

interface CustomerCompany {
  id: number
  code: string
  name: string
  is_individual: boolean
  address: string | null
  postal_code: string | null
  phone: string | null
  email: string | null
}

interface UploadedFile {
  file: File
  uploadId?: string
  uploadUrl?: string
  status: 'pending' | 'uploading' | 'uploaded' | 'previewing' | 'processing' | 'completed' | 'failed'
  error?: string
  previewData?: any
  jobId?: number
  columnMapping?: ColumnMapping
  showMapping?: boolean
  selectedIssuerId?: number
  selectedCustomerId?: number
}

export default function ImportsPage() {
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [issuers, setIssuers] = useState<IssuerCompany[]>([])
  const [defaultIssuerId, setDefaultIssuerId] = useState<number | null>(null)
  const [customers, setCustomers] = useState<CustomerCompany[]>([])
  const [requiredFields, setRequiredFields] = useState<FieldInfo[]>([])
  const [optionalFields, setOptionalFields] = useState<FieldInfo[]>([])
  const [templates, setTemplates] = useState<MappingTemplate[]>([])
  const [showSaveTemplate, setShowSaveTemplate] = useState<number | null>(null)

  // 請求者一覧を取得
  useEffect(() => {
    const fetchIssuers = async () => {
      try {
        const response = await fetch('http://localhost:8100/api/v1/settings/issuer/list')
        if (response.ok) {
          const data = await response.json()
          setIssuers(data)
          if (data.length > 0) {
            setDefaultIssuerId(data[0].id)
          }
        }
      } catch (error) {
        console.error('Failed to fetch issuers:', error)
      }
    }
    fetchIssuers()
  }, [])

  // 取引先会社一覧を取得
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

  // マッピングフィールド情報を取得
  useEffect(() => {
    const fetchFields = async () => {
      try {
        const response = await fetch('http://localhost:8100/api/v1/mapping/fields')
        if (response.ok) {
          const data = await response.json()
          setRequiredFields(data.required_fields)
          setOptionalFields(data.optional_fields)
        }
      } catch (error) {
        console.error('Failed to fetch fields:', error)
      }
    }
    fetchFields()
  }, [])

  // マッピングテンプレート一覧を取得
  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        const response = await fetch('http://localhost:8100/api/v1/mapping/templates')
        if (response.ok) {
          const data = await response.json()
          setTemplates(data)
        }
      } catch (error) {
        console.error('Failed to fetch templates:', error)
      }
    }
    fetchTemplates()
  }, [])

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles = acceptedFiles.map(file => ({
      file,
      status: 'pending' as const,
      selectedIssuerId: defaultIssuerId || undefined
    }))
    setFiles(prev => [...prev, ...newFiles])
  }, [defaultIssuerId])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/pdf': ['.pdf'],
      'text/plain': ['.txt']
    }
  })

  const handleUpload = async (index: number) => {
    const fileData = files[index]
    setFiles(prev => prev.map((f, i) => i === index ? { ...f, status: 'uploading' } : f))

    try {
      const formData = new FormData()
      formData.append('file', fileData.file)

      const response = await fetch('http://localhost:8100/api/v1/imports/upload', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`)
      }

      const data = await response.json()
      setFiles(prev => prev.map((f, i) =>
        i === index ? {
          ...f,
          status: 'uploaded',
          uploadId: data.upload_id,
          uploadUrl: data.upload_url
        } : f
      ))
    } catch (error) {
      setFiles(prev => prev.map((f, i) =>
        i === index ? { ...f, status: 'failed', error: String(error) } : f
      ))
    }
  }

  const handlePreview = async (index: number) => {
    const fileData = files[index]
    if (!fileData.uploadId) return

    setFiles(prev => prev.map((f, i) => i === index ? { ...f, status: 'previewing' } : f))

    try {
      const fileType = fileData.file.name.split('.').pop()?.toLowerCase() || 'csv'

      const response = await fetch('http://localhost:8100/api/v1/imports/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          upload_id: fileData.uploadId,
          filename: fileData.file.name,
          file_type: fileType,
          preview_rows: 5
        })
      })

      if (!response.ok) {
        throw new Error(`Preview failed: ${response.statusText}`)
      }

      const previewData = await response.json()

      // 自動マッピング提案を取得
      if (previewData.success && previewData.columns) {
        const mappingResponse = await fetch('http://localhost:8100/api/v1/imports/mapping/suggest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(previewData.columns)
        })

        const mappingData = await mappingResponse.json()

        setFiles(prev => prev.map((f, i) =>
          i === index ? {
            ...f,
            status: 'uploaded',
            previewData,
            columnMapping: mappingData.mapping || {}
          } : f
        ))
      } else {
        setFiles(prev => prev.map((f, i) =>
          i === index ? { ...f, status: 'uploaded', previewData } : f
        ))
      }
    } catch (error) {
      setFiles(prev => prev.map((f, i) =>
        i === index ? { ...f, status: 'failed', error: String(error) } : f
      ))
    }
  }

  const handleCreateJob = async (index: number) => {
    const fileData = files[index]
    if (!fileData.uploadId) return

    setFiles(prev => prev.map((f, i) => i === index ? { ...f, status: 'processing' } : f))

    try {
      const fileType = fileData.file.name.split('.').pop()?.toLowerCase() || 'csv'

      const response = await fetch('http://localhost:8100/api/v1/imports/jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          upload_id: fileData.uploadId,
          filename: fileData.file.name,
          file_type: fileType,
          apply_ai_mapping: true,
          apply_quality_check: true
        })
      })

      if (!response.ok) {
        throw new Error(`Job creation failed: ${response.statusText}`)
      }

      const jobData = await response.json()
      setFiles(prev => prev.map((f, i) =>
        i === index ? { ...f, jobId: jobData.id, status: 'processing' } : f
      ))

      // ジョブステータスをポーリング
      pollJobStatus(index, jobData.id)
    } catch (error) {
      setFiles(prev => prev.map((f, i) =>
        i === index ? { ...f, status: 'failed', error: String(error) } : f
      ))
    }
  }

  const pollJobStatus = async (index: number, jobId: number) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8100/api/v1/imports/jobs/${jobId}`)
        const jobData = await response.json()

        if (jobData.status === 'completed') {
          // ジョブ完了後、自動的にデータをインポート
          clearInterval(interval)
          await handleImportData(index, jobId)
        } else if (jobData.status === 'failed') {
          setFiles(prev => prev.map((f, i) =>
            i === index ? { ...f, status: 'failed', error: jobData.errors?.join(', ') } : f
          ))
          clearInterval(interval)
        }
      } catch (error) {
        clearInterval(interval)
      }
    }, 2000)
  }

  const handleImportData = async (index: number, jobId: number) => {
    const fileData = files[index]

    try {
      const response = await fetch(`http://localhost:8100/api/v1/imports/jobs/${jobId}/import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: jobId,
          column_mapping: fileData.columnMapping || {},
          issuer_id: fileData.selectedIssuerId,
          customer_id: fileData.selectedCustomerId
        })
      })

      if (!response.ok) {
        throw new Error(`Import failed: ${response.statusText}`)
      }

      const importResult = await response.json()

      if (importResult.success) {
        setFiles(prev => prev.map((f, i) =>
          i === index ? { ...f, status: 'completed' } : f
        ))
      } else {
        setFiles(prev => prev.map((f, i) =>
          i === index ? {
            ...f,
            status: 'failed',
            error: importResult.errors?.join(', ') || 'Import failed'
          } : f
        ))
      }
    } catch (error) {
      setFiles(prev => prev.map((f, i) =>
        i === index ? { ...f, status: 'failed', error: String(error) } : f
      ))
    }
  }

  const toggleMapping = (index: number) => {
    setFiles(prev => prev.map((f, i) =>
      i === index ? { ...f, showMapping: !f.showMapping } : f
    ))
  }

  const updateMapping = (index: number, standardField: string, sourceColumn: string) => {
    setFiles(prev => prev.map((f, i) => {
      if (i !== index) return f
      const newMapping = { ...f.columnMapping, [standardField]: sourceColumn }
      return { ...f, columnMapping: newMapping }
    }))
  }

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  // テンプレートをロード
  const loadTemplate = (index: number, templateId: number) => {
    const template = templates.find(t => t.id === templateId)
    if (template) {
      setFiles(prev => prev.map((f, i) =>
        i === index ? { ...f, columnMapping: template.column_mapping } : f
      ))
    }
  }

  // テンプレートを保存
  const saveTemplate = async (index: number, templateName: string) => {
    const fileData = files[index]
    if (!fileData.columnMapping) return

    try {
      const response = await fetch('http://localhost:8100/api/v1/mapping/templates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          template_name: templateName,
          description: `${fileData.file.name}用のマッピング`,
          file_type: fileData.file.name.split('.').pop()?.toLowerCase() || 'csv',
          column_mapping: fileData.columnMapping,
          is_default: false
        })
      })

      if (response.ok) {
        const newTemplate = await response.json()
        setTemplates(prev => [...prev, newTemplate])
        setShowSaveTemplate(null)
        alert('テンプレートを保存しました')
      } else {
        const error = await response.json()
        alert(`保存に失敗しました: ${error.detail}`)
      }
    } catch (error) {
      alert(`保存に失敗しました: ${error}`)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800'
      case 'failed': return 'bg-red-100 text-red-800'
      case 'processing': return 'bg-blue-100 text-blue-800'
      case 'uploaded': return 'bg-accent/10 text-accent'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'pending': return '待機中'
      case 'uploading': return 'アップロード中'
      case 'uploaded': return 'アップロード完了'
      case 'previewing': return 'プレビュー中'
      case 'processing': return '処理中'
      case 'completed': return '完了'
      case 'failed': return '失敗'
      default: return status
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* タブナビゲーション */}
      <div className="bg-white border-b border-line">
        <div className="max-w-7xl mx-auto px-8">
          <div className="flex space-x-8">
            <Link
              href="/imports"
              className="px-4 py-4 text-sm font-medium text-accent border-b-2 border-accent"
            >
              データ取り込み
            </Link>
            <Link
              href="/orders"
              className="px-4 py-4 text-sm font-medium text-muted hover:text-ink hover:border-b-2 hover:border-accent transition-colors"
            >
              注文一覧
            </Link>
          </div>
        </div>
      </div>

      <div className="p-8">
        <div className="max-w-6xl mx-auto">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-ink mb-2">データ取り込み</h1>
            <p className="text-muted">CSV、Excel、PDF、テキストファイルから注文データを取り込みます</p>
          </div>

          {/* Drop Zone */}
          <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all mb-6 ${
            isDragActive
              ? 'border-accent bg-accent/5 scale-[1.02]'
              : 'border-line bg-white hover:border-accent hover:bg-accent/5'
          }`}
        >
          <input {...getInputProps()} />
          <svg
            className="w-16 h-16 mx-auto mb-4 text-accent"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
          <p className="text-lg font-medium text-ink mb-2">
            {isDragActive ? 'ファイルをドロップしてください' : 'ファイルをドラッグ＆ドロップ'}
          </p>
          <p className="text-sm text-muted">または、クリックしてファイルを選択</p>
          <p className="text-xs text-muted mt-2">対応形式: CSV, Excel (.xlsx/.xls), PDF, TXT</p>
          </div>

          {/* File List */}
          {files.length > 0 && (
            <div className="space-y-4">
              {files.map((fileData, index) => (
                <div key={index} className="bg-white rounded-xl border border-line p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <svg className="w-10 h-10 text-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <div>
                      <p className="font-semibold text-ink">{fileData.file.name}</p>
                      <p className="text-xs text-muted">{(fileData.file.size / 1024).toFixed(2)} KB</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(fileData.status)}`}>
                      {getStatusText(fileData.status)}
                    </span>
                    <button onClick={() => removeFile(index)} className="text-red-500 hover:text-red-700 p-1">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </div>

                {/* Issuer Selection */}
                {issuers.length > 0 && (
                  <div className="mb-4 bg-gray-50 rounded-lg p-4">
                    <label className="block text-sm font-medium text-ink mb-2">
                      請求者会社（自社）を選択
                    </label>
                    <select
                      value={fileData.selectedIssuerId || ''}
                      onChange={(e) => {
                        const issuerId = e.target.value ? parseInt(e.target.value) : undefined
                        setFiles(prev => prev.map((f, i) =>
                          i === index ? { ...f, selectedIssuerId: issuerId } : f
                        ))
                      }}
                      className="w-full px-4 py-2 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                    >
                      {issuers.map((issuer) => (
                        <option key={issuer.id} value={issuer.id}>
                          {issuer.name} {issuer.brand_name ? `(${issuer.brand_name})` : ''}
                        </option>
                      ))}
                    </select>
                    <p className="text-xs text-muted mt-1">
                      この取引の請求書を発行する会社を選択してください
                    </p>
                  </div>
                )}

                {/* Customer Selection */}
                <div className="mb-4 bg-blue-50 rounded-lg p-4 border-2 border-blue-200">
                  <label className="block text-sm font-medium text-ink mb-2">
                    取引先会社を選択（オプション）
                  </label>
                  <select
                    value={fileData.selectedCustomerId || ''}
                    onChange={(e) => {
                      const customerId = e.target.value ? parseInt(e.target.value) : undefined
                      setFiles(prev => prev.map((f, i) =>
                        i === index ? { ...f, selectedCustomerId: customerId } : f
                      ))
                    }}
                    className="w-full px-4 py-2 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">（CSVのデータから自動作成）</option>
                    {customers.map((customer) => (
                      <option key={customer.id} value={customer.id}>
                        {customer.name} {customer.is_individual ? '（個人）' : '（法人）'}
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-blue-700 mt-2 font-medium">
                    💡 会社を選択すると、すべてのデータがこの会社に紐付けられます
                  </p>
                  <p className="text-xs text-muted mt-1">
                    月ごとにまとめて請求する場合、ここで会社を選択してください。<br/>
                    選択しない場合は、CSVの顧客名から自動で会社を作成します。
                  </p>
                </div>

                {/* Action Buttons */}
                <div className="flex space-x-3 mb-4">
                  {fileData.status === 'pending' && (
                    <button
                      onClick={() => handleUpload(index)}
                      className="px-4 py-2 bg-accent text-white rounded-lg hover:bg-accent/90 transition-colors"
                    >
                      アップロード
                    </button>
                  )}
                  {fileData.status === 'uploaded' && !fileData.previewData && (
                    <button
                      onClick={() => handlePreview(index)}
                      className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                    >
                      プレビュー
                    </button>
                  )}
                  {fileData.status === 'uploaded' && fileData.previewData && (
                    <>
                      <button
                        onClick={() => toggleMapping(index)}
                        className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors"
                      >
                        {fileData.showMapping ? '列マッピングを閉じる' : '列マッピング設定'}
                      </button>
                      <button
                        onClick={() => handleCreateJob(index)}
                        className="px-4 py-2 bg-accent text-white rounded-lg hover:bg-accent/90 transition-colors"
                      >
                        インポート実行
                      </button>
                    </>
                  )}
                </div>

                {/* Column Mapping */}
                {fileData.showMapping && fileData.previewData && fileData.columnMapping && (
                  <div className="mt-4 border-t border-line pt-4">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-sm font-semibold text-ink">列マッピング設定</h3>
                      <div className="flex space-x-2">
                        {templates.length > 0 && (
                          <select
                            onChange={(e) => {
                              if (e.target.value) {
                                loadTemplate(index, parseInt(e.target.value))
                              }
                            }}
                            className="px-3 py-1 text-xs border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                          >
                            <option value="">テンプレートから読み込み</option>
                            {templates.map((template) => (
                              <option key={template.id} value={template.id}>
                                {template.template_name}
                              </option>
                            ))}
                          </select>
                        )}
                        <button
                          onClick={() => setShowSaveTemplate(showSaveTemplate === index ? null : index)}
                          className="px-3 py-1 text-xs bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors"
                        >
                          {showSaveTemplate === index ? 'キャンセル' : 'テンプレート保存'}
                        </button>
                      </div>
                    </div>

                    {/* テンプレート保存フォーム */}
                    {showSaveTemplate === index && (
                      <div className="mb-4 p-3 bg-purple-50 border border-purple-200 rounded-lg">
                        <input
                          type="text"
                          placeholder="テンプレート名を入力..."
                          className="w-full px-3 py-2 text-sm border border-line rounded-lg mb-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                          onKeyPress={(e) => {
                            if (e.key === 'Enter') {
                              const input = e.target as HTMLInputElement
                              if (input.value.trim()) {
                                saveTemplate(index, input.value.trim())
                              }
                            }
                          }}
                        />
                        <p className="text-xs text-muted">Enter キーを押して保存</p>
                      </div>
                    )}

                    {/* 必須フィールド */}
                    <div className="mb-4">
                      <p className="text-xs font-semibold text-ink mb-2 flex items-center">
                        <span className="inline-block w-2 h-2 bg-red-500 rounded-full mr-2"></span>
                        必須フィールド
                      </p>
                      <div className="space-y-2">
                        {requiredFields.map((field) => (
                          <div key={field.key} className="flex items-start space-x-3">
                            <div className="w-36">
                              <label className="text-xs text-ink font-medium">
                                {field.label}
                                <span className="text-red-500 ml-1">*</span>
                              </label>
                              <p className="text-xs text-muted mt-0.5" title={field.description}>
                                {field.description.substring(0, 20)}...
                              </p>
                            </div>
                            <select
                              value={fileData.columnMapping[field.key] || ''}
                              onChange={(e) => updateMapping(index, field.key, e.target.value)}
                              className="flex-1 px-3 py-2 text-sm border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                            >
                              <option value="">（未設定）</option>
                              {fileData.previewData.columns.map((col: string) => (
                                <option key={col} value={col}>{col}</option>
                              ))}
                            </select>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* オプションフィールド */}
                    <div className="pt-3 border-t border-line">
                      <p className="text-xs font-semibold text-ink mb-2 flex items-center">
                        <span className="inline-block w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                        オプションフィールド
                      </p>
                      <div className="space-y-2 max-h-96 overflow-y-auto">
                        {optionalFields.map((field) => (
                          <div key={field.key} className="flex items-start space-x-3">
                            <div className="w-36">
                              <label className="text-xs text-muted font-medium">
                                {field.label}
                              </label>
                              <p className="text-xs text-muted mt-0.5" title={field.description}>
                                {field.description.substring(0, 20)}...
                              </p>
                            </div>
                            <select
                              value={fileData.columnMapping[field.key] || ''}
                              onChange={(e) => updateMapping(index, field.key, e.target.value)}
                              className="flex-1 px-3 py-2 text-sm border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                            >
                              <option value="">（未設定）</option>
                              {fileData.previewData.columns.map((col: string) => (
                                <option key={col} value={col}>{col}</option>
                              ))}
                            </select>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Preview Data */}
                {fileData.previewData && fileData.previewData.success && (
                  <div className="mt-4 border-t border-line pt-4">
                    <h3 className="text-sm font-semibold text-ink mb-2">
                      プレビュー ({fileData.previewData.row_count}行、{fileData.previewData.columns.length}列)
                      {Object.keys(fileData.columnMapping || {}).length > 0 && (
                        <span className="ml-2 text-xs text-purple-600">- マッピング適用済み</span>
                      )}
                    </h3>
                    <div className="overflow-x-auto border border-line rounded-lg">
                      <table className="min-w-full text-xs">
                        <thead>
                          <tr className="bg-gray-50">
                            {(() => {
                              // マッピングが設定されている場合
                              const hasMappings = fileData.columnMapping && Object.keys(fileData.columnMapping).some(key => fileData.columnMapping![key])

                              if (hasMappings) {
                                // マッピング済みの列のみ表示（全て表示）
                                const mappedColumns = Object.entries(fileData.columnMapping!)
                                  .filter(([_, sourceCol]) => sourceCol)

                                return mappedColumns.map(([fieldKey, sourceCol], i) => {
                                  const field = [...requiredFields, ...optionalFields].find(f => f.key === fieldKey)
                                  return (
                                    <th key={i} className="px-3 py-2 text-left text-ink font-medium border-r border-line whitespace-nowrap sticky top-0 bg-gray-50">
                                      <div className="flex flex-col">
                                        <span className="font-semibold">{field?.label || fieldKey}</span>
                                        <span className="text-xs text-muted font-normal">({sourceCol})</span>
                                      </div>
                                    </th>
                                  )
                                })
                              } else {
                                // マッピング前は元のCSV列名を全て表示
                                return fileData.previewData.columns.map((col: string, i: number) => (
                                  <th key={i} className="px-3 py-2 text-left text-ink font-medium border-r border-line whitespace-nowrap sticky top-0 bg-gray-50">
                                    {col}
                                  </th>
                                ))
                              }
                            })()}
                          </tr>
                        </thead>
                        <tbody>
                          {fileData.previewData.data.map((row: any, rowIndex: number) => {
                            const hasMappings = fileData.columnMapping && Object.keys(fileData.columnMapping).some(key => fileData.columnMapping![key])

                            return (
                              <tr key={rowIndex} className="border-t border-line hover:bg-gray-50">
                                {(() => {
                                  if (hasMappings) {
                                    // マッピング済みの列のみ表示（全て表示）
                                    const mappedColumns = Object.entries(fileData.columnMapping!)
                                      .filter(([_, sourceCol]) => sourceCol)

                                    return mappedColumns.map(([fieldKey, sourceCol], i) => (
                                      <td key={i} className="px-3 py-2 text-muted border-r border-line whitespace-nowrap">
                                        {row[sourceCol as string] || '-'}
                                      </td>
                                    ))
                                  } else {
                                    // マッピング前は全列表示
                                    return fileData.previewData.columns.map((col: string, j: number) => (
                                      <td key={j} className="px-3 py-2 text-muted border-r border-line whitespace-nowrap">
                                        {row[col] || '-'}
                                      </td>
                                    ))
                                  }
                                })()}
                              </tr>
                            )
                          })}
                        </tbody>
                      </table>
                    </div>
                    {fileData.previewData.warnings?.length > 0 && (
                      <div className="mt-2 text-xs text-yellow-600">
                        ⚠️ {fileData.previewData.warnings.join(', ')}
                      </div>
                    )}
                  </div>
                )}

                {/* Error */}
                {fileData.error && (
                  <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                    エラー: {fileData.error}
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
