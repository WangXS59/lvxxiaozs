<template>
  <div>
    <div v-if="loading" style="text-align:center;padding:40px;color:#888">
      🗺️ 地图加载中...
    </div>
    <div :id="mapContainerId" :style="{ width: '100%', height: height + 'px' }"></div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from "vue"
import type { DayPlan } from "../types"

const props = defineProps<{
  days: DayPlan[]
  destination: string
  height?: number
}>()

const mapContainerId = "amap-container-" + Math.random().toString(36).slice(2, 8)
const loading = ref(true)
let map: any = null
let markers: any[] = []

function loadAmapScript(): Promise<void> {
  return new Promise((resolve, reject) => {
    if ((window as any).AMap) {
      resolve()
      return
    }
    const AMAP_JS_KEY = (import.meta.env.VITE_AMAP_JS_KEY as string) || ""
    if (!AMAP_JS_KEY) {
      reject(new Error("未配置高德地图 JS Key：请在 frontend/.env 中设置 VITE_AMAP_JS_KEY"))
      return
    }
    const script = document.createElement("script")
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${AMAP_JS_KEY}&plugin=AMap.Polyline`
    script.onload = () => resolve()
    script.onerror = () => reject(new Error("地图加载失败"))
    document.head.appendChild(script)
  })
}

function initMap() {
  const allSpots: any[] = []
  props.days.forEach((day) => {
    day.spots.forEach((spot) => {
      if (spot.location?.latitude && spot.location?.longitude) {
        allSpots.push({
          ...spot,
          day_index: day.day_index,
          theme: day.theme,
        })
      }
    })
  })

  if (allSpots.length === 0) {
    loading.value = false
    return
  }

  const dom = document.getElementById(mapContainerId)
  if (!dom) return

  map = new (window as any).AMap.Map(dom, {
    zoom: 12,
    center: [allSpots[0].location?.longitude, allSpots[0].location?.latitude],
    resizeEnable: true,
  })

  // 添加标记点
  const iconColors = ["#1677ff", "#52c41a", "#fa8c16", "#eb2f96", "#722ed1", "#13c2c2", "#f5222d"]
  allSpots.forEach((spot, i) => {
    const color = iconColors[spot.day_index % iconColors.length]
    const marker = new (window as any).AMap.Marker({
      position: [spot.location?.longitude, spot.location?.latitude],
      title: `D${spot.day_index + 1} ${spot.name}`,
      label: {
        content: `<div style="background:${color};color:#fff;padding:2px 8px;border-radius:12px;font-size:12px;white-space:nowrap">D${spot.day_index + 1} ${spot.name}</div>`,
        offset: new (window as any).AMap.Pixel(0, -30),
      },
    })
    marker.setMap(map)

    // 点击弹出信息窗
    marker.on("click", () => {
      const info = new (window as any).AMap.InfoWindow({
        content: `
          <div style="padding:8px;max-width:250px">
            <h4 style="margin:0 0 4px">📅 第${spot.day_index + 1}天 · ${spot.theme || ""}</h4>
            <strong>${spot.name}</strong>
            <p style="margin:4px 0;color:#666">${spot.description?.slice(0, 80) || ""}</p>
            <span style="color:#888">📍 ${spot.location?.address || ""}</span>
          </div>
        `,
        offset: new (window as any).AMap.Pixel(0, -30),
      })
      info.open(map, marker.getPosition())
    })
    markers.push(marker)
  })

  // 按天画路线（虚线箭头）
  const dayGroups: any[][] = []
  props.days.forEach((day) => {
    const group: any[] = []
    day.spots.forEach((spot) => {
      if (spot.location?.latitude && spot.location?.longitude) {
        group.push([spot.location.longitude, spot.location.latitude])
      }
    })
    if (group.length >= 2) dayGroups.push(group)
  })

  const lineColors = ["#1677ff", "#52c41a", "#fa8c16", "#eb2f96", "#722ed1"]
  dayGroups.forEach((path, i) => {
    new (window as any).AMap.Polyline({
      path,
      strokeColor: lineColors[i % lineColors.length],
      strokeWeight: 3,
      strokeOpacity: 0.7,
      strokeStyle: "dashed",
      lineJoin: "round",
      showDir: true,
      map,
    })
  })

  // 自适应视野
  map.setFitView(null, false, [80, 80, 80, 80])
  loading.value = false
}

onMounted(async () => {
  try {
    await loadAmapScript()
    initMap()
  } catch (e) {
    loading.value = false
  }
})

onBeforeUnmount(() => {
  if (map) map.destroy()
})
</script>
