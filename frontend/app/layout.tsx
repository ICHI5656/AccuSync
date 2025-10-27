import type { Metadata } from 'next'
import './globals.css'
import Navbar from './components/Navbar'

export const metadata: Metadata = {
  title: 'AccuSync - 請求書作成システム',
  description: 'AI駆動の次世代請求書作成システム',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ja">
      <body className="bg-white text-ink antialiased">
        <Navbar />
        {children}
      </body>
    </html>
  )
}
