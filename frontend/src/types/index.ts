export interface ChatMessage {
  query: string
  answer: string
  intent: 'sales_analysis' | 'knowledge_query' | 'document_analysis'
  trace?: string
  doc_filenames?: string[]
}

export interface Document {
  index_id: string
  filename: string
}

export interface SalesData {
  columns: string[]
  rows: Record<string, any>[]
  summary: { product: string; quantity: number }[]
}
