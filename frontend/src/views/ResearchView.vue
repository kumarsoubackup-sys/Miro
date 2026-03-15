<template>
  <div class="research-view">
    <header class="research-header">
      <div class="header-left">
        <button class="brand-btn" @click="router.push('/')">MIROFISH</button>
        <div class="header-copy">
          <div class="eyebrow">Research Mode</div>
          <h1>Bottleneck Research Workbench</h1>
        </div>
      </div>

      <div class="header-right">
        <div class="ontology-chip" v-if="ontology">
          {{ ontology.ontology_name }} / {{ ontology.ontology_version }}
        </div>
        <button class="ghost-btn" @click="refreshProjects" :disabled="projectListLoading">
          {{ projectListLoading ? 'Refreshing...' : 'Refresh Projects' }}
        </button>
      </div>
    </header>

    <main class="research-layout">
      <aside class="sidebar">
        <section class="panel create-panel">
          <div class="panel-header">
            <span class="panel-kicker">01 / New Research Project</span>
          </div>

          <div class="field-grid">
            <label class="field">
              <span>Project Name</span>
              <input v-model="createForm.name" type="text" placeholder="InP photonics map" />
            </label>

            <label class="field">
              <span>Theme</span>
              <input v-model="createForm.theme" type="text" placeholder="HBM / advanced packaging" />
            </label>
          </div>

          <label class="field">
            <span>Why It Matters</span>
            <textarea
              v-model="createForm.whyItMatters"
              rows="3"
              placeholder="What structural dependency might the market be underestimating?"
            />
          </label>

          <label class="field">
            <span>Mispricing Hypothesis</span>
            <textarea
              v-model="createForm.mispricingHypothesis"
              rows="3"
              placeholder="Where should repricing show up if the thesis is correct?"
            />
          </label>

          <div class="field-grid">
            <label class="field">
              <span>Focus Areas</span>
              <input v-model="createForm.focusAreasText" type="text" placeholder="packaging, memory, ai infra" />
            </label>

            <label class="field">
              <span>Tags</span>
              <input v-model="createForm.tagsText" type="text" placeholder="ai, semis, bottlenecks" />
            </label>
          </div>

          <button class="primary-btn" @click="handleCreateProject" :disabled="savingCreate">
            {{ savingCreate ? 'Creating...' : 'Create Research Project' }}
          </button>
        </section>

        <section class="panel projects-panel">
          <div class="panel-header split">
            <span class="panel-kicker">02 / Research Projects</span>
            <span class="panel-meta">{{ projects.length }} total</span>
          </div>

          <div v-if="projectListLoading" class="empty-state compact">Loading projects...</div>

          <div v-else-if="projects.length === 0" class="empty-state compact">
            No research projects yet.
          </div>

          <div v-else class="project-list">
            <button
              v-for="project in projects"
              :key="project.research_project_id"
              class="project-list-item"
              :class="{ active: selectedProject?.research_project_id === project.research_project_id }"
              @click="openProject(project.research_project_id)"
            >
              <div class="item-top">
                <span class="item-name">{{ project.name }}</span>
                <span class="item-status">{{ project.status }}</span>
              </div>
              <div class="item-meta">
                <span>{{ project.claims_audit_count || 0 }} claims</span>
                <span>{{ project.scorecard_count || 0 }} scores</span>
              </div>
            </button>
          </div>
        </section>
      </aside>

      <section class="workspace">
        <div v-if="workspaceError" class="banner error">{{ workspaceError }}</div>
        <div v-if="workspaceNotice" class="banner success">{{ workspaceNotice }}</div>

        <section v-if="selectedProject" class="panel workspace-panel">
          <div class="workspace-header">
            <div>
              <div class="panel-kicker">Active Project</div>
              <h2>{{ selectedProject.name }}</h2>
              <p class="workspace-subtitle">
                {{ selectedProject.status }} · {{ selectedProject.ontology_name }}/{{ selectedProject.ontology_version }}
              </p>
            </div>

            <div class="workspace-actions">
              <div class="stat-box">
                <span class="stat-label">Claims</span>
                <span class="stat-value">{{ selectedProject.claims_audit_count || 0 }}</span>
              </div>
              <div class="stat-box">
                <span class="stat-label">Scorecards</span>
                <span class="stat-value">{{ selectedProject.scorecard_count || 0 }}</span>
              </div>
              <button class="danger-btn" @click="handleDeleteProject" :disabled="deletingProject">
                {{ deletingProject ? 'Deleting...' : 'Delete Project' }}
              </button>
            </div>
          </div>

          <div class="tab-bar">
            <button
              v-for="tab in tabs"
              :key="tab.key"
              class="tab-btn"
              :class="{ active: activeTab === tab.key }"
              @click="activeTab = tab.key"
            >
              {{ tab.label }}
            </button>
          </div>

          <div v-if="projectLoading" class="empty-state">Loading project artifacts...</div>

          <div v-else class="tab-content">
            <section v-if="activeTab === 'intake'" class="tab-panel">
              <div class="panel-header split">
                <span class="panel-kicker">Thesis Intake</span>
                <button class="primary-btn small" @click="handleSaveThesisIntake" :disabled="savingTab">
                  {{ savingTab ? 'Saving...' : 'Save Intake' }}
                </button>
              </div>

              <div class="field-grid">
                <label class="field">
                  <span>Theme</span>
                  <input v-model="thesisIntake.theme" type="text" />
                </label>
                <label class="field">
                  <span>Research Goal</span>
                  <input v-model="thesisIntake.researchGoal" type="text" />
                </label>
              </div>

              <label class="field">
                <span>Why This Matters</span>
                <textarea v-model="thesisIntake.whyItMatters" rows="4" />
              </label>

              <label class="field">
                <span>Mispricing Hypothesis</span>
                <textarea v-model="thesisIntake.mispricingHypothesis" rows="4" />
              </label>

              <label class="field">
                <span>Dependency Chain (one per line)</span>
                <textarea v-model="thesisIntake.dependencyChainText" rows="5" />
              </label>

              <label class="field">
                <span>Expression Candidates (one per line)</span>
                <textarea v-model="thesisIntake.expressionCandidatesText" rows="4" />
              </label>
            </section>

            <section v-else-if="activeTab === 'claims'" class="tab-panel">
              <div class="panel-header split">
                <span class="panel-kicker">Claims Audit</span>
                <div class="button-row">
                  <button class="ghost-btn" @click="addClaimRow">Add Row</button>
                  <button class="primary-btn small" @click="handleSaveClaimsAudit" :disabled="savingTab">
                    {{ savingTab ? 'Saving...' : 'Save Claims Audit' }}
                  </button>
                </div>
              </div>

              <div class="table-shell">
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>Claim</th>
                      <th>Status</th>
                      <th>Confidence</th>
                      <th>Source URL</th>
                      <th>Source Type</th>
                      <th>Notes</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, index) in claimsAuditRows" :key="`claim-${index}`">
                      <td><textarea v-model="row.claim_text" rows="2" /></td>
                      <td>
                        <select v-model="row.status">
                          <option value="supported">supported</option>
                          <option value="unverified">unverified</option>
                          <option value="unsupported">unsupported</option>
                        </select>
                      </td>
                      <td>
                        <select v-model="row.confidence">
                          <option value="high">high</option>
                          <option value="medium">medium</option>
                          <option value="low">low</option>
                        </select>
                      </td>
                      <td><textarea v-model="row.source_url" rows="2" /></td>
                      <td><input v-model="row.source_type" type="text" /></td>
                      <td><textarea v-model="row.notes" rows="2" /></td>
                      <td>
                        <button class="row-delete" @click="removeClaimRow(index)">×</button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>

            <section v-else-if="activeTab === 'scorecards'" class="tab-panel">
              <div class="panel-header split">
                <span class="panel-kicker">Scorecards</span>
                <div class="button-row">
                  <button class="ghost-btn" @click="addScorecardRow">Add Row</button>
                  <button class="primary-btn small" @click="handleSaveScorecards" :disabled="savingTab">
                    {{ savingTab ? 'Saving...' : 'Save Scorecards' }}
                  </button>
                </div>
              </div>

              <div class="table-shell">
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>Candidate</th>
                      <th>Severity</th>
                      <th>Severity Band</th>
                      <th>Value Capture</th>
                      <th>Value Band</th>
                      <th>Public Companies</th>
                      <th>Notes</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, index) in scorecardRows" :key="`score-${index}`">
                      <td><input v-model="row.candidate_name" type="text" /></td>
                      <td><input v-model="row.severity_score" type="number" step="0.1" min="0" max="100" /></td>
                      <td><input v-model="row.severity_band" type="text" /></td>
                      <td><input v-model="row.value_capture_score" type="number" step="0.1" min="0" max="100" /></td>
                      <td><input v-model="row.value_capture_band" type="text" /></td>
                      <td><textarea v-model="row.public_companies_text" rows="2" /></td>
                      <td><textarea v-model="row.notes" rows="2" /></td>
                      <td>
                        <button class="row-delete" @click="removeScorecardRow(index)">×</button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>

            <section v-else class="tab-panel">
              <div class="panel-header split">
                <span class="panel-kicker">Summary</span>
                <button class="primary-btn small" @click="handleSaveSummary" :disabled="savingTab">
                  {{ savingTab ? 'Saving...' : 'Save Summary' }}
                </button>
              </div>

              <div class="field-grid">
                <label class="field">
                  <span>Top Severity Layer</span>
                  <input v-model="summary.topSeverityLayer" type="text" />
                </label>
                <label class="field">
                  <span>Top Value-Capture Layer</span>
                  <input v-model="summary.topValueCaptureLayer" type="text" />
                </label>
              </div>

              <div class="field-grid">
                <label class="field">
                  <span>Thesis Status</span>
                  <input v-model="summary.thesisStatus" type="text" />
                </label>
                <label class="field">
                  <span>Next Action</span>
                  <input v-model="summary.nextAction" type="text" />
                </label>
              </div>

              <label class="field">
                <span>Key Takeaway</span>
                <textarea v-model="summary.keyTakeaway" rows="4" />
              </label>

              <label class="field">
                <span>Open Questions</span>
                <textarea v-model="summary.openQuestionsText" rows="4" />
              </label>
            </section>
          </div>
        </section>

        <section v-else class="panel empty-workspace">
          <div class="empty-state large">
            <h2>No Active Research Project</h2>
            <p>Create a new project or select one from the sidebar to start editing thesis intake, claims audit, scorecards, and summary artifacts.</p>
          </div>
        </section>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  createResearchProject,
  deleteResearchProject,
  getResearchOntology,
  getResearchProjectArtifacts,
  listResearchProjects,
  saveResearchClaimsAudit,
  saveResearchScorecards,
  saveResearchSummary,
  saveResearchThesisIntake
} from '../api/research'

const route = useRoute()
const router = useRouter()

const ontology = ref(null)
const projects = ref([])
const selectedProject = ref(null)
const projectListLoading = ref(false)
const projectLoading = ref(false)
const savingCreate = ref(false)
const savingTab = ref(false)
const deletingProject = ref(false)
const workspaceError = ref('')
const workspaceNotice = ref('')
const activeTab = ref('intake')

const tabs = [
  { key: 'intake', label: 'Thesis Intake' },
  { key: 'claims', label: 'Claims Audit' },
  { key: 'scorecards', label: 'Scorecards' },
  { key: 'summary', label: 'Summary' }
]

const createForm = reactive({
  name: '',
  theme: '',
  whyItMatters: '',
  mispricingHypothesis: '',
  focusAreasText: '',
  tagsText: ''
})

const thesisIntake = reactive(emptyThesisIntake())
const claimsAuditRows = ref([emptyClaimRow()])
const scorecardRows = ref([emptyScorecardRow()])
const summary = reactive(emptySummary())

const selectedProjectId = computed(() => route.params.researchProjectId || '')

function emptyThesisIntake() {
  return {
    theme: '',
    researchGoal: '',
    whyItMatters: '',
    mispricingHypothesis: '',
    dependencyChainText: '',
    expressionCandidatesText: ''
  }
}

function emptyClaimRow() {
  return {
    claim_text: '',
    status: 'unverified',
    confidence: 'medium',
    source_url: '',
    source_type: '',
    notes: ''
  }
}

function emptyScorecardRow() {
  return {
    candidate_name: '',
    severity_score: '',
    severity_band: '',
    value_capture_score: '',
    value_capture_band: '',
    public_companies_text: '',
    notes: ''
  }
}

function emptySummary() {
  return {
    topSeverityLayer: '',
    topValueCaptureLayer: '',
    thesisStatus: '',
    nextAction: '',
    keyTakeaway: '',
    openQuestionsText: ''
  }
}

function csvToArray(value) {
  return (value || '')
    .split(',')
    .map(item => item.trim())
    .filter(Boolean)
}

function linesToArray(value) {
  return (value || '')
    .split('\n')
    .map(item => item.trim())
    .filter(Boolean)
}

function arrayToLines(value) {
  return Array.isArray(value) ? value.join('\n') : ''
}

function resetWorkspaceNotice() {
  workspaceError.value = ''
  workspaceNotice.value = ''
}

async function loadOntology() {
  try {
    const res = await getResearchOntology()
    ontology.value = res.data
  } catch (error) {
    workspaceError.value = error.message || 'Failed to load research ontology.'
  }
}

async function refreshProjects() {
  projectListLoading.value = true
  try {
    const res = await listResearchProjects(100)
    projects.value = res.data || []
  } catch (error) {
    workspaceError.value = error.message || 'Failed to load research projects.'
  } finally {
    projectListLoading.value = false
  }
}

async function openProject(researchProjectId) {
  if (!researchProjectId) return
  if (selectedProjectId.value !== researchProjectId) {
    await router.push({ name: 'Research', params: { researchProjectId } })
    return
  }
  await loadProjectBundle(researchProjectId)
}

function hydrateThesisIntake(payload = {}) {
  Object.assign(thesisIntake, emptyThesisIntake(), {
    theme: payload.theme || payload.title || '',
    researchGoal: payload.research_goal || payload.market_signal || '',
    whyItMatters: payload.why_this_matters || '',
    mispricingHypothesis: payload.mispricing_hypothesis || '',
    dependencyChainText: arrayToLines(payload.dependency_chain),
    expressionCandidatesText: arrayToLines(payload.expression_candidates)
  })
}

function hydrateClaimsAudit(rows = []) {
  claimsAuditRows.value = rows.length
    ? rows.map(row => ({
        claim_text: row.claim_text || '',
        status: row.status || 'unverified',
        confidence: row.confidence || 'medium',
        source_url: row.source_url || '',
        source_type: row.source_type || row.source_class || '',
        notes: row.notes || ''
      }))
    : [emptyClaimRow()]
}

function hydrateScorecards(rows = []) {
  scorecardRows.value = rows.length
    ? rows.map(row => ({
        candidate_name: row.candidate_name || '',
        severity_score:
          row.severity_score ??
          row.severity?.score_0_to_100 ??
          '',
        severity_band: row.severity_band || row.severity?.band || '',
        value_capture_score:
          row.value_capture_score ??
          row.value_capture?.score_0_to_100 ??
          '',
        value_capture_band:
          row.value_capture_band || row.value_capture?.band || '',
        public_companies_text: Array.isArray(row.public_companies)
          ? row.public_companies.join(', ')
          : (row.public_companies_text || ''),
        notes: row.notes || ''
      }))
    : [emptyScorecardRow()]
}

function hydrateSummary(payload = {}) {
  Object.assign(summary, emptySummary(), {
    topSeverityLayer: payload.top_severity_layer || '',
    topValueCaptureLayer: payload.top_value_capture_layer || '',
    thesisStatus: payload.thesis_status || '',
    nextAction: payload.next_action || '',
    keyTakeaway: payload.key_takeaway || '',
    openQuestionsText: arrayToLines(payload.open_questions)
  })
}

async function loadProjectBundle(researchProjectId) {
  projectLoading.value = true
  resetWorkspaceNotice()
  try {
    const res = await getResearchProjectArtifacts(researchProjectId)
    const bundle = res.data
    selectedProject.value = bundle.research_project
    hydrateThesisIntake(bundle.thesis_intake)
    hydrateClaimsAudit(bundle.claims_audit)
    hydrateScorecards(bundle.scorecards)
    hydrateSummary(bundle.summary)
  } catch (error) {
    workspaceError.value = error.message || 'Failed to load project artifacts.'
    selectedProject.value = null
  } finally {
    projectLoading.value = false
  }
}

async function handleCreateProject() {
  if (!createForm.name.trim()) {
    workspaceError.value = 'Project name is required.'
    return
  }

  savingCreate.value = true
  resetWorkspaceNotice()
  try {
    const payload = {
      name: createForm.name.trim(),
      tags: csvToArray(createForm.tagsText),
      focus_areas: csvToArray(createForm.focusAreasText),
      thesis_intake: {
        theme: createForm.theme.trim(),
        why_this_matters: createForm.whyItMatters.trim(),
        mispricing_hypothesis: createForm.mispricingHypothesis.trim()
      }
    }

    const res = await createResearchProject(payload)
    createForm.name = ''
    createForm.theme = ''
    createForm.whyItMatters = ''
    createForm.mispricingHypothesis = ''
    createForm.focusAreasText = ''
    createForm.tagsText = ''

    await refreshProjects()
    workspaceNotice.value = 'Research project created.'
    await router.push({
      name: 'Research',
      params: { researchProjectId: res.data.research_project_id }
    })
  } catch (error) {
    workspaceError.value = error.message || 'Failed to create research project.'
  } finally {
    savingCreate.value = false
  }
}

async function handleSaveThesisIntake() {
  if (!selectedProject.value) return

  savingTab.value = true
  resetWorkspaceNotice()
  try {
    await saveResearchThesisIntake(selectedProject.value.research_project_id, {
      theme: thesisIntake.theme.trim(),
      research_goal: thesisIntake.researchGoal.trim(),
      why_this_matters: thesisIntake.whyItMatters.trim(),
      mispricing_hypothesis: thesisIntake.mispricingHypothesis.trim(),
      dependency_chain: linesToArray(thesisIntake.dependencyChainText),
      expression_candidates: linesToArray(thesisIntake.expressionCandidatesText)
    })
    await refreshProjects()
    await loadProjectBundle(selectedProject.value.research_project_id)
    workspaceNotice.value = 'Thesis intake saved.'
  } catch (error) {
    workspaceError.value = error.message || 'Failed to save thesis intake.'
  } finally {
    savingTab.value = false
  }
}

function addClaimRow() {
  claimsAuditRows.value.push(emptyClaimRow())
}

function removeClaimRow(index) {
  claimsAuditRows.value.splice(index, 1)
  if (claimsAuditRows.value.length === 0) {
    claimsAuditRows.value.push(emptyClaimRow())
  }
}

async function handleSaveClaimsAudit() {
  if (!selectedProject.value) return

  savingTab.value = true
  resetWorkspaceNotice()
  try {
    const cleanedRows = claimsAuditRows.value
      .map(row => ({
        claim_text: row.claim_text.trim(),
        status: row.status,
        confidence: row.confidence,
        source_url: row.source_url.trim(),
        source_type: row.source_type.trim(),
        notes: row.notes.trim()
      }))
      .filter(row => Object.values(row).some(value => value))

    await saveResearchClaimsAudit(selectedProject.value.research_project_id, cleanedRows)
    await refreshProjects()
    await loadProjectBundle(selectedProject.value.research_project_id)
    workspaceNotice.value = 'Claims audit saved.'
  } catch (error) {
    workspaceError.value = error.message || 'Failed to save claims audit.'
  } finally {
    savingTab.value = false
  }
}

function addScorecardRow() {
  scorecardRows.value.push(emptyScorecardRow())
}

function removeScorecardRow(index) {
  scorecardRows.value.splice(index, 1)
  if (scorecardRows.value.length === 0) {
    scorecardRows.value.push(emptyScorecardRow())
  }
}

async function handleSaveScorecards() {
  if (!selectedProject.value) return

  savingTab.value = true
  resetWorkspaceNotice()
  try {
    const cleanedRows = scorecardRows.value
      .map(row => ({
        candidate_name: row.candidate_name.trim(),
        severity_score: row.severity_score === '' ? null : Number(row.severity_score),
        severity_band: row.severity_band.trim(),
        value_capture_score:
          row.value_capture_score === '' ? null : Number(row.value_capture_score),
        value_capture_band: row.value_capture_band.trim(),
        public_companies: csvToArray(row.public_companies_text),
        notes: row.notes.trim()
      }))
      .filter(row => row.candidate_name || row.notes || row.public_companies.length)

    await saveResearchScorecards(selectedProject.value.research_project_id, cleanedRows)
    await refreshProjects()
    await loadProjectBundle(selectedProject.value.research_project_id)
    workspaceNotice.value = 'Scorecards saved.'
  } catch (error) {
    workspaceError.value = error.message || 'Failed to save scorecards.'
  } finally {
    savingTab.value = false
  }
}

async function handleSaveSummary() {
  if (!selectedProject.value) return

  savingTab.value = true
  resetWorkspaceNotice()
  try {
    await saveResearchSummary(selectedProject.value.research_project_id, {
      top_severity_layer: summary.topSeverityLayer.trim(),
      top_value_capture_layer: summary.topValueCaptureLayer.trim(),
      thesis_status: summary.thesisStatus.trim(),
      next_action: summary.nextAction.trim(),
      key_takeaway: summary.keyTakeaway.trim(),
      open_questions: linesToArray(summary.openQuestionsText)
    })
    await refreshProjects()
    await loadProjectBundle(selectedProject.value.research_project_id)
    workspaceNotice.value = 'Summary saved.'
  } catch (error) {
    workspaceError.value = error.message || 'Failed to save summary.'
  } finally {
    savingTab.value = false
  }
}

async function handleDeleteProject() {
  if (!selectedProject.value) return

  deletingProject.value = true
  resetWorkspaceNotice()
  try {
    const currentId = selectedProject.value.research_project_id
    await deleteResearchProject(currentId)
    selectedProject.value = null
    hydrateThesisIntake({})
    hydrateClaimsAudit([])
    hydrateScorecards([])
    hydrateSummary({})
    await refreshProjects()
    workspaceNotice.value = 'Research project deleted.'
    await router.push({ name: 'Research' })
  } catch (error) {
    workspaceError.value = error.message || 'Failed to delete research project.'
  } finally {
    deletingProject.value = false
  }
}

watch(
  () => selectedProjectId.value,
  async (researchProjectId) => {
    if (researchProjectId) {
      await loadProjectBundle(researchProjectId)
    } else {
      selectedProject.value = null
      hydrateThesisIntake({})
      hydrateClaimsAudit([])
      hydrateScorecards([])
      hydrateSummary({})
    }
  },
  { immediate: true }
)

onMounted(async () => {
  await Promise.all([loadOntology(), refreshProjects()])
})
</script>

<style scoped>
.research-view {
  min-height: 100vh;
  background:
    radial-gradient(circle at top right, rgba(255, 69, 0, 0.08), transparent 28%),
    linear-gradient(180deg, #ffffff 0%, #f7f4ef 100%);
  color: #111111;
}

.research-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 28px 36px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(12px);
  position: sticky;
  top: 0;
  z-index: 5;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 18px;
}

.brand-btn {
  border: none;
  background: #111111;
  color: #ffffff;
  padding: 12px 16px;
  font-weight: 800;
  letter-spacing: 0.12em;
  cursor: pointer;
}

.eyebrow {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  color: #d94b11;
  margin-bottom: 4px;
}

.header-copy h1 {
  font-size: 1.9rem;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ontology-chip {
  border: 1px solid rgba(0, 0, 0, 0.12);
  padding: 10px 14px;
  background: #fff8f4;
  font-size: 0.85rem;
}

.research-layout {
  display: grid;
  grid-template-columns: 360px minmax(0, 1fr);
  gap: 24px;
  padding: 24px 36px 40px;
}

.sidebar,
.workspace {
  min-width: 0;
}

.panel {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 18px 50px rgba(0, 0, 0, 0.05);
}

.create-panel,
.projects-panel,
.workspace-panel,
.empty-workspace {
  padding: 20px;
}

.sidebar {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.panel-header {
  margin-bottom: 16px;
}

.panel-header.split,
.workspace-header,
.button-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.panel-kicker,
.panel-meta,
.workspace-subtitle {
  font-size: 0.78rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: #7d746b;
}

.workspace-header {
  align-items: flex-start;
  margin-bottom: 18px;
}

.workspace-header h2 {
  font-size: 1.8rem;
  margin: 4px 0 6px;
}

.workspace-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.stat-box {
  min-width: 88px;
  padding: 10px 12px;
  background: #f6f0e8;
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.stat-label {
  display: block;
  font-size: 0.72rem;
  text-transform: uppercase;
  color: #6f655b;
  margin-bottom: 4px;
}

.stat-value {
  font-size: 1.15rem;
  font-weight: 700;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 14px;
}

.field span {
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #6f655b;
}

.field input,
.field textarea,
.data-table input,
.data-table textarea,
.data-table select {
  width: 100%;
  border: 1px solid rgba(0, 0, 0, 0.12);
  background: #fffdf9;
  padding: 12px;
  font: inherit;
  color: inherit;
  outline: none;
}

.field input:focus,
.field textarea:focus,
.data-table input:focus,
.data-table textarea:focus,
.data-table select:focus {
  border-color: #d94b11;
}

.primary-btn,
.ghost-btn,
.danger-btn,
.tab-btn,
.project-list-item,
.row-delete {
  font: inherit;
}

.primary-btn,
.ghost-btn,
.danger-btn {
  border: 1px solid transparent;
  padding: 12px 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.primary-btn {
  background: #111111;
  color: #ffffff;
}

.primary-btn.small {
  padding: 10px 12px;
  font-size: 0.9rem;
}

.primary-btn:hover:not(:disabled) {
  background: #d94b11;
}

.ghost-btn {
  background: #ffffff;
  border-color: rgba(0, 0, 0, 0.12);
}

.ghost-btn:hover:not(:disabled) {
  border-color: #d94b11;
  color: #d94b11;
}

.danger-btn {
  background: #fff5f1;
  border-color: rgba(217, 75, 17, 0.2);
  color: #b33a0d;
}

.danger-btn:hover:not(:disabled) {
  background: #ffe7de;
}

.primary-btn:disabled,
.ghost-btn:disabled,
.danger-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.project-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 48vh;
  overflow: auto;
}

.project-list-item {
  display: block;
  width: 100%;
  text-align: left;
  padding: 14px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: #fffdf9;
  cursor: pointer;
}

.project-list-item.active {
  border-color: #d94b11;
  background: #fff3ec;
}

.item-top,
.item-meta {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.item-name {
  font-weight: 600;
}

.item-status,
.item-meta {
  font-size: 0.82rem;
  color: #7a7269;
}

.tab-bar {
  display: flex;
  gap: 10px;
  margin-bottom: 18px;
  overflow-x: auto;
}

.tab-btn {
  white-space: nowrap;
  border: 1px solid rgba(0, 0, 0, 0.1);
  background: #fcfaf6;
  padding: 10px 14px;
  cursor: pointer;
}

.tab-btn.active {
  background: #111111;
  border-color: #111111;
  color: #ffffff;
}

.table-shell {
  overflow-x: auto;
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 920px;
}

.data-table th,
.data-table td {
  padding: 10px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  vertical-align: top;
}

.data-table th {
  background: #f6f0e8;
  text-align: left;
  font-size: 0.76rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #6f655b;
}

.row-delete {
  width: 32px;
  height: 32px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  background: #ffffff;
  cursor: pointer;
}

.row-delete:hover {
  border-color: #d94b11;
  color: #d94b11;
}

.banner {
  padding: 14px 16px;
  margin-bottom: 14px;
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.banner.error {
  background: #fff0ec;
  color: #9c2c02;
}

.banner.success {
  background: #f1f8f2;
  color: #255b2c;
}

.empty-state {
  display: grid;
  place-items: center;
  min-height: 240px;
  text-align: center;
  color: #6f655b;
}

.empty-state.compact {
  min-height: 90px;
}

.empty-state.large h2 {
  font-size: 1.8rem;
  margin-bottom: 12px;
}

@media (max-width: 1100px) {
  .research-layout {
    grid-template-columns: 1fr;
  }

  .workspace-actions,
  .field-grid {
    grid-template-columns: 1fr;
    display: grid;
  }
}

@media (max-width: 720px) {
  .research-header,
  .research-layout {
    padding-left: 18px;
    padding-right: 18px;
  }

  .research-header,
  .header-left,
  .header-right,
  .workspace-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
