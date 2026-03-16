<template>
  <div class="lab-panel">
    <section class="lab-shell">
      <div class="shell-head">
        <div>
          <span class="shell-kicker">COUNTERFACTUAL LAB</span>
          <h2>Inject an actor into a historical run</h2>
        </div>
        <div class="shell-note">Base run stays untouched</div>
      </div>

      <div class="lab-grid">
        <label class="field full">
          <span>Template Profile</span>
          <select v-model="selectedTemplateId" @change="applyTemplate">
            <option value="">Custom actor</option>
            <option v-for="profile in profiles" :key="profile.user_id" :value="String(profile.user_id)">
              {{ profile.name }} · {{ profile.profession || profile.country || 'template' }}
            </option>
          </select>
        </label>

        <label class="field">
          <span>Actor Name</span>
          <input v-model="form.name" type="text" placeholder="EU backchannel envoy" />
        </label>

        <label class="field">
          <span>Role</span>
          <select v-model="form.entity_type">
            <option>Diplomat</option>
            <option>GovernmentOfficial</option>
            <option>MediaOutlet</option>
            <option>Organization</option>
            <option>PredictionMarket</option>
            <option>StrategicActor</option>
          </select>
        </label>

        <label class="field">
          <span>Profession</span>
          <input v-model="form.profession" type="text" placeholder="Diplomatic mediator" />
        </label>

        <label class="field">
          <span>Country</span>
          <input v-model="form.country" type="text" placeholder="France" />
        </label>

        <label class="field">
          <span>Stance</span>
          <select v-model="form.stance">
            <option>observer</option>
            <option>mediator</option>
            <option>hawkish</option>
            <option>dovish</option>
            <option>neutral</option>
          </select>
        </label>

        <label class="field">
          <span>Injection Round</span>
          <input v-model.number="form.injection_round" type="number" :min="0" :max="maxRound" />
        </label>

        <label class="field">
          <span>Active Hours Preset</span>
          <select v-model="form.active_hours_preset">
            <option value="office">Office Hours</option>
            <option value="newsdesk">Newsdesk</option>
            <option value="always_on">Always On</option>
            <option value="evening">Evening Window</option>
          </select>
        </label>

        <label class="field">
          <span>Activity Level</span>
          <input v-model.number="form.activity_level" type="range" min="0.1" max="1" step="0.05" />
          <small>{{ form.activity_level.toFixed(2) }}</small>
        </label>

        <label class="field">
          <span>Influence Weight</span>
          <input v-model.number="form.influence_weight" type="range" min="1" max="5" step="0.1" />
          <small>{{ form.influence_weight.toFixed(1) }}</small>
        </label>

        <label class="field">
          <span>Posts / Hour</span>
          <input v-model.number="form.posts_per_hour" type="number" min="0.1" max="6" step="0.1" />
        </label>

        <label class="field">
          <span>Comments / Hour</span>
          <input v-model.number="form.comments_per_hour" type="number" min="0.1" max="6" step="0.1" />
        </label>

        <label class="field full">
          <span>Interested Topics</span>
          <input v-model="form.interested_topics_text" type="text" placeholder="backchannel diplomacy, nuclear inspections, sanctions relief" />
        </label>

        <label class="field full">
          <span>Bio</span>
          <textarea v-model="form.bio" rows="3" placeholder="Short public-facing identity for the injected actor"></textarea>
        </label>

        <label class="field full">
          <span>Persona</span>
          <textarea v-model="form.persona" rows="4" placeholder="Internal worldview, incentives, blind spots"></textarea>
        </label>

        <label class="field full">
          <span>Opening Statement At Injection</span>
          <textarea v-model="form.opening_statement" rows="4" placeholder="Optional first message this actor posts when the chosen round starts"></textarea>
        </label>
      </div>

      <div class="submit-row">
        <div class="submit-note">
          New branch will be cloned from <strong>{{ simulationId }}</strong> and launched from the original starting point.
        </div>
        <button class="launch-btn" :disabled="launching || !canLaunch" @click="launchBranch">
          <span v-if="launching">BRANCHING...</span>
          <span v-else>LAUNCH COUNTERFACTUAL</span>
        </button>
      </div>

      <div v-if="error" class="error-box">{{ error }}</div>
    </section>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { createCounterfactualSimulation } from '../api/simulation'

const props = defineProps({
  simulationId: String,
  profiles: {
    type: Array,
    default: () => []
  },
  selectedRound: {
    type: Number,
    default: 0
  },
  maxRound: {
    type: Number,
    default: 1
  }
})

const emit = defineEmits(['launched'])

const launching = ref(false)
const error = ref('')
const selectedTemplateId = ref('')
const form = reactive({
  name: '',
  entity_type: 'Diplomat',
  profession: 'Diplomat',
  country: 'Global',
  stance: 'observer',
  injection_round: 0,
  active_hours_preset: 'office',
  activity_level: 0.45,
  influence_weight: 2.4,
  posts_per_hour: 1.0,
  comments_per_hour: 0.7,
  bio: '',
  persona: '',
  interested_topics_text: '',
  opening_statement: '',
  age: 38,
  gender: 'other',
  mbti: 'INTJ'
})

const canLaunch = computed(() => form.name.trim().length > 1 && form.persona.trim().length > 0)

watch(() => props.selectedRound, (round) => {
  form.injection_round = round
}, { immediate: true })

function activeHoursFromPreset(preset) {
  if (preset === 'always_on') return Array.from({ length: 24 }, (_, idx) => idx)
  if (preset === 'newsdesk') return [6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]
  if (preset === 'evening') return [15,16,17,18,19,20,21,22,23]
  return [8,9,10,11,12,13,14,15,16,17,18]
}

function applyTemplate() {
  const profile = props.profiles.find(item => String(item.user_id) === selectedTemplateId.value)
  if (!profile) return

  form.name = `${profile.name} Branch`
  form.profession = profile.profession || form.profession
  form.country = profile.country || form.country
  form.bio = profile.bio || form.bio
  form.persona = profile.persona || form.persona
  form.interested_topics_text = Array.isArray(profile.interested_topics) ? profile.interested_topics.join(', ') : form.interested_topics_text
  form.age = profile.age || form.age
  form.gender = profile.gender || form.gender
  form.mbti = profile.mbti || form.mbti
  if (profile.profession === 'Diplomat' || profile.profession === 'GovernmentOfficial') {
    form.entity_type = profile.profession
  }
}

async function launchBranch() {
  launching.value = true
  error.value = ''
  try {
    const actor = {
      name: form.name.trim(),
      entity_type: form.entity_type,
      profession: form.profession.trim() || form.entity_type,
      country: form.country.trim() || 'Global',
      stance: form.stance,
      bio: form.bio.trim(),
      persona: form.persona.trim(),
      interested_topics: form.interested_topics_text.split(',').map(item => item.trim()).filter(Boolean),
      activity_level: form.activity_level,
      influence_weight: form.influence_weight,
      posts_per_hour: form.posts_per_hour,
      comments_per_hour: form.comments_per_hour,
      active_hours: activeHoursFromPreset(form.active_hours_preset),
      response_delay_min: 10,
      response_delay_max: 45,
      age: form.age,
      gender: form.gender,
      mbti: form.mbti
    }

    const response = await createCounterfactualSimulation(props.simulationId, {
      actor,
      injection_round: form.injection_round,
      opening_statement: form.opening_statement.trim()
    })

    emit('launched', response.data)
  } catch (launchError) {
    error.value = launchError.message || 'Failed to create counterfactual branch'
  } finally {
    launching.value = false
  }
}
</script>

<style scoped>
.lab-panel {
  height: 100%;
  overflow-y: auto;
  background: radial-gradient(circle at top, rgba(17, 40, 30, 0.95), #050908 48%);
  color: #dbffed;
  padding: 24px;
}

.lab-shell {
  border: 1px solid rgba(122, 240, 181, 0.14);
  background: rgba(4, 9, 8, 0.84);
  padding: 22px;
}

.shell-head,
.submit-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.shell-kicker,
.shell-note,
.submit-note,
.field span,
.field small {
  font-family: 'JetBrains Mono', 'IBM Plex Mono', monospace;
}

.shell-kicker,
.shell-note,
.field span,
.field small {
  font-size: 11px;
  letter-spacing: 0.14em;
  color: rgba(219, 255, 237, 0.62);
}

.shell-head h2 {
  margin: 10px 0 0;
  font-size: 30px;
  line-height: 1.1;
}

.lab-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  margin-top: 22px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field.full {
  grid-column: 1 / -1;
}

.field input,
.field select,
.field textarea {
  width: 100%;
  border: 1px solid rgba(122, 240, 181, 0.14);
  background: rgba(255, 255, 255, 0.03);
  color: #f3fff8;
  padding: 12px 13px;
  font: inherit;
}

.field textarea {
  resize: vertical;
}

.submit-row {
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px solid rgba(122, 240, 181, 0.1);
}

.submit-note {
  max-width: 380px;
  font-size: 12px;
  line-height: 1.7;
  color: rgba(219, 255, 237, 0.76);
}

.launch-btn {
  border: 1px solid rgba(122, 240, 181, 0.18);
  background: linear-gradient(90deg, rgba(77, 226, 165, 0.16), rgba(255, 211, 106, 0.12));
  color: #f7fff9;
  padding: 14px 18px;
  font-family: 'JetBrains Mono', 'IBM Plex Mono', monospace;
  font-size: 11px;
  letter-spacing: 0.14em;
  cursor: pointer;
}

.launch-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.error-box {
  margin-top: 16px;
  padding: 12px 14px;
  border: 1px solid rgba(255, 107, 107, 0.4);
  color: #ffb4b4;
  background: rgba(255, 107, 107, 0.08);
  font-size: 13px;
}

@media (max-width: 980px) {
  .lab-grid {
    grid-template-columns: 1fr;
  }

  .submit-row {
    flex-direction: column;
  }
}
</style>
