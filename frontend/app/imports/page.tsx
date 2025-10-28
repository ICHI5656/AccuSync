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

interface Product {
  id: number
  sku: string
  name: string
  default_price: string
  tax_rate: number
}

interface PriceModalData {
  fileIndex: number
  rowIndex: number
  extractedKeyword: string
  customerId: number | undefined
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
  hasSavedTemplate?: boolean  // 保存済みテンプレートから読み込んだかどうか
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
  const [products, setProducts] = useState<Product[]>([])
  const [priceModal, setPriceModal] = useState<PriceModalData | null>(null)
  const [selectedProduct, setSelectedProduct] = useState<number | null>(null)
  const [priceInput, setPriceInput] = useState('')

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

  // 商品一覧を取得
  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const response = await fetch('http://localhost:8100/api/v1/products/?limit=1000')
        if (response.ok) {
          const data = await response.json()
          setProducts(data)
        }
      } catch (error) {
        console.error('Failed to fetch products:', error)
      }
    }
    fetchProducts()
  }, [])

  // 顧客のマッピングテンプレートを取得
  const fetchCustomerMappingTemplate = async (customerId: number): Promise<ColumnMapping | null> => {
    try {
      const response = await fetch(`http://localhost:8100/api/v1/mapping/templates?customer_id=${customerId}&is_active=true`)
      if (response.ok) {
        const templates = await response.json()
        // デフォルトテンプレートまたは最新のテンプレートを使用
        const template = templates.find((t: MappingTemplate) => t.is_default) || templates[0]
        return template ? template.column_mapping : null
      }
    } catch (error) {
      console.error('Failed to fetch customer mapping template:', error)
    }
    return null
  }

  // プレビューデータから識別情報を抽出
  const extractCustomerIdentifiers = (previewData: any, columnMapping: ColumnMapping) => {
    if (!previewData || !previewData.data || previewData.data.length === 0) {
      return null
    }

    // 最初の行から識別情報を取得
    const firstRow = previewData.data[0]
    const identifiers: any = {}

    // 列マッピングから対応する列を探す
    const customerNameCol = Object.entries(columnMapping).find(([key]) => key === 'customer_name')?.[1]
    const addressCol = Object.entries(columnMapping).find(([key]) => key === 'address')?.[1]
    const phoneCol = Object.entries(columnMapping).find(([key]) => key === 'phone')?.[1]
    const emailCol = Object.entries(columnMapping).find(([key]) => key === 'email')?.[1]
    const postalCodeCol = Object.entries(columnMapping).find(([key]) => key === 'postal_code')?.[1]

    if (customerNameCol && firstRow[customerNameCol]) {
      identifiers.store_name = firstRow[customerNameCol]
    }
    if (addressCol && firstRow[addressCol]) {
      identifiers.address = firstRow[addressCol]
    }
    if (phoneCol && firstRow[phoneCol]) {
      identifiers.phone = firstRow[phoneCol]
    }
    if (emailCol && firstRow[emailCol]) {
      identifiers.email = firstRow[emailCol]
    }
    if (postalCodeCol && firstRow[postalCodeCol]) {
      identifiers.postal_code = firstRow[postalCodeCol]
    }

    return Object.keys(identifiers).length > 0 ? identifiers : null
  }

  // 顧客を自動判別
  const detectCustomer = async (identifiers: any) => {
    try {
      const response = await fetch('http://localhost:8100/api/v1/customers/detect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ identifiers })
      })

      if (response.ok) {
        const data = await response.json()
        return data.customer_id ? data : null
      }
    } catch (error) {
      console.error('Failed to detect customer:', error)
    }
    return null
  }

  // 顧客の識別情報を保存
  const saveCustomerIdentifiers = async (customerId: number, identifiers: any) => {
    try {
      const response = await fetch(`http://localhost:8100/api/v1/customers/${customerId}/identifiers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(identifiers)
      })

      if (response.ok) {
        console.log('Customer identifiers saved successfully')
        return true
      }
    } catch (error) {
      console.error('Failed to save customer identifiers:', error)
    }
    return false
  }

  // 既存の価格ルールを取得
  const fetchExistingPrice = async (customerId: number, productTypeKeyword: string): Promise<string | null> => {
    try {
      const response = await fetch(`http://localhost:8100/api/v1/products/pricing?customer_id=${customerId}&product_type_keyword=${encodeURIComponent(productTypeKeyword)}`)
      if (response.ok) {
        const rules = await response.json()
        if (rules && rules.length > 0) {
          // 最新のルールを返す
          return rules[0].price
        }
      }
    } catch (error) {
      console.error('Failed to fetch existing price:', error)
    }
    return null
  }

  // 価格モーダルが開かれた時に既存価格を読み込む
  useEffect(() => {
    if (priceModal && priceModal.customerId && priceModal.extractedKeyword) {
      fetchExistingPrice(priceModal.customerId, priceModal.extractedKeyword).then(price => {
        if (price) {
          setPriceInput(price)
        }
      })
    }
  }, [priceModal])

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

      // マッピング処理
      let columnMapping: ColumnMapping = {}
      let hasSavedTemplate = false

      if (previewData.success && previewData.columns) {
        // 1. 手動選択された顧客がいる場合、その顧客のマッピングテンプレートを取得
        if (fileData.selectedCustomerId) {
          const customerMapping = await fetchCustomerMappingTemplate(fileData.selectedCustomerId)
          if (customerMapping && Object.keys(customerMapping).length > 0) {
            columnMapping = customerMapping
            hasSavedTemplate = true
          } else {
            // テンプレートがない場合は自動マッピング
            const mappingResponse = await fetch('http://localhost:8100/api/v1/imports/mapping/suggest', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(previewData.columns)
            })
            const mappingData = await mappingResponse.json()
            columnMapping = mappingData.mapping || {}
          }
        } else {
          // 2. 顧客未選択の場合、まず自動マッピング提案を取得
          const mappingResponse = await fetch('http://localhost:8100/api/v1/imports/mapping/suggest', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(previewData.columns)
          })
          const mappingData = await mappingResponse.json()
          columnMapping = mappingData.mapping || {}
        }

        // 3. 自動判別：顧客が未選択の場合のみ実行
        let detectedCustomerId = fileData.selectedCustomerId
        if (!fileData.selectedCustomerId && Object.keys(columnMapping).length > 0) {
          try {
            const identifiers = extractCustomerIdentifiers(previewData, columnMapping)
            if (identifiers) {
              const detected = await detectCustomer(identifiers)
              if (detected && detected.customer_id) {
                detectedCustomerId = detected.customer_id
                console.log(`✅ 顧客を自動判別しました: ${detected.customer_name} (${detected.matched_by}でマッチ)`)

                // 4. 自動判別された顧客のマッピングテンプレートを取得
                try {
                  const customerMapping = await fetchCustomerMappingTemplate(detectedCustomerId)
                  if (customerMapping && Object.keys(customerMapping).length > 0) {
                    columnMapping = customerMapping
                    hasSavedTemplate = true
                    console.log(`✅ 保存済みマッピングテンプレートを適用しました`)
                  }
                } catch (mappingError) {
                  console.warn('マッピングテンプレートの取得に失敗しましたが、処理を続行します:', mappingError)
                }
              }
            }
          } catch (detectionError) {
            console.warn('顧客の自動判別に失敗しましたが、処理を続行します:', detectionError)
          }
        }

        setFiles(prev => prev.map((f, i) =>
          i === index ? {
            ...f,
            status: 'uploaded',
            previewData,
            columnMapping,
            hasSavedTemplate,
            selectedCustomerId: detectedCustomerId
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

      // エラーがある場合のみ失敗として扱う
      if (importResult.errors && importResult.errors.length > 0) {
        setFiles(prev => prev.map((f, i) =>
          i === index ? {
            ...f,
            status: 'failed',
            error: importResult.errors.join(', ')
          } : f
        ))
      } else if (importResult.imported_rows > 0) {
        // 正常にインポートされた行がある場合は成功
        setFiles(prev => prev.map((f, i) =>
          i === index ? {
            ...f,
            status: 'completed',
            error: importResult.warnings?.length > 0
              ? `✅ ${importResult.imported_rows}件インポート完了 (${importResult.skipped_rows}件スキップ)`
              : undefined
          } : f
        ))
      } else if (importResult.skipped_rows > 0) {
        // 全てスキップされた場合は警告として表示
        const skipReasons = importResult.warnings?.slice(2, 5).join('\n') || ''
        setFiles(prev => prev.map((f, i) =>
          i === index ? {
            ...f,
            status: 'completed',
            error: `⚠️ ${importResult.skipped_rows}件スキップされました\n\n理由:\n${skipReasons}\n\n💡 商品を事前に商品マスタに登録してください`
          } : f
        ))
      } else {
        // インポートもスキップもない場合（データなし）
        setFiles(prev => prev.map((f, i) =>
          i === index ? {
            ...f,
            status: 'failed',
            error: 'インポート可能なデータがありません'
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
          customer_id: fileData.selectedCustomerId || null,
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

  // 価格ルールを保存
  const savePricingRule = async () => {
    if (!priceModal || !priceInput) {
      alert('価格を入力してください')
      return
    }

    if (!priceModal.customerId) {
      alert('取引先が選択されていません')
      return
    }

    if (!priceModal.extractedKeyword) {
      alert('商品タイプが取得できませんでした')
      return
    }

    try {
      const response = await fetch('http://localhost:8100/api/v1/products/pricing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          customer_id: priceModal.customerId,
          product_type_keyword: priceModal.extractedKeyword,
          price: parseFloat(priceInput),
          priority: 0
        })
      })

      if (response.ok) {
        alert(`価格ルールを保存しました\n商品タイプ: ${priceModal.extractedKeyword}\n価格: ¥${priceInput}`)

        // プレビューデータの単価を更新
        const fileIndex = priceModal.fileIndex
        const newPrice = priceInput
        const keyword = priceModal.extractedKeyword

        setFiles(prev => prev.map((f, i) => {
          if (i !== fileIndex || !f.previewData || !f.columnMapping) return f

          // 単価列を特定
          const unitPriceCol = Object.entries(f.columnMapping).find(([key]) => key === 'unit_price')?.[1]

          if (!unitPriceCol) return f

          // extracted_memoが一致する行の単価を更新
          const updatedData = f.previewData.data.map((row: any) => {
            if (row['extracted_memo'] === keyword) {
              return { ...row, [unitPriceCol]: newPrice }
            }
            return row
          })

          return {
            ...f,
            previewData: {
              ...f.previewData,
              data: updatedData
            }
          }
        }))

        setPriceModal(null)
        setSelectedProduct(null)
        setPriceInput('')
      } else {
        const error = await response.json()
        alert(`保存に失敗しました: ${error.detail || '不明なエラー'}`)
      }
    } catch (error) {
      console.error('Failed to save pricing rule:', error)
      alert('保存に失敗しました')
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

                      // 状態更新を先に実行
                      setFiles(prev => prev.map((f, i) =>
                        i === index ? { ...f, selectedCustomerId: customerId } : f
                      ))

                      // 顧客が選択された場合、識別情報を保存（バックグラウンドで実行）
                      if (customerId && fileData.previewData && fileData.columnMapping) {
                        const identifiers = extractCustomerIdentifiers(fileData.previewData, fileData.columnMapping)
                        if (identifiers) {
                          saveCustomerIdentifiers(customerId, identifiers).catch((error) => {
                            console.error('識別情報の保存に失敗しました:', error)
                          })
                        }
                      }
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
                      プレビュー ({fileData.previewData.row_count}行)
                      {fileData.hasSavedTemplate && (
                        <span className="ml-2 text-xs text-green-600 font-medium">✓ 保存済みテンプレート適用</span>
                      )}
                      {!fileData.hasSavedTemplate && Object.keys(fileData.columnMapping || {}).length > 0 && (
                        <span className="ml-2 text-xs text-purple-600">- マッピング提案済み</span>
                      )}
                    </h3>
                    {fileData.columnMapping && Object.keys(fileData.columnMapping).length > 0 ? (
                      <div className="mb-3 p-2 bg-blue-50 border border-blue-200 rounded text-xs text-blue-700">
                        📊 必要なデータのみ表示中: <span className="font-semibold">商品タイプ・会社名・数量・単価・注文日</span>
                        {fileData.hasSavedTemplate && (
                          <span className="ml-2">（💾 保存済みテンプレート適用）</span>
                        )}
                      </div>
                    ) : (
                      <div className="mb-3 p-2 bg-gray-50 border border-gray-200 rounded text-xs text-gray-700">
                        📋 CSV元データの全列を表示中 - 列マッピング設定後、必要なデータのみに絞り込まれます
                      </div>
                    )}
                    <div className="overflow-x-auto border border-line rounded-lg">
                      <table className="min-w-full text-xs">
                        <thead>
                          <tr className="bg-gray-50">
                            {(() => {
                              const columns = []

                              // マッピング後は必須フィールドのみ表示
                              if (fileData.columnMapping && Object.keys(fileData.columnMapping).length > 0) {
                                // 表示する列の優先順位
                                const priorityFields = ['customer_name', 'quantity', 'unit_price', 'order_date']

                                // extracted_memoを先頭に追加
                                if (fileData.previewData.columns.includes('extracted_memo')) {
                                  columns.push(
                                    <th key="extracted_memo" className="px-3 py-2 text-left font-medium border-r border-line whitespace-nowrap sticky top-0 bg-purple-100 text-purple-800 cursor-help">
                                      📝 商品タイプ<br/>
                                      <span className="text-xs font-normal">（価格設定）</span>
                                    </th>
                                  )
                                }

                                // 優先フィールドのみを表示
                                priorityFields.forEach((fieldKey) => {
                                  const sourceCol = fileData.columnMapping[fieldKey]
                                  if (sourceCol) {
                                    const field = [...requiredFields, ...optionalFields].find(f => f.key === fieldKey)
                                    columns.push(
                                      <th key={fieldKey} className="px-3 py-2 text-left text-ink font-medium border-r border-line whitespace-nowrap sticky top-0 bg-gray-50">
                                        <div className="flex flex-col">
                                          <span className="font-semibold">{field?.label || fieldKey}</span>
                                          <span className="text-xs text-muted font-normal">({sourceCol})</span>
                                        </div>
                                      </th>
                                    )
                                  }
                                })

                                return columns
                              } else {
                                // マッピング前：元のCSV列名を全て表示
                                const extractedMemoIndex = fileData.previewData.columns.indexOf('extracted_memo')
                                const otherColumns = fileData.previewData.columns.filter((c: string) => c !== 'extracted_memo')

                                if (extractedMemoIndex !== -1) {
                                  columns.push(
                                    <th key="extracted_memo" className="px-3 py-2 text-left font-medium border-r border-line whitespace-nowrap sticky top-0 bg-purple-100 text-purple-800 cursor-help">
                                      📝 商品タイプ<br/>
                                      <span className="text-xs font-normal">（価格設定）</span>
                                    </th>
                                  )
                                }

                                // その他の列を追加
                                otherColumns.forEach((col: string, i: number) => {
                                  columns.push(
                                    <th key={i} className="px-3 py-2 text-left font-medium border-r border-line whitespace-nowrap sticky top-0 bg-gray-50 text-ink">
                                      {col}
                                    </th>
                                  )
                                })

                                return columns
                              }
                            })()}
                          </tr>
                        </thead>
                        <tbody>
                          {fileData.previewData.data.map((row: any, rowIndex: number) => {
                            return (
                              <tr key={rowIndex} className="border-t border-line hover:bg-gray-50">
                                {(() => {
                                  const cells = []

                                  // マッピング後は必須フィールドのみ表示
                                  if (fileData.columnMapping && Object.keys(fileData.columnMapping).length > 0) {
                                    const priorityFields = ['customer_name', 'quantity', 'unit_price', 'order_date']

                                    // extracted_memoを先頭に追加
                                    if (fileData.previewData.columns.includes('extracted_memo')) {
                                      cells.push(
                                        <td
                                          key="extracted_memo"
                                          className="px-3 py-2 border-r border-line whitespace-nowrap bg-purple-50 text-purple-700 font-medium cursor-pointer hover:bg-purple-100"
                                          onClick={() => setPriceModal({
                                            fileIndex: index,
                                            rowIndex,
                                            extractedKeyword: row['extracted_memo'] || '',
                                            customerId: fileData.selectedCustomerId
                                          })}
                                          title="クリックして価格を設定"
                                        >
                                          {row['extracted_memo'] || '-'}
                                        </td>
                                      )
                                    }

                                    // 優先フィールドのみを表示
                                    priorityFields.forEach((fieldKey) => {
                                      const sourceCol = fileData.columnMapping[fieldKey]
                                      if (sourceCol) {
                                        // 単価の場合は価格フォーマット
                                        let displayValue = row[sourceCol as string] || '-'
                                        if (fieldKey === 'unit_price' && displayValue !== '-') {
                                          displayValue = `¥${parseFloat(displayValue).toLocaleString()}`
                                        }

                                        cells.push(
                                          <td key={fieldKey} className="px-3 py-2 text-muted border-r border-line whitespace-nowrap">
                                            {displayValue}
                                          </td>
                                        )
                                      }
                                    })

                                    return cells
                                  } else {
                                    // マッピング前：全列表示
                                    const extractedMemoIndex = fileData.previewData.columns.indexOf('extracted_memo')
                                    const otherColumns = fileData.previewData.columns.filter((c: string) => c !== 'extracted_memo')

                                    if (extractedMemoIndex !== -1) {
                                      cells.push(
                                        <td
                                          key="extracted_memo"
                                          className="px-3 py-2 border-r border-line whitespace-nowrap bg-purple-50 text-purple-700 font-medium cursor-pointer hover:bg-purple-100"
                                          onClick={() => setPriceModal({
                                            fileIndex: index,
                                            rowIndex,
                                            extractedKeyword: row['extracted_memo'] || '',
                                            customerId: fileData.selectedCustomerId
                                          })}
                                          title="クリックして価格を設定"
                                        >
                                          {row['extracted_memo'] || '-'}
                                        </td>
                                      )
                                    }

                                    // その他の列を追加
                                    otherColumns.forEach((col: string, j: number) => {
                                      cells.push(
                                        <td key={j} className="px-3 py-2 text-muted border-r border-line whitespace-nowrap">
                                          {row[col] || '-'}
                                        </td>
                                      )
                                    })

                                    return cells
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

                {/* Error or Warning */}
                {fileData.error && (
                  <div className={`mt-4 p-3 border rounded text-sm ${
                    fileData.error.startsWith('⚠️')
                      ? 'bg-yellow-50 border-yellow-200 text-yellow-800'
                      : fileData.error.startsWith('✅')
                      ? 'bg-green-50 border-green-200 text-green-800'
                      : 'bg-red-50 border-red-200 text-red-700'
                  }`}>
                    {fileData.error.split('\n').map((line, i) => (
                      <div key={i}>{line}</div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* 価格設定モーダル */}
        {priceModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl p-6 max-w-md w-full mx-4 shadow-2xl">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-bold text-ink">価格設定</h3>
                <button
                  onClick={() => {
                    setPriceModal(null)
                    setSelectedProduct(null)
                    setPriceInput('')
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="mb-4 p-4 bg-purple-50 border-2 border-purple-300 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">商品タイプ</p>
                <p className="text-xl font-bold text-purple-700">{priceModal.extractedKeyword}</p>
                <p className="text-xs text-gray-500 mt-2">
                  このタイプの全ての商品（デザイン違いを含む）に同じ価格が適用されます
                </p>
              </div>

              {!priceModal.customerId && (
                <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <p className="text-sm text-yellow-700">⚠️ 取引先を選択してから価格を設定してください</p>
                </div>
              )}

              <div className="mb-4">
                <label className="block text-sm font-medium text-ink mb-2">
                  価格（円）
                </label>
                <input
                  type="number"
                  value={priceInput}
                  onChange={(e) => setPriceInput(e.target.value)}
                  placeholder="価格を入力..."
                  className="w-full px-3 py-2 border border-line rounded-lg focus:outline-none focus:ring-2 focus:ring-accent"
                  disabled={!priceModal.customerId}
                />
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
                <p className="text-xs text-blue-700">
                  💡 この取引先に対して、「{priceModal.extractedKeyword}」タイプ全般の価格を設定します。<br/>
                  次回のインポート時、この取引先の同じタイプの商品に対して自動的にこの価格が適用されます。<br/>
                  <span className="font-semibold mt-1 block">
                    例: 「ハードケース」で¥1,200を設定すると、デザイン違いの全てのハードケースに¥1,200が適用されます
                  </span>
                </p>
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={() => {
                    setPriceModal(null)
                    setSelectedProduct(null)
                    setPriceInput('')
                  }}
                  className="flex-1 px-4 py-2 border border-line rounded-lg hover:bg-gray-50 transition-colors"
                >
                  キャンセル
                </button>
                <button
                  onClick={savePricingRule}
                  disabled={!priceModal.customerId || !priceInput}
                  className="flex-1 px-4 py-2 bg-accent text-white rounded-lg hover:bg-accent/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  保存
                </button>
              </div>
            </div>
          </div>
        )}
        </div>
      </div>
    </div>
  )
}
