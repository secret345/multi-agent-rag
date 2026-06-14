import { defineStore } from 'pinia'
import { ref } from 'vue'
import client from '@/api/client'
import type { ChatMessage, SalesData } from '@/types'

export const useChatStore = defineStore('chat', () => {
  const messages = ref<ChatMessage[]>([])
  const loading = ref(false)
  const streamingContent = ref('')
  const streamingIntent = ref('')
  const streamingTrace = ref('')

  async function loadHistory() {
    try {
      const { data } = await client.get('/chat/history')
      messages.value = data.messages || []
    } catch {
      messages.value = []
    }
  }

  async function saveHistory() {
    try {
      await client.put('/chat/history', { messages: messages.value })
    } catch {}
  }

  async function clearHistory() {
    messages.value = []
    try {
      await client.delete('/chat/history')
    } catch {}
  }

  async function getSalesData(): Promise<SalesData | null> {
    try {
      const { data } = await client.get('/chat/sales-data')
      return data
    } catch {
      return null
    }
  }

  function sendMessage(
    query: string,
    docIndexIds: string[],
    onChunk: (content: string) => void,
    onMeta: (intent: string, trace: string) => void,
    onDone: (fullAnswer: string) => void,
    onError: (err: string) => void,
  ) {
    loading.value = true
    streamingContent.value = ''
    streamingIntent.value = ''
    streamingTrace.value = ''

    const token = localStorage.getItem('token') || ''
    const chatHistory: { role: string; content: string }[] = []
    for (const msg of messages.value) {
      chatHistory.push({ role: 'user', content: msg.query })
      chatHistory.push({ role: 'assistant', content: msg.answer })
    }

    fetch('/api/chat/ask', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ query, chat_history: chatHistory, doc_index_ids: docIndexIds }),
    })
      .then(async (response) => {
        if (!response.ok) {
          const err = await response.json().catch(() => ({ detail: '请求失败' }))
          throw new Error(err.detail || '请求失败')
        }

        const reader = response.body!.getReader()
        const decoder = new TextDecoder()
        let buffer = ''
        let fullAnswer = ''

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue
            try {
              const event = JSON.parse(line.slice(6))
              if (event.type === 'meta') {
                streamingIntent.value = event.intent
                streamingTrace.value = event.trace || ''
                onMeta(event.intent, event.trace || '')
              } else if (event.type === 'chunk') {
                fullAnswer += event.content
                streamingContent.value = fullAnswer
                onChunk(event.content)
              } else if (event.type === 'done') {
                loading.value = false
                onDone(fullAnswer)
              }
            } catch {}
          }
        }
      })
      .catch((err) => {
        loading.value = false
        onError(err.message || '请求失败')
      })
  }

  return {
    messages,
    loading,
    streamingContent,
    streamingIntent,
    streamingTrace,
    loadHistory,
    saveHistory,
    clearHistory,
    getSalesData,
    sendMessage,
  }
})
