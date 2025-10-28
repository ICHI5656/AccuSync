'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

export default function Navbar() {
  const pathname = usePathname()

  const isActive = (path: string) => pathname === path

  return (
    <nav className="bg-white border-b border-line">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <Link href="/" className="flex items-center">
              <span className="text-2xl font-bold text-accent">AccuSync</span>
              <span className="ml-2 text-sm text-muted">あきゅシンク</span>
            </Link>
            <div className="hidden sm:ml-8 sm:flex sm:space-x-8">
              <Link
                href="/"
                className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors ${
                  isActive('/')
                    ? 'border-accent text-accent'
                    : 'border-transparent text-muted hover:border-line hover:text-ink'
                }`}
              >
                ホーム
              </Link>
              <Link
                href="/imports"
                className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors ${
                  isActive('/imports')
                    ? 'border-accent text-accent'
                    : 'border-transparent text-muted hover:border-line hover:text-ink'
                }`}
              >
                データ取り込み
              </Link>
              <Link
                href="/jobs"
                className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors ${
                  isActive('/jobs')
                    ? 'border-accent text-accent'
                    : 'border-transparent text-muted hover:border-line hover:text-ink'
                }`}
              >
                ジョブ一覧
              </Link>
              <Link
                href="/customers"
                className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors ${
                  isActive('/customers')
                    ? 'border-accent text-accent'
                    : 'border-transparent text-muted hover:border-line hover:text-ink'
                }`}
              >
                取引先管理
              </Link>
              <Link
                href="/products"
                className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors ${
                  isActive('/products')
                    ? 'border-accent text-accent'
                    : 'border-transparent text-muted hover:border-line hover:text-ink'
                }`}
              >
                商品管理
              </Link>
              <Link
                href="/settings"
                className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors ${
                  isActive('/settings')
                    ? 'border-accent text-accent'
                    : 'border-transparent text-muted hover:border-line hover:text-ink'
                }`}
              >
                設定
              </Link>
            </div>
          </div>
          <div className="flex items-center">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-sm text-muted">システム稼働中</span>
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}
