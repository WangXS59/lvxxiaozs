<template>
  <div>
    <a-space style="margin-bottom:16px">
      <a-button @click="$emit('back')">← 返回</a-button>
      <a-button type="primary" @click="handleSave">💾 保存行程</a-button>
      <a-button :href="mdUrl" target="_blank">📄 导出 MD</a-button>
      <a-button :href="pdfUrl" target="_blank">📕 导出 PDF</a-button>
    </a-space>

    <a-card :title="`${itinerary.destination} · ${itinerary.summary}`" style="margin-bottom:16px">
      <a-row :gutter="16">
        <a-col :span="6">
          <a-statistic title="总预算" :value="itinerary.estimated_budget" prefix="¥" />
        </a-col>
        <a-col :span="6">
          <a-statistic title="行程天数" :value="itinerary.days.length" suffix="天" />
        </a-col>
        <a-col :span="6">
          <a-statistic title="景点数" :value="totalSpots" suffix="个" />
        </a-col>
        <a-col :span="6">
          <div v-if="weather.forecasts.length">
            <span style="color:#888">整体天气</span><br/>
            <span>{{ weather.forecasts[0]?.day_weather }} {{ weather.forecasts[0]?.day_temp }}°C</span>
          </div>
        </a-col>
      </a-row>
    </a-card>

    <!-- 地图 -->
    <a-card title="🗺️ 路线导航" style="margin-bottom:16px">
      <AmapTripMap
        v-if="hasCoordinates"
        :days="itinerary.days"
        :destination="itinerary.destination"
        :height="360"
      />
      <div v-else style="text-align:center;padding:24px;color:#888">
        地图坐标加载中（高德地图 API 补全中）
      </div>
    </a-card>

    <!-- 每日行程 -->
    <a-card v-for="day in itinerary.days" :key="day.day_index" style="margin-bottom:12px">
      <template #title>
        <span>📅 第{{ day.day_index + 1 }}天 · {{ day.theme }}</span>
      </template>
      <template #extra>
        <a-space>
          <span style="color:#888">{{ day.date }}</span>
          <!-- 当天天气 -->
          <span v-if="getDayWeather(day.date)" style="color:#1677ff">
            {{ getDayWeather(day.date)?.day_weather }}
            {{ getDayWeather(day.date)?.day_temp }}°C
          </span>
          <!-- 编辑按钮 -->
          <a-button size="small" type="dashed" @click="startEdit(day.day_index)">
            ✏️ 智能调整
          </a-button>
        </a-space>
      </template>

      <!-- 编辑面板 -->
      <div v-if="editingDay === day.day_index" style="margin-bottom:12px;padding:12px;background:#fffbe6;border:1px solid #ffe58f;border-radius:6px">
        <a-input
          v-model:value="editInstruction"
          placeholder="用自然语言描述想怎么改，如：把下午行程换成逛古城，午餐安排吃米线"
          @pressEnter="handleEdit(day.day_index)"
          style="margin-bottom:8px"
        />
        <a-space>
          <a-button size="small" type="primary" :loading="editLoading" @click="handleEdit(day.day_index)">
            🤖 AI 调整
          </a-button>
          <a-button size="small" @click="editingDay = -1">取消</a-button>
        </a-space>
      </div>

      <div v-for="spot in day.spots" :key="spot.name" style="margin-bottom:12px">
        <h4>🏛 {{ spot.name }}</h4>
        <p>{{ spot.description }}</p>
        <a-space>
          <a-tag v-if="spot.estimated_cost">💰 ¥{{ spot.estimated_cost }}</a-tag>
          <a-tag v-if="spot.location?.address">📍 {{ spot.location.address }}</a-tag>
        </a-space>
      </div>

      <div v-for="meal in day.meals" :key="meal.name" style="margin-bottom:8px">
        <a-tag color="orange">🍽 {{ meal.type }}</a-tag>
        <strong>{{ meal.name }}</strong>
        <span v-if="meal.description" style="color:#888;margin-left:8px">{{ meal.description }}</span>
      </div>

      <!-- 住宿推荐 -->
      <div v-if="day.hotel && day.hotel.name" style="margin-top:12px;padding:10px 14px;background:#f6ffed;border:1px solid #b7eb8f;border-radius:6px">
        <strong>🏨 当晚住宿：{{ day.hotel.name }}</strong>
        <span v-if="day.hotel.level" style="margin-left:8px;color:#888">（{{ day.hotel.level }}）</span>
        <span v-if="day.hotel.estimated_cost" style="margin-left:8px">💰 ¥{{ day.hotel.estimated_cost }}</span>
        <div v-if="day.hotel.notes" style="margin-top:4px;color:#666;font-size:13px">{{ day.hotel.notes }}</div>
      </div>

      <a-alert v-if="day.notes" :message="day.notes" type="info" show-icon style="margin-top:8px" />
    </a-card>

    <!-- 预算明细 -->
    <a-card title="💵 预算明细" style="margin-bottom:16px">
      <a-row :gutter="16">
        <a-col :span="4" v-for="item in budgetItems" :key="item.label">
          <a-statistic :title="item.label" :value="item.value" prefix="¥" />
        </a-col>
      </a-row>
    </a-card>

    <!-- 旅行提示 -->
    <a-card title="💡 旅行提示" v-if="itinerary.tips.length">
      <ul>
        <li v-for="tip in itinerary.tips" :key="tip">{{ tip }}</li>
      </ul>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, reactive, watch } from "vue"
import { message } from "ant-design-vue"
import type { Itinerary, WeatherResponse, WeatherForecast } from "../types"
import { saveTrip, fetchWeather, getMarkdownUrl, getPdfUrl, editTripDay } from "../services/api"
import AmapTripMap from "../components/AmapTripMap.vue"

const props = defineProps<{ itinerary: Itinerary }>()
const emit = defineEmits<{ update: [itinerary: Itinerary]; back: [] }>()

// 组件内部响应式副本 —— 这才是界面实际渲染的数据源
const itinerary = reactive<Itinerary>(JSON.parse(JSON.stringify(props.itinerary)))

// prop 变化时同步到内部副本
watch(() => props.itinerary, (val) => {
  if (val) Object.assign(itinerary, JSON.parse(JSON.stringify(val)))
}, { deep: true })

const weather = ref<WeatherResponse>({ city: "", forecasts: [] })
const mdUrl = computed(() => getMarkdownUrl(itinerary.trip_id))
const pdfUrl = computed(() => getPdfUrl(itinerary.trip_id))

// 编辑状态
const editingDay = ref(-1)
const editInstruction = ref("")
const editLoading = ref(false)

const totalSpots = computed(() =>
  itinerary.days.reduce((sum, d) => sum + d.spots.length, 0)
)

const hasCoordinates = computed(() =>
  itinerary.days.some((d) =>
    d.spots.some((s) => s.location?.latitude && s.location?.longitude)
  )
)

const budgetItems = computed(() => {
  const bd = itinerary.budget_breakdown
  return [
    { label: "交通", value: bd.transport },
    { label: "住宿", value: bd.hotel },
    { label: "餐饮", value: bd.meals },
    { label: "门票", value: bd.tickets },
    { label: "其他", value: bd.other },
  ]
})

// 按日期匹配天气
function getDayWeather(dateStr: string): WeatherForecast | undefined {
  if (!dateStr) return undefined
  return weather.value.forecasts.find((f) => f.date === dateStr)
}

function startEdit(dayIndex: number) {
  editingDay.value = dayIndex
  editInstruction.value = ""
}

async function handleEdit(dayIndex: number) {
  if (!editInstruction.value.trim()) {
    message.warning("请输入调整内容")
    return
  }
  editLoading.value = true
  try {
    const resp = await editTripDay(itinerary.trip_id, dayIndex, editInstruction.value)
    // 直接把 API 返回的新数据写入本地响应式副本，界面立即刷新
    const updated: Itinerary = resp.itinerary
    itinerary.days = updated.days
    itinerary.summary = updated.summary
    itinerary.tips = updated.tips
    itinerary.budget_breakdown = updated.budget_breakdown
    // 同步通知父组件
    emit("update", { ...itinerary } as Itinerary)
    message.success("调整完成！")
    editingDay.value = -1
  } catch (e: any) {
    message.error("调整失败：" + (e?.response?.data?.detail || e.message))
  } finally {
    editLoading.value = false
  }
}

async function handleSave() {
  try {
    await saveTrip(itinerary as Itinerary)
    message.success("保存成功！")
  } catch (e: any) {
    message.error("保存失败：" + e.message)
  }
}

onMounted(async () => {
  try {
    weather.value = await fetchWeather(itinerary.destination)
  } catch (e) {}
})
</script>
