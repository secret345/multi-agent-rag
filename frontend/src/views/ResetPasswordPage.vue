<template>
  <div class="auth-container">
    <el-card class="auth-card">
      <template #header>
        <h2 style="text-align: center; margin: 0">重置密码</h2>
      </template>

      <el-steps :active="step" finish-status="success" align-center style="margin-bottom: 24px">
        <el-step title="验证手机号" />
        <el-step title="输入验证码" />
        <el-step title="设置新密码" />
      </el-steps>

      <!-- Step 1: Phone -->
      <div v-if="step === 0">
        <el-form ref="phoneFormRef" :model="phoneForm" :rules="phoneRules" label-position="top">
          <el-form-item label="注册手机号" prop="phone">
            <el-input v-model="phoneForm.phone" placeholder="请输入手机号" maxlength="11" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="sendLoading" style="width: 100%" @click="handleSendCode">发送验证码</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- Step 2: Code -->
      <div v-if="step === 1">
        <p style="color: #909399; margin-bottom: 16px">验证码已发送至 {{ phoneForm.phone }}（模拟模式，查看控制台）</p>
        <el-form ref="codeFormRef" :model="codeForm" :rules="codeRules" label-position="top">
          <el-form-item label="6位验证码" prop="code">
            <el-input v-model="codeForm.code" placeholder="请输入验证码" maxlength="6" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="verifyLoading" style="width: 100%" @click="handleVerifyCode">验证</el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- Step 3: New password -->
      <div v-if="step === 2">
        <el-form ref="pwdFormRef" :model="pwdForm" :rules="pwdRules" label-position="top">
          <el-form-item label="新密码" prop="password">
            <el-input v-model="pwdForm.password" type="password" placeholder="至少6位" show-password />
          </el-form-item>
          <el-form-item label="确认新密码" prop="confirmPassword">
            <el-input v-model="pwdForm.confirmPassword" type="password" placeholder="再次输入密码" show-password />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="resetLoading" style="width: 100%" @click="handleResetPassword">重置密码</el-button>
          </el-form-item>
        </el-form>
      </div>

      <div style="text-align: center; margin-top: 16px">
        <router-link to="/login" style="color: #409eff; text-decoration: none; font-size: 14px">返回登录</router-link>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import client from '@/api/client'

const router = useRouter()
const step = ref(0)
const sendLoading = ref(false)
const verifyLoading = ref(false)
const resetLoading = ref(false)

const phoneFormRef = ref<FormInstance>()
const codeFormRef = ref<FormInstance>()
const pwdFormRef = ref<FormInstance>()

const phoneForm = reactive({ phone: '' })
const codeForm = reactive({ code: '' })
const pwdForm = reactive({ password: '', confirmPassword: '' })

const phoneRules: FormRules = {
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' },
  ],
}
const codeRules: FormRules = { code: [{ required: true, message: '请输入验证码', trigger: 'blur' }] }
const pwdRules: FormRules = {
  password: [{ required: true, message: '请输入新密码', trigger: 'blur' }, { min: 6, message: '密码至少6位', trigger: 'blur' }],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: (_r: any, v: string, cb: any) => (v !== pwdForm.password ? cb(new Error('两次密码不一致')) : cb()), trigger: 'blur' },
  ],
}

async function handleSendCode() {
  const valid = await phoneFormRef.value?.validate().catch(() => false)
  if (!valid) return
  sendLoading.value = true
  try {
    await client.post('/auth/reset-password/send-code', { phone: phoneForm.phone })
    ElMessage.success('验证码已发送')
    step.value = 1
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '发送失败')
  } finally {
    sendLoading.value = false
  }
}

async function handleVerifyCode() {
  const valid = await codeFormRef.value?.validate().catch(() => false)
  if (!valid) return
  verifyLoading.value = true
  try {
    await client.post('/auth/reset-password/verify', { phone: phoneForm.phone, code: codeForm.code })
    step.value = 2
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '验证失败')
  } finally {
    verifyLoading.value = false
  }
}

async function handleResetPassword() {
  const valid = await pwdFormRef.value?.validate().catch(() => false)
  if (!valid) return
  resetLoading.value = true
  try {
    await client.post('/auth/reset-password/confirm', { phone: phoneForm.phone, code: codeForm.code, new_password: pwdForm.password })
    ElMessage.success('密码重置成功，请登录')
    router.push('/login')
  } catch (err: any) {
    ElMessage.error(err.response?.data?.detail || '重置失败')
  } finally {
    resetLoading.value = false
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
  width: 460px;
}
</style>
