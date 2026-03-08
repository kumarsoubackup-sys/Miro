import { describe, it, expect, beforeEach } from 'vitest'
import { 
  setPendingUpload, 
  getPendingUpload, 
  clearPendingUpload,
  default as state 
} from '../pendingUpload'

describe('PendingUpload Store', () => {
  beforeEach(() => {
    // 重置状态
    clearPendingUpload()
  })

  describe('setPendingUpload', () => {
    it('should set files and requirement', () => {
      const files = [new File(['content'], 'test.txt')]
      const requirement = 'Test requirement'
      
      setPendingUpload(files, requirement)
      
      expect(state.files).toEqual(files)
      expect(state.simulationRequirement).toBe(requirement)
      expect(state.isPending).toBe(true)
    })

    it('should handle empty files array', () => {
      setPendingUpload([], 'requirement')
      
      expect(state.files).toEqual([])
      expect(state.isPending).toBe(true)
    })

    it('should handle empty requirement', () => {
      const files = [new File(['content'], 'test.txt')]
      
      setPendingUpload(files, '')
      
      expect(state.simulationRequirement).toBe('')
      expect(state.isPending).toBe(true)
    })

    it('should handle multiple files', () => {
      const files = [
        new File(['content1'], 'file1.txt'),
        new File(['content2'], 'file2.txt'),
        new File(['content3'], 'file3.txt')
      ]
      
      setPendingUpload(files, 'Multi-file requirement')
      
      expect(state.files).toHaveLength(3)
      expect(state.isPending).toBe(true)
    })
  })

  describe('getPendingUpload', () => {
    it('should return current state', () => {
      const files = [new File(['content'], 'test.txt')]
      const requirement = 'Test requirement'
      
      setPendingUpload(files, requirement)
      const result = getPendingUpload()
      
      expect(result.files).toEqual(files)
      expect(result.simulationRequirement).toBe(requirement)
      expect(result.isPending).toBe(true)
    })

    it('should return default state when nothing set', () => {
      const result = getPendingUpload()
      
      expect(result.files).toEqual([])
      expect(result.simulationRequirement).toBe('')
      expect(result.isPending).toBe(false)
    })

    it('should return independent copy', () => {
      setPendingUpload([new File(['content'], 'test.txt')], 'requirement')
      const result1 = getPendingUpload()
      
      clearPendingUpload()
      const result2 = getPendingUpload()
      
      expect(result1.isPending).toBe(true)
      expect(result2.isPending).toBe(false)
    })
  })

  describe('clearPendingUpload', () => {
    it('should reset all state values', () => {
      setPendingUpload([new File(['content'], 'test.txt')], 'requirement')
      
      clearPendingUpload()
      
      expect(state.files).toEqual([])
      expect(state.simulationRequirement).toBe('')
      expect(state.isPending).toBe(false)
    })

    it('should work when called multiple times', () => {
      clearPendingUpload()
      clearPendingUpload()
      clearPendingUpload()
      
      expect(state.files).toEqual([])
      expect(state.simulationRequirement).toBe('')
      expect(state.isPending).toBe(false)
    })
  })

  describe('state reactivity', () => {
    it('should maintain state across function calls', () => {
      const files = [new File(['content'], 'test.txt')]
      
      setPendingUpload(files, 'requirement')
      
      // 多次获取应该返回相同状态
      const result1 = getPendingUpload()
      const result2 = getPendingUpload()
      
      expect(result1.files).toEqual(result2.files)
      expect(result1.simulationRequirement).toBe(result2.simulationRequirement)
    })

    it('should update existing state instead of creating new', () => {
      setPendingUpload([new File(['content1'], 'file1.txt')], 'first')
      
      const files2 = [new File(['content2'], 'file2.txt')]
      setPendingUpload(files2, 'second')
      
      expect(state.files).toEqual(files2)
      expect(state.simulationRequirement).toBe('second')
      expect(state.isPending).toBe(true)
    })
  })
})
