<template>
  <div class="chat-layout">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <h3>企业数据分析助手</h3>
      </div>

      <div class="sidebar-content">
        <!-- API Key -->
        <div class="sidebar-section">
          <h4>API 设置</h4>
          <el-input
            v-model="apiKey"
            type="password"
            placeholder="DashScope API Key"
            show-password
            @change="saveApiKey"
          />
          <p class="hint">留空则使用系统默认</p>
        </div>

        <el-divider />

        <!-- Document Upload -->
        <div class="sidebar-section">
          <h4>文档上传</h4>
          <el-upload
            :auto-upload="false"
            :on-change="handleFileChange"
            accept=".txt,.pdf,.docx"
            :show-file-list="false"
          >
            <el-button type="primary" :loading="uploading">选择文档</el-button>
          </el-upload>

          <div v-if="documents.length" class="doc-list">
            <div v-for="doc in documents" :key="doc.index_id" class="doc-item">
              <span class="doc-name">{{ doc.filename }}</span>
              <el-button type="danger" link @click="deleteDocument(doc.index_id)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
          </div>
        </div>

        <el-divider />

        <!-- Actions -->
        <div class="sidebar-section">
          <el-button style="width: 100%" @click="handleClearHistory">清空对话记录</el-button>
        </div>
      </div>

      <div class="sidebar-footer">
        <div class="user-info">
          <el-icon><User /></el-icon>
          <span>{{ authStore.phone }}</span>
        </div>
        <el-button type="danger" link @click="handleLogout">退出登录</el-button>
      </div>
    </aside>

    <!-- Chat Area -->
    <main class="chat-main">
      <div class="messages-container" ref="messagesRef">
        <div v-if="!chatStore.messages.length && !chatStore.loading" class="empty-state">
          <el-icon :size="48" color="#c0c4cc"><ChatDotRound /></el-icon>
          <p>请输入你的问题开始对话</p>
        </div>

        <ChatMessage
          v-for="(msg, index) in chatStore.messages"
          :key="index"
          :message="msg"
        />

        <!-- Streaming message -->
        <ChatMessage
          v-if="chatStore.loading"
          :message="{
            query: currentQuery,
            answer: chatStore.streamingContent,
            intent: (chatStore.streamingIntent as any) || 'knowledge_query',
            trace: chatStore.streamingTrace,
          }"
          :streaming="true"
        />
      </div>

      <ChatInput :disabled="chatStore.loading" @send="handleSend" />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, User, ChatDotRound } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import client from '@/api/client'
import type { Document } from '@/types'
import ChatMessage from '@/components/ChatMessage.vue'
import ChatInput from '@/components/ChatInput.vue'

const router = useRouter()
const authStore = useAuthStore()
const chatStore = useChatStore()

const messagesRef = ref<HTMLElement>()
const apiKey = ref('')
const documents = ref<Document[]>([])
const uploading = ref(false)
const currentQuery = ref('')

onMounted(async () => {
  await chatStore.loadHistory()
  await loadSettings()
  await loadDocuments()
  scrollToBottom()
})

watch(() => chatStore.messages.length, () => nextTick(scrollToBottom))
watch(() => chatStore.streamingContent, () => nextTick(scrollToBottom))

function scrollToBottom() {
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

async function loadSettings() {
  try {
    const { data } = await client.get('/settings')
    apiKey.value = data.api_key || ''
  } catch {}
}

async function saveApiKey() {
  try {
    await client.put('/settings', { api_key: apiKey.value })
    ElMessage.success('API Key 已保存')
  } catch {
    ElMessage.error('保存失败')
  }
}

async function loadDocuments() {
  try {
    const { data } = await client.get('/documents')
    documents.value = data.documents || []
  } catch {
    documents.value = []
  }
}

async function handleFileChange(file: any) {
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file.raw)
    const { data } = await client.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    documents.value.push(data)
    ElMessage.success(`'${data.filename}' 索引完成`)
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
  }
}

async function deleteDocument(indexId: string) {
  try {
    await ElMessageBox.confirm('确定删除该文档？', '确认')
    await client.delete(`/documents/${indexId}`)
    documents.value = documents.value.filter((d) => d.index_id !== indexId)
    ElMessage.success('已删除')
  } catch {}
}

function handleSend(query: string) {
  currentQuery.value = query
  const docIndexIds = documents.value.map((d) => d.index_id)

  chatStore.sendMessage(
    query,
    docIndexIds,
    () => {},
    () => {},
    async (fullAnswer) => {
      chatStore.messages.push({
        query,
        answer: fullAnswer,
        intent: (chatStore.streamingIntent as any) || 'knowledge_query',
        trace: chatStore.streamingTrace || undefined,
      })
      await chatStore.saveHistory()
      scrollToBottom()
    },
    (err) => {
      ElMessage.error(err)
    },
  )
}

async function handleClearHistory() {
  try {
    await ElMessageBox.confirm('确定清空所有对话记录？', '确认')
    await chatStore.clearHistory()
    ElMessage.success('已清空')
  } catch {}
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.chat-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  width: 300px;
  background: #f5f7fa;
  border-right: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-header {
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
}

.sidebar-header h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.sidebar-section h4 {
  margin: 0 0 8px;
  font-size: 14px;
  color: #606266;
}

.hint {
  font-size: 12px;
  color: #909399;
  margin: 4px 0 0;
}

.doc-list {
  margin-top: 8px;
}

.doc-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 0;
}

.doc-name {
  font-size: 13px;
  color: #606266;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  margin-right: 8px;
}

.sidebar-footer {
  padding: 12px 16px;
  border-top: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #606266;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.empty-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #909399;
}

.empty-state p {
  margin-top: 12px;
  font-size: 14px;
}
</style>
