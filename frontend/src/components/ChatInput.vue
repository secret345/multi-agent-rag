<template>
  <div class="chat-input-container">
    <div class="input-wrapper">
      <el-input
        ref="inputRef"
        v-model="inputText"
        type="textarea"
        :rows="1"
        :autosize="{ minRows: 1, maxRows: 4 }"
        placeholder="请输入你的问题..."
        :disabled="disabled"
        resize="none"
        @keydown="handleKeydown"
      />
      <el-button
        type="primary"
        :icon="Promotion"
        :disabled="!inputText.trim() || disabled"
        circle
        class="send-btn"
        @click="handleSend"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Promotion } from '@element-plus/icons-vue'

defineProps<{
  disabled?: boolean
}>()

const emit = defineEmits<{
  send: [query: string]
}>()

const inputText = ref('')
const inputRef = ref()

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

function handleSend() {
  const query = inputText.value.trim()
  if (!query) return
  emit('send', query)
  inputText.value = ''
}
</script>

<style scoped>
.chat-input-container {
  padding: 16px 20px;
  border-top: 1px solid #e4e7ed;
  background: white;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  max-width: 900px;
  margin: 0 auto;
}

.input-wrapper :deep(.el-textarea__inner) {
  border-radius: 12px;
  padding: 10px 16px;
  resize: none;
}

.send-btn {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
}
</style>
