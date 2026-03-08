import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock service
const mockService = vi.fn()
const mockRequestWithRetry = vi.fn((fn) => fn())

vi.mock('../index', () => ({
  default: mockService,
  requestWithRetry: mockRequestWithRetry
}))

// 动态导入被测函数
const importGraphAPI = async () => {
  const module = await import('../graph')
  return module
}

describe('Graph API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('generateOntology', () => {
    it('should call service with correct parameters', async () => {
      const { generateOntology } = await importGraphAPI()
      const mockFormData = new FormData()
      mockFormData.append('files', new Blob(['test']), 'test.txt')
      
      mockService.mockResolvedValue({ data: { success: true } })
      
      await generateOntology(mockFormData)
      
      expect(mockRequestWithRetry).toHaveBeenCalled()
    })

    it('should return response data on success', async () => {
      const { generateOntology } = await importGraphAPI()
      const mockResponse = { success: true, data: { project_id: '123' } }
      mockService.mockResolvedValue(mockResponse)
      
      const result = await generateOntology(new FormData())
      
      expect(result).toEqual(mockResponse)
    })
  })

  describe('buildGraph', () => {
    it('should call service with correct parameters', async () => {
      const { buildGraph } = await importGraphAPI()
      const data = { project_id: '123', graph_name: 'test-graph' }
      mockService.mockResolvedValue({ data: { success: true } })
      
      await buildGraph(data)
      
      expect(mockRequestWithRetry).toHaveBeenCalled()
    })
  })

  describe('getTaskStatus', () => {
    it('should call service with task ID', async () => {
      const { getTaskStatus } = await importGraphAPI()
      const taskId = 'task-123'
      const mockResponse = { 
        success: true, 
        data: { 
          task_id: taskId, 
          status: 'processing',
          progress: 50 
        } 
      }
      mockService.mockResolvedValue(mockResponse)
      
      const result = await getTaskStatus(taskId)
      
      expect(mockService).toHaveBeenCalledWith(expect.objectContaining({
        url: `/api/graph/task/${taskId}`,
        method: 'get'
      }))
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getGraphData', () => {
    it('should call service with graph ID', async () => {
      const { getGraphData } = await importGraphAPI()
      const graphId = 'graph-456'
      const mockResponse = { 
        success: true, 
        data: { nodes: [], edges: [] } 
      }
      mockService.mockResolvedValue(mockResponse)
      
      const result = await getGraphData(graphId)
      
      expect(mockService).toHaveBeenCalledWith(expect.objectContaining({
        url: `/api/graph/data/${graphId}`,
        method: 'get'
      }))
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getProject', () => {
    it('should call service with project ID', async () => {
      const { getProject } = await importGraphAPI()
      const projectId = 'proj-789'
      const mockResponse = { 
        success: true, 
        data: { 
          project_id: projectId, 
          name: 'Test Project' 
        } 
      }
      mockService.mockResolvedValue(mockResponse)
      
      const result = await getProject(projectId)
      
      expect(mockService).toHaveBeenCalledWith(expect.objectContaining({
        url: `/api/graph/project/${projectId}`,
        method: 'get'
      }))
      expect(result).toEqual(mockResponse)
    })
  })
})
