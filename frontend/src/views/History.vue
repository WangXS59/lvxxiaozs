<template>
  <a-card title="📋 历史行程">
    <a-table
      :dataSource="trips"
      :columns="columns"
      :loading="loading"
      rowKey="trip_id"
      size="middle"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'action'">
          <a-space>
            <a-button type="link" size="small" @click="handleView(record)">查看</a-button>
            <a-popconfirm title="确定删除？" @confirm="handleDelete(record.trip_id)">
              <a-button type="link" size="small" danger>删除</a-button>
            </a-popconfirm>
          </a-space>
        </template>
      </template>
    </a-table>
  </a-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue"
import { message } from "ant-design-vue"
import type { TripSummaryItem, Itinerary } from "../types"
import { listTrips, deleteTrip, getTripDetail } from "../services/api"

const emit = defineEmits<{ view: [itinerary: Itinerary] }>()

const loading = ref(false)
const trips = ref<TripSummaryItem[]>([])

const columns = [
  { title: "目的地", dataIndex: "destination", key: "destination" },
  { title: "概要", dataIndex: "summary", key: "summary", ellipsis: true },
  { title: "更新时间", dataIndex: "updated_at", key: "updated_at", width: 180 },
  { title: "操作", key: "action", width: 150 },
]

async function load() {
  loading.value = true
  try {
    trips.value = await listTrips()
  } catch (e) {
    message.error("加载失败")
  } finally {
    loading.value = false
  }
}

async function handleView(record: TripSummaryItem) {
  try {
    const itinerary = await getTripDetail(record.trip_id)
    emit("view", itinerary)
  } catch (e) {
    message.error("加载失败")
  }
}

async function handleDelete(tripId: string) {
  try {
    await deleteTrip(tripId)
    message.success("已删除")
    await load()
  } catch (e) {
    message.error("删除失败")
  }
}

onMounted(load)
</script>
