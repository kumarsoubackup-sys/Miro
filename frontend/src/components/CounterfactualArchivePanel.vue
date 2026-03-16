<template>
  <div class="archive-panel">
    <section class="panel-block hero-block">
      <div class="block-head">
        <span class="block-kicker">ARCHIVE SIGNAL</span>
        <span class="block-id">{{ compactId }}</span>
      </div>
      <h2 class="block-title">Historical Run Snapshot</h2>
      <p class="block-copy">{{ requirementExcerpt }}</p>
      <div class="metric-grid">
        <div class="metric-card">
          <span class="metric-label">Actions</span>
          <span class="metric-value">{{ totalActions }}</span>
        </div>
        <div class="metric-card">
          <span class="metric-label">Rounds</span>
          <span class="metric-value">{{ totalRounds }}</span>
        </div>
        <div class="metric-card">
          <span class="metric-label">Agents</span>
          <span class="metric-value">{{ agentStats.length }}</span>
        </div>
      </div>
    </section>

    <section class="panel-block round-block">
      <div class="block-head">
        <span class="block-kicker">ROUND MAP</span>
        <span class="round-pill">R{{ selectedRound }}</span>
      </div>
      <input
        class="round-slider"
        type="range"
        :min="0"
        :max="sliderMax"
        :value="selectedRound"
        @input="emitRound($event.target.value)"
      />
      <div class="round-labels">
        <span>0</span>
        <span>{{ Math.floor(sliderMax / 2) }}</span>
        <span>{{ sliderMax }}</span>
      </div>
      <div class="heat-strip">
        <button
          v-for="round in timeline"
          :key="round.round_num"
          class="heat-cell"
          :class="{ active: round.round_num === selectedRound }"
          :style="{ '--cell-height': `${cellHeight(round)}px` }"
          @click="emitRound(round.round_num)"
          :title="`Round ${round.round_num}: ${round.total_actions} actions`"
        >
          <span></span>
        </button>
      </div>
    </section>

    <section class="panel-block agent-block">
      <div class="block-head">
        <span class="block-kicker">ACTIVE SOCIETIES</span>
        <span class="subtle">Top movers</span>
      </div>
      <div class="agent-list">
        <div v-for="agent in topAgents" :key="agent.agent_id" class="agent-row">
          <div>
            <div class="agent-name">{{ agent.agent_name || `Agent ${agent.agent_id}` }}</div>
            <div class="agent-meta">TW {{ agent.twitter_actions }} / RD {{ agent.reddit_actions }}</div>
          </div>
          <span class="agent-total">{{ agent.total_actions }}</span>
        </div>
      </div>
    </section>

    <section class="panel-block action-block">
      <div class="block-head">
        <span class="block-kicker">ROUND {{ selectedRound }}</span>
        <span class="subtle">{{ loadingActions ? 'Loading' : `${roundActions.length} captured` }}</span>
      </div>
      <div v-if="loadingActions" class="empty-state">Loading archived actions...</div>
      <div v-else-if="roundActions.length === 0" class="empty-state">No archived actions in this round.</div>
      <div v-else class="action-list">
        <article v-for="action in roundActions" :key="action.id || `${action.timestamp}-${action.agent_id}-${action.action_type}`" class="action-item">
          <div class="action-top">
            <span class="action-agent">{{ action.agent_name || `Agent ${action.agent_id}` }}</span>
            <span class="action-type">{{ action.action_type }}</span>
          </div>
          <div class="action-body">{{ actionText(action) }}</div>
          <div class="action-meta">{{ action.platform }} · {{ action.timestamp ? formatTime(action.timestamp) : 'n/a' }}</div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  simulationId: String,
  simulationData: Object,
  simulationConfig: Object,
  timeline: {
    type: Array,
    default: () => []
  },
  agentStats: {
    type: Array,
    default: () => []
  },
  roundActions: {
    type: Array,
    default: () => []
  },
  selectedRound: {
    type: Number,
    default: 0
  },
  loadingActions: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:selectedRound'])

const compactId = computed(() => (props.simulationId || 'sim_unknown').replace('sim_', 'SIM_').toUpperCase())
const totalActions = computed(() => props.timeline.reduce((sum, round) => sum + (round.total_actions || 0), 0))
const totalRounds = computed(() => props.timeline.length ? Math.max(...props.timeline.map(item => item.round_num || 0)) : 0)
const sliderMax = computed(() => totalRounds.value || 1)
const topAgents = computed(() => props.agentStats.slice(0, 8))
const requirementExcerpt = computed(() => {
  const requirement = props.simulationConfig?.simulation_requirement || props.simulationData?.simulation_requirement || ''
  if (!requirement) return 'Archived simulation context ready for counterfactual branching.'
  return requirement.length > 220 ? `${requirement.slice(0, 220)}...` : requirement
})

function emitRound(value) {
  emit('update:selectedRound', Number(value))
}

function cellHeight(round) {
  const max = Math.max(...props.timeline.map(item => item.total_actions || 0), 1)
  return 10 + (((round.total_actions || 0) / max) * 44)
}

function actionText(action) {
  const args = action.action_args || {}
  return args.content || args.quote_content || args.query || args.post_content || args.original_content || 'No captured body.'
}

function formatTime(timestamp) {
  try {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch {
    return timestamp
  }
}
</script>

<style scoped>
.archive-panel {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
  background: linear-gradient(180deg, #f7f7f4 0%, #eeefe7 100%);
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.panel-block {
  border: 1px solid #d7d9cf;
  background: rgba(255, 255, 255, 0.74);
  padding: 18px;
  box-shadow: 0 8px 20px rgba(19, 24, 19, 0.06);
}

.block-head,
.metric-grid,
.agent-row,
.action-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.block-kicker,
.block-id,
.round-pill,
.action-type,
.action-meta,
.agent-meta,
.subtle {
  font-family: 'JetBrains Mono', 'IBM Plex Mono', monospace;
}

.block-kicker,
.subtle,
.block-id {
  font-size: 11px;
  letter-spacing: 0.14em;
  color: #5d665e;
}

.block-title {
  margin: 12px 0 8px;
  font-size: 28px;
  line-height: 1.1;
  color: #11150f;
}

.block-copy {
  margin: 0;
  color: #425044;
  line-height: 1.7;
  font-size: 14px;
}

.metric-grid {
  margin-top: 18px;
}

.metric-card {
  flex: 1;
  padding: 12px 14px;
  border: 1px solid #dde2d2;
  background: #fdfef8;
}

.metric-label {
  display: block;
  font-size: 12px;
  color: #66715f;
  margin-bottom: 8px;
}

.metric-value {
  font-family: 'JetBrains Mono', 'IBM Plex Mono', monospace;
  font-size: 24px;
  color: #121611;
}

.round-slider {
  width: 100%;
  margin-top: 14px;
}

.round-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 6px;
  font-family: 'JetBrains Mono', 'IBM Plex Mono', monospace;
  font-size: 11px;
  color: #697267;
}

.heat-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(10px, 1fr));
  gap: 6px;
  align-items: end;
  margin-top: 18px;
}

.heat-cell {
  border: none;
  background: transparent;
  padding: 0;
  cursor: pointer;
}

.heat-cell span {
  display: block;
  width: 100%;
  height: var(--cell-height);
  min-height: 10px;
  background: linear-gradient(180deg, #bcc8bc, #4b5e51);
  opacity: 0.45;
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.heat-cell.active span,
.heat-cell:hover span {
  opacity: 1;
  transform: translateY(-2px);
}

.round-pill,
.action-type,
.agent-total {
  color: #0f1510;
  font-size: 11px;
  letter-spacing: 0.12em;
}

.agent-list,
.action-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 14px;
}

.agent-row,
.action-item {
  border: 1px solid #dfe3d8;
  background: rgba(255, 255, 255, 0.9);
  padding: 12px 14px;
}

.agent-name,
.action-agent {
  color: #131813;
  font-weight: 600;
}

.action-body {
  margin-top: 10px;
  color: #455145;
  line-height: 1.6;
  font-size: 13px;
}

.empty-state {
  margin-top: 14px;
  border: 1px dashed #c8d0c3;
  padding: 20px;
  text-align: center;
  color: #6a7368;
  font-family: 'JetBrains Mono', 'IBM Plex Mono', monospace;
  font-size: 12px;
}
</style>
