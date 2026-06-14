<template>
  <div class="message-pair">
    <!-- User message -->
    <div class="message-row user-row">
      <div class="message-bubble user-bubble">
        <p>{{ message.query }}</p>
      </div>
    </div>

    <!-- Assistant message -->
    <div class="message-row assistant-row">
      <div class="message-bubble assistant-bubble">
        <!-- Intent badge -->
        <div class="intent-badge" :class="message.intent">
          {{ intentLabel }}
        </div>

        <!-- Answer text -->
        <div class="answer-text" v-html="renderMarkdown(message.answer)"></div>

        <!-- Streaming cursor -->
        <span v-if="streaming" class="streaming-cursor">|</span>

        <!-- Document analysis: show doc names -->
        <div v-if="message.intent === 'document_analysis' && message.doc_filenames?.length" class="doc-caption">
          <el-icon><Document /></el-icon>
          文档分析: {{ message.doc_filenames.join(', ') }}
        </div>

        <!-- Sales analysis: show chart -->
        <SalesChart v-if="message.intent === 'sales_analysis' && !streaming" />

        <!-- Trace -->
        <el-collapse v-if="message.trace" class="trace-collapse">
          <el-collapse-item title="调用链路">
            <pre class="trace-content">{{ message.trace }}</pre>
          </el-collapse-item>
        </el-collapse>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Document } from '@element-plus/icons-vue'
import type { ChatMessage } from '@/types'
import SalesChart from './SalesChart.vue'

const props = defineProps<{
  message: ChatMessage
  streaming?: boolean
}>()

const intentLabel = computed(() => {
  switch (props.message.intent) {
    case 'sales_analysis': return '销量分析'
    case 'document_analysis': return '文档分析'
    default: return '知识问答'
  }
})

function renderMarkdown(text: string): string {
  if (!text) return ''
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>')
}
</script>

<style scoped>
.message-pair {
  margin-bottom: 24px;
}

.message-row {
  display: flex;
  margin-bottom: 8px;
}

.user-row {
  justify-content: flex-end;
}

.assistant-row {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 75%;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
  font-size: 14px;
}

.user-bubble {
  background: #409eff;
  color: white;
  border-bottom-right-radius: 4px;
}

.user-bubble p {
  margin: 0;
}

.assistant-bubble {
  background: #f4f4f5;
  color: #303133;
  border-bottom-left-radius: 4px;
}

.intent-badge {
  display: inline-block;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 10px;
  margin-bottom: 8px;
  color: white;
}

.intent-badge.sales_analysis {
  background: #e6a23c;
}

.intent-badge.knowledge_query {
  background: #409eff;
}

.intent-badge.document_analysis {
  background: #67c23a;
}

.answer-text {
  word-break: break-word;
}

.streaming-cursor {
  animation: blink 0.8s infinite;
  color: #409eff;
  font-weight: bold;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.doc-caption {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 4px;
}

.trace-collapse {
  margin-top: 8px;
}

.trace-content {
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
  color: #606266;
  margin: 0;
}
</style>
