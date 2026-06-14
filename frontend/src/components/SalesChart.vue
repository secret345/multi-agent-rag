<template>
  <div v-if="salesData" class="sales-chart-container">
    <el-row :gutter="16">
      <el-col :span="12">
        <p class="chart-label">原始数据</p>
        <el-table :data="salesData.rows" size="small" max-height="250" stripe border>
          <el-table-column v-for="col in salesData.columns" :key="col" :prop="col" :label="col" />
        </el-table>
      </el-col>
      <el-col :span="12">
        <p class="chart-label">销量统计</p>
        <div ref="chartRef" style="height: 250px"></div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import Plotly from 'plotly.js-dist-min'
import { useChatStore } from '@/stores/chat'
import type { SalesData } from '@/types'

const chatStore = useChatStore()
const salesData = ref<SalesData | null>(null)
const chartRef = ref<HTMLElement>()

onMounted(async () => {
  salesData.value = await chatStore.getSalesData()
  await nextTick()
  if (chartRef.value && salesData.value?.summary) {
    Plotly.newPlot(chartRef.value, [{
      x: salesData.value.summary.map((d) => d.product),
      y: salesData.value.summary.map((d) => d.quantity),
      type: 'bar',
      text: salesData.value.summary.map((d) => String(d.quantity)),
      textposition: 'auto',
      marker: {
        color: ['#409eff', '#67c23a', '#e6a23c', '#f56c6c', '#909399'],
      },
    }], {
      margin: { t: 10, b: 40, l: 40, r: 10 },
      xaxis: { title: '产品' },
      yaxis: { title: '销量' },
    }, { responsive: true, displayModeBar: false })
  }
})
</script>

<style scoped>
.sales-chart-container {
  margin-top: 12px;
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
}

.chart-label {
  font-size: 12px;
  color: #909399;
  margin: 0 0 8px;
}
</style>
