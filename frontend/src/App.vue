<template>
  <div class="app-container">
    <header class="app-header">
      <h1 @click="goHome">🗺️ 旅行小助手</h1>
      <nav>
        <a-button type="text" @click="goHome">规划行程</a-button>
        <a-button v-if="currentItinerary" type="text" @click="currentView = 'result'" style="color:#ffd666 !important">
          📋 当前行程
        </a-button>
        <a-button type="text" @click="currentView = 'history'">历史记录</a-button>
      </nav>
    </header>
    <main>
      <Home v-if="currentView === 'home'" @navigate="handleNavigate" />
      <Result
        v-else-if="currentView === 'result'"
        :itinerary="currentItinerary"
        :key="renderKey"
        @back="goHome"
        @update="handleItineraryUpdate"
      />
      <History
        v-else-if="currentView === 'history'"
        @view="handleViewTrip"
      />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue"
import Home from "./views/Home.vue"
import Result from "./views/Result.vue"
import History from "./views/History.vue"
import type { Itinerary } from "./types"

const currentView = ref<"home" | "result" | "history">("home")
const currentItinerary = ref<Itinerary | null>(null)
const renderKey = ref(0)

function handleItineraryUpdate(it: Itinerary) {
  currentItinerary.value = it
  renderKey.value++  // 强制 Result 组件重新渲染
}

function goHome() {
  // 回到首页但不清空当前行程，方便通过「当前行程」按钮回来
  currentView.value = "home"
}

function handleNavigate(view: string, itinerary?: Itinerary) {
  if (view === "result" && itinerary) {
    currentItinerary.value = itinerary
    currentView.value = "result"
  } else {
    currentView.value = view as any
  }
}

function handleViewTrip(itinerary: Itinerary) {
  currentItinerary.value = itinerary
  currentView.value = "result"
}
</script>

<style>
body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: #f0f2f5; }
.app-header {
  background: linear-gradient(135deg, #1677ff, #0958d9);
  color: white; padding: 0 24px; display: flex;
  align-items: center; justify-content: space-between; height: 56px;
}
.app-header h1 { margin: 0; font-size: 20px; cursor: pointer; }
.app-header nav .ant-btn-text { color: white !important; }
main { max-width: 1200px; margin: 24px auto; padding: 0 16px; }
</style>
