<template>
  <div class="auth-container">
    <el-card class="auth-card">
      <template #header>
        <div class="card-header">
          <h2>企业数据分析助手</h2>
          <p class="subtitle">Multi-Agent RAG 数据分析平台</p>
        </div>
      </template>

      <div v-if="mode === 'login'">
        <el-alert v-if="errMsg" :title="errMsg" type="error" show-icon :closable="true" style="margin-bottom: 16px" @close="errMsg = ''" />

        <el-form label-position="top">
          <el-form-item label="手机号">
            <el-input v-model="phone" placeholder="请输入手机号" maxlength="11" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="password" type="password" placeholder="请输入密码" show-password @keyup.enter="doLogin" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="loading" style="width: 100%" @click="doLogin">登录</el-button>
          </el-form-item>
        </el-form>
        <div class="auth-links">
          <a href="#" @click.prevent="mode = 'register'; errMsg = ''">注册新账号</a>
          <span style="margin: 0 8px; color: #c0c4cc">|</span>
          <router-link to="/reset">忘记密码？</router-link>
        </div>
      </div>

      <div v-else>
        <el-alert v-if="errMsg" :title="errMsg" type="error" show-icon :closable="true" style="margin-bottom: 16px" @close="errMsg = ''" />

        <el-form label-position="top">
          <el-form-item label="手机号">
            <el-input v-model="phone" placeholder="请输入手机号" maxlength="11" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="password" type="password" placeholder="至少6位" show-password />
          </el-form-item>
          <el-form-item label="确认密码">
            <el-input v-model="confirmPassword" type="password" placeholder="再次输入密码" show-password @keyup.enter="doRegister" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="loading" style="width: 100%" @click="doRegister">注册</el-button>
          </el-form-item>
        </el-form>
        <div class="auth-links">
          <a href="#" @click.prevent="mode = 'login'; errMsg = ''">已有账号？去登录</a>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import client from '@/api/client'

const router = useRouter()
const authStore = useAuthStore()

const mode = ref<'login' | 'register'>('login')
const phone = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const errMsg = ref('')

async function doLogin() {
  errMsg.value = ''
  if (!phone.value || !password.value) {
    errMsg.value = '请输入手机号和密码'
    return
  }
  loading.value = true
  try {
    const { data } = await client.post('/auth/login', { phone: phone.value, password: password.value })
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('phone', phone.value)
    authStore.token = data.access_token
    authStore.phone = phone.value
    ElMessage.success('登录成功')
    router.push('/chat')
  } catch (err: any) {
    errMsg.value = err.response?.data?.detail || '登录失败，请检查手机号和密码'
  } finally {
    loading.value = false
  }
}

async function doRegister() {
  errMsg.value = ''
  if (!phone.value || !password.value) {
    errMsg.value = '请输入手机号和密码'
    return
  }
  if (password.value.length < 6) {
    errMsg.value = '密码至少6位'
    return
  }
  if (password.value !== confirmPassword.value) {
    errMsg.value = '两次密码不一致'
    return
  }
  loading.value = true
  try {
    await client.post('/auth/register', { phone: phone.value, password: password.value })
    ElMessage.success('注册成功，请登录')
    mode.value = 'login'
    password.value = ''
    confirmPassword.value = ''
  } catch (err: any) {
    errMsg.value = err.response?.data?.detail || '注册失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-container {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.auth-card {
  width: 420px;
}
.card-header {
  text-align: center;
}
.card-header h2 {
  margin: 0;
  color: #303133;
}
.subtitle {
  color: #909399;
  font-size: 13px;
  margin-top: 4px;
}
.auth-links {
  text-align: center;
  margin-top: 8px;
}
.auth-links a {
  color: #409eff;
  text-decoration: none;
  font-size: 14px;
  cursor: pointer;
}
</style>
