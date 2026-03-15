import service, { requestWithRetry } from './index'

export const getResearchOntology = () => {
  return service.get('/api/research/ontology')
}

export const createResearchProject = (data) => {
  return requestWithRetry(() => service.post('/api/research/project', data), 3, 1000)
}

export const listResearchProjects = (limit = 50) => {
  return service.get('/api/research/project/list', { params: { limit } })
}

export const getResearchProject = (researchProjectId) => {
  return service.get(`/api/research/project/${researchProjectId}`)
}

export const deleteResearchProject = (researchProjectId) => {
  return service.delete(`/api/research/project/${researchProjectId}`)
}

export const getResearchProjectArtifacts = (researchProjectId) => {
  return service.get(`/api/research/project/${researchProjectId}/artifacts`)
}

export const saveResearchThesisIntake = (researchProjectId, data) => {
  return requestWithRetry(
    () => service.post(`/api/research/project/${researchProjectId}/thesis-intake`, data),
    3,
    1000
  )
}

export const saveResearchClaimsAudit = (researchProjectId, rows) => {
  return requestWithRetry(
    () => service.post(`/api/research/project/${researchProjectId}/claims-audit`, { rows }),
    3,
    1000
  )
}

export const saveResearchScorecards = (researchProjectId, rows) => {
  return requestWithRetry(
    () => service.post(`/api/research/project/${researchProjectId}/scorecards`, { rows }),
    3,
    1000
  )
}

export const saveResearchSummary = (researchProjectId, data) => {
  return requestWithRetry(
    () => service.post(`/api/research/project/${researchProjectId}/summary`, data),
    3,
    1000
  )
}
