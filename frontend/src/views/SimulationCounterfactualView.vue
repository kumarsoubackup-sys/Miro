<template>
  <div class="main-view">
    <header class="app-header">
      <div class="header-left">
        <div class="brand" @click="router.push('/')">MIROFISH</div>
      </div>

      <div class="header-center">
        <div class="view-switcher">
          <button
            v-for="mode in ['archive', 'split', 'lab']"
            :key="mode"
            class="switch-btn"
            :class="{ active: viewMode === mode }"
            @click="viewMode = mode"
          >
            {{ { archive: '档案', split: '双栏', lab: '实验室' }[mode] }}
          </button>
        </div>
      </div>

      <div class="header-right">
        <div class="workflow-step">
          <span class="step-num">Step 3/5</span>
          <span class="step-name">反事实注入</span>
        </div>
        <div class="step-divider"></div>
        <span class="status-indicator" :class="statusClass">
          <span class="dot"></span>
          {{ statusText }}
        </span>
      </div>
    </header>

    <main class="content-area">
      <div class="panel-wrapper left" :style="leftPanelStyle">
        <CounterfactualArchivePanel
          :simulation-id="currentSimulationId"
          :simulation-data="simulationData"
          :simulation-config="simulationConfig"
          :timeline="timeline"
          :agent-stats="agentStats"
          :round-actions="roundActions"
          :selected-round="selectedRound"
          :loading-actions="loadingActions"
          @update:selectedRound="selectedRound = $event"
        />
      </div>

      <div class="panel-wrapper right" :style="rightPanelStyle">
        <CounterfactualLabPanel
          :simulation-id="currentSimulationId"
          :profiles="profiles"
          :selected-round="selectedRound"
          :max-round="maxRound"
          @launched="handleLaunched"
        />
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import CounterfactualArchivePanel from '../components/CounterfactualArchivePanel.vue'
import CounterfactualLabPanel from '../components/CounterfactualLabPanel.vue'
import {
  getSimulation,
  getSimulationConfig,
  getSimulationTimeline,
  getAgentStats,
  getSimulationActions,
  getSimulationProfiles
} from '../api/simulation'

const route = useRoute()
const router = useRouter()

const viewMode = ref('split')
const currentSimulationId = ref(route.params.simulationId)
const simulationData = ref(null)
const simulationConfig = ref(null)
const timeline = ref([])
const agentStats = ref([])
const roundActions = ref([])
const profiles = ref([])
const selectedRound = ref(0)
const loadingActions = ref(false)
const currentStatus = ref('processing')

const maxRound = computed(() => timeline.value.length ? Math.max(...timeline.value.map(item => item.round_num || 0)) : 0)

const leftPanelStyle = computed(() => {
  if (viewMode.value === 'archive') return { width: '100%', opacity: 1, transform: 'translateX(0)' }
  if (viewMode.value === 'lab') return { width: '0%', opacity: 0, transform: 'translateX(-20px)' }
  return { width: '54%', opacity: 1, transform: 'translateX(0)' }
})

const rightPanelStyle = computed(() => {
  if (viewMode.value === 'lab') return { width: '100%', opacity: 1, transform: 'translateX(0)' }
  if (viewMode.value === 'archive') return { width: '0%', opacity: 0, transform: 'translateX(20px)' }
  return { width: '46%', opacity: 1, transform: 'translateX(0)' }
})

const statusClass = computed(() => currentStatus.value)
const statusText = computed(() => {
  if (currentStatus.value === 'error') return 'Error'
  if (currentStatus.value === 'completed') return 'Ready'
  return 'Loading'
})

async function loadBaseData() {
  currentStatus.value = 'processing'
  const simulationId = currentSimulationId.value
  try {
    const [simulationRes, configRes, timelineRes, agentStatsRes, profilesRes] = await Promise.all([
      getSimulation(simulationId),
      getSimulationConfig(simulationId),
      getSimulationTimeline(simulationId, 0),
      getAgentStats(simulationId),
      getSimulationProfiles(simulationId, 'reddit')
    ])

    simulationData.value = simulationRes.data || null
    simulationConfig.value = configRes.data || null
    timeline.value = timelineRes.data || []
    agentStats.value = agentStatsRes.data || []
    profiles.value = profilesRes.data?.profiles || []

    if (timeline.value.length > 0) {
      const hottestRound = [...timeline.value].sort((a, b) => (b.total_actions || 0) - (a.total_actions || 0))[0]
      selectedRound.value = hottestRound?.round_num || timeline.value[0].round_num
    }

    currentStatus.value = 'completed'
  } catch (error) {
    console.error('加载反事实工作台失败:', error)
    currentStatus.value = 'error'
  }
}

async function loadRoundActions(roundNum) {
  if (roundNum === null || roundNum === undefined) return
  loadingActions.value = true
  try {
    const response = await getSimulationActions(currentSimulationId.value, {
      round_num: roundNum,
      limit: 300
    })
    roundActions.value = response.data?.actions || []
  } catch (error) {
    console.error('加载轮次动作失败:', error)
    roundActions.value = []
  } finally {
    loadingActions.value = false
  }
}

function handleLaunched(payload) {
  const simulationId = payload?.simulation?.simulation_id
  if (!simulationId) return
  router.push({
    name: 'SimulationRun',
    params: { simulationId }
  })
}

watch(selectedRound, (round) => {
  loadRoundActions(round)
})

onMounted(async () => {
  await loadBaseData()
})
</script>

<style scoped>
.main-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  overflow: hidden;
  font-family: 'Space Grotesk', 'Noto Sans SC', system-ui, sans-serif;
}

.app-header {
  height: 60px;
  border-bottom: 1px solid #eaeaea;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: #fff;
  z-index: 100;
  position: relative;
}

.header-center {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
}

.brand {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 800;
  font-size: 18px;
  letter-spacing: 1px;
  cursor: pointer;
}

.view-switcher {
  display: flex;
  background: #f5f5f5;
  padding: 4px;
  border-radius: 6px;
  gap: 4px;
}

.switch-btn {
  border: none;
  background: transparent;
  padding: 6px 16px;
  font-size: 12px;
  font-weight: 600;
  color: #666;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.switch-btn.active {
  background: #fff;
  color: #000;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.workflow-step {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.step-num {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  color: #999;
}

.step-name {
  font-weight: 700;
  color: #000;
}

.step-divider {
  width: 1px;
  height: 14px;
  background-color: #e0e0e0;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ccc;
}

.status-indicator.processing .dot {
  background: #ff5722;
  animation: pulse 1s infinite;
}

.status-indicator.completed .dot {
  background: #4caf50;
}

.status-indicator.error .dot {
  background: #f44336;
}

@keyframes pulse {
  50% { opacity: 0.5; }
}

.content-area {
  flex: 1;
  display: flex;
  position: relative;
  overflow: hidden;
}

.panel-wrapper {
  height: 100%;
  overflow: hidden;
  transition: width 0.4s cubic-bezier(0.25, 0.8, 0.25, 1), opacity 0.3s ease, transform 0.3s ease;
}

.panel-wrapper.left {
  border-right: 1px solid #eaeaea;
}
</style>
