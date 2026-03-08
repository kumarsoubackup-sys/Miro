import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// 测试 requestWithRetry 函数
describe('requestWithRetry', () => {
  let requestWithRetry

  beforeEach(async () => {
    vi.resetModules()
    const module = await import('../index')
    requestWithRetry = module.requestWithRetry
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should return result on successful request', async () => {
    const mockRequest = vi.fn().mockResolvedValue({ data: 'success' })
    
    const result = await requestWithRetry(mockRequest, 3, 10)
    
    expect(result).toEqual({ data: 'success' })
    expect(mockRequest).toHaveBeenCalledTimes(1)
  })

  it('should retry on failure and eventually succeed', async () => {
    const mockRequest = vi.fn()
      .mockRejectedValueOnce(new Error('Network error'))
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValue({ data: 'success' })
    
    const result = await requestWithRetry(mockRequest, 3, 10)
    
    expect(result).toEqual({ data: 'success' })
    expect(mockRequest).toHaveBeenCalledTimes(3)
  })

  it('should throw error after max retries', async () => {
    const mockRequest = vi.fn().mockRejectedValue(new Error('Persistent error'))
    
    await expect(requestWithRetry(mockRequest, 2, 10)).rejects.toThrow('Persistent error')
    expect(mockRequest).toHaveBeenCalledTimes(2)  // 初始 + 1次重试
  })

  it('should use exponential backoff', async () => {
    const mockRequest = vi.fn()
      .mockRejectedValueOnce(new Error('Error 1'))
      .mockRejectedValueOnce(new Error('Error 2'))
      .mockResolvedValue({ data: 'success' })
    
    const startTime = Date.now()
    await requestWithRetry(mockRequest, 3, 50)
    const elapsed = Date.now() - startTime
    
    // 第一次重试等待 50ms，第二次等待 100ms
    expect(elapsed).toBeGreaterThanOrEqual(140)
    expect(mockRequest).toHaveBeenCalledTimes(3)
  })
})
