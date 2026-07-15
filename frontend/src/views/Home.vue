<template>
  <a-card title="规划你的旅行" class="home-card">
    <a-form layout="vertical" :model="form" @finish="handleSubmit">
      <a-row :gutter="16">
        <a-col :span="8">
          <a-form-item label="目的地" required>
            <a-input v-model:value="form.destination" placeholder="如：大理" />
          </a-form-item>
        </a-col>
        <a-col :span="4">
          <a-form-item label="出发日期" required>
            <a-date-picker v-model:value="form.start_date" style="width:100%" />
          </a-form-item>
        </a-col>
        <a-col :span="4">
          <a-form-item label="结束日期" required>
            <a-date-picker v-model:value="form.end_date" style="width:100%" />
          </a-form-item>
        </a-col>
        <a-col :span="4">
          <a-form-item label="人数">
            <a-input-number v-model:value="form.travelers" :min="1" style="width:100%" />
          </a-form-item>
        </a-col>
        <a-col :span="4">
          <a-form-item label="预算（元）">
            <a-input-number v-model:value="form.budget" :min="0" :step="500" style="width:100%" placeholder="可选" />
          </a-form-item>
        </a-col>
      </a-row>
      <a-row :gutter="16">
        <a-col :span="8">
          <a-form-item label="旅行偏好">
            <a-select v-model:value="form.preferences" placeholder="可选">
              <a-select-option value="喜爱自然风光">喜爱自然风光</a-select-option>
              <a-select-option value="偏爱历史文化">偏爱历史文化</a-select-option>
              <a-select-option value="美食探店为主">美食探店为主</a-select-option>
              <a-select-option value="休闲度假放松">休闲度假放松</a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
        <a-col :span="4">
          <a-form-item label="旅行节奏">
            <a-select v-model:value="form.pace">
              <a-select-option value="轻松">轻松</a-select-option>
              <a-select-option value="适中">适中</a-select-option>
              <a-select-option value="紧凑">紧凑</a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
        <a-col :span="4">
          <a-form-item label="住宿档次">
            <a-select v-model:value="form.hotel_level">
              <a-select-option value="经济型">经济型</a-select-option>
              <a-select-option value="舒适型">舒适型</a-select-option>
              <a-select-option value="豪华型">豪华型</a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
        <a-col :span="8">
          <a-form-item label="额外要求">
            <a-input v-model:value="form.special_notes" placeholder="如：不去太累的景点" />
          </a-form-item>
        </a-col>
      </a-row>
      <a-form-item>
        <a-button type="primary" html-type="submit" :loading="loading" size="large" block>
          🧠 AI 生成旅行计划
        </a-button>
      </a-form-item>
    </a-form>
  </a-card>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue"
import { message } from "ant-design-vue"
import { generateTrip } from "../services/api"
import type { Itinerary } from "../types"
import dayjs from "dayjs"

const emit = defineEmits<{ navigate: [view: string, itinerary?: Itinerary] }>()

const loading = ref(false)
const form = reactive({
  destination: "",
  start_date: null as any,
  end_date: null as any,
  travelers: 2,
  budget: null as number | null,
  preferences: undefined as string | undefined,
  pace: "适中",
  hotel_level: "舒适型",
  special_notes: "",
})

async function handleSubmit() {
  if (!form.destination || !form.start_date || !form.end_date) {
    message.warning("请填写目的地和日期")
    return
  }
  loading.value = true
  try {
    const resp = await generateTrip({
      destination: form.destination,
      start_date: form.start_date.format("YYYY-MM-DD"),
      end_date: form.end_date.format("YYYY-MM-DD"),
      travelers: form.travelers,
      budget: form.budget || undefined,
      preferences: form.preferences,
      pace: form.pace,
      hotel_level: form.hotel_level,
      special_notes: form.special_notes,
    })
    message.success("行程生成成功！")
    emit("navigate", "result", resp.itinerary)
  } catch (e: any) {
    message.error("生成失败：" + (e?.response?.data?.detail || e.message))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.home-card { max-width: 900px; margin: 0 auto; }
</style>
