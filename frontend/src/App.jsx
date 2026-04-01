import { useState, useEffect, useRef } from 'react'
import axios from 'axios'

// 支持环境变量配置 API 地址
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8002'

// 莫兰迪粉彩配色
const colors = {
  bg: '#F8F9FA',
  cardBg: '#FFFFFF',
  blue: { light: '#E3F2FD', dark: '#1565C0' },
  green: { light: '#E8F5E9', dark: '#2E7D32' },
  orange: { light: '#FFF3E0', dark: '#E65100' },
  red: { light: '#FFEBEE', dark: '#C62828' },
  purple: { light: '#F3E5F5', dark: '#6A1B9A' },
  cyan: { light: '#E0F7FA', dark: '#006064' },
  text: { primary: '#212121', secondary: '#424242', tertiary: '#757575' },
  border: '#E0E0E0'
}

// Agent 流程配置
const workflowSteps = [
  { name: '调研', key: 'research', icon: '🔍', color: colors.blue },
  { name: '创作', key: 'creator', icon: '✍️', color: colors.green },
  { name: '审核', key: 'reviewer', icon: '📋', color: colors.purple },
  { name: '优化', key: 'optimizer', icon: '✨', color: colors.cyan },
  { name: '配图', key: 'image', icon: '🎨', color: colors.orange }
]

function App() {
  // 表单状态
  const [formData, setFormData] = useState({
    topic: '',
    audience: '',
    platform: 'xiaohongshu',
    tone: 'casual',
    priority: 'standard',
    emotion: 'hopeful',
    style: 'minimalist',
    brand_keywords: ''
  })

  // 图片相关状态
  const [selectedImage, setSelectedImage] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const [imagePath, setImagePath] = useState(null)
  const [isUploading, setIsUploading] = useState(false)

  // 任务状态
  const [taskId, setTaskId] = useState(null)
  const [taskStatus, setTaskStatus] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [copied, setCopied] = useState(false)
  const [activeTab, setActiveTab] = useState('content')

  // 版本历史状态
  const [showVersionHistory, setShowVersionHistory] = useState(false)
  const [versionHistory, setVersionHistory] = useState([])
  const [currentVersionIndex, setCurrentVersionIndex] = useState(null)

  // 阶段确认状态
  const [awaitingConfirmation, setAwaitingConfirmation] = useState(false)
  const [currentStepResult, setCurrentStepResult] = useState(null)
  const [expandedSections, setExpandedSections] = useState({})

  // 修改意见状态
  const [modificationInput, setModificationInput] = useState('')
  const [isModifying, setIsModifying] = useState(false)
  const [modifySuccess, setModifySuccess] = useState(false)

  // 历史记录状态
  const [showHistory, setShowHistory] = useState(false)
  const [history, setHistory] = useState([])

  // WebSocket 引用
  const wsRef = useRef(null)
  const pollTimerRef = useRef(null)

  // 处理输入变化
  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  // 处理图片选择
  const handleImageSelect = (e) => {
    const file = e.target.files[0]
    if (file) {
      setSelectedImage(file)
      setImagePreview(URL.createObjectURL(file))
    }
  }

  // 上传图片
  const uploadImage = async () => {
    if (!selectedImage) return null

    setIsUploading(true)
    try {
      const formDataImg = new FormData()
      formDataImg.append('file', selectedImage)

      const response = await axios.post(`${API_BASE}/api/upload-image`, formDataImg)

      setImagePath(response.data.filepath)
      return response.data.filepath
    } catch (err) {
      console.error('图片上传失败:', err)
      console.error('错误详情:', err.response?.data)
      setError('图片上传失败：' + (err.response?.data?.detail || err.message))
      return null
    } finally {
      setIsUploading(false)
    }
  }

  // 移除图片
  const handleRemoveImage = () => {
    setSelectedImage(null)
    setImagePreview(null)
    setImagePath(null)
  }

  // 提交表单 - 启动工作流
  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsSubmitting(true)
    setError(null)
    setResult(null)
    setTaskStatus(null)
    setAwaitingConfirmation(false)
    setActiveTab('content')

    // 先上传图片（如果有）
    let uploadedImagePath = null
    if (selectedImage) {
      uploadedImagePath = await uploadImage()
      if (!uploadedImagePath) {
        setIsSubmitting(false)
        return
      }
    }

    try {
      const response = await axios.post(`${API_BASE}/api/generate`, {
        ...formData,
        brand_keywords: formData.brand_keywords.split(',').map(k => k.trim()).filter(Boolean),
        product_image_path: uploadedImagePath
      })

      const { task_id } = response.data
      setTaskId(task_id)

      // 连接 WebSocket
      connectWebSocket(task_id)
      // 轮询任务状态
      pollTaskStatus(task_id)

    } catch (err) {
      setError(err.response?.data?.detail || '提交失败，请重试')
      setIsSubmitting(false)
    }
  }

  // 连接 WebSocket
  const connectWebSocket = (id) => {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsHost = import.meta.env.VITE_WS_BASE || API_BASE.replace(/^http/, 'ws').replace(':8002', ':8002')
    const ws = new WebSocket(`${wsHost}/ws/task/${id}`)

    ws.onopen = () => console.log('WebSocket 已连接')
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)

      // 处理确认请求
      if (data.type === 'confirmation_required') {
        setAwaitingConfirmation(true)
        setCurrentStepResult(data.result)
        setTaskStatus(prev => ({
          ...prev,
          ...data,
          awaiting_confirmation: true
        }))
      } else {
        setTaskStatus(data)
        if (data.status === 'completed') {
          setResult(data.result)
          setIsSubmitting(false)
          setAwaitingConfirmation(false)
          if (pollTimerRef.current) clearTimeout(pollTimerRef.current)
        } else if (data.status === 'failed') {
          setError(data.current_step)
          setIsSubmitting(false)
          setAwaitingConfirmation(false)
        }
      }
    }
    ws.onerror = (error) => console.error('WebSocket 错误:', error)
    ws.onclose = () => console.log('WebSocket 已关闭')
    wsRef.current = ws
  }

  // 轮询任务状态
  const pollTaskStatus = async (id) => {
    const poll = async () => {
      try {
        const response = await axios.get(`${API_BASE}/api/task/${id}`)
        const status = response.data

        setTaskStatus(status)

        // 检查是否需要确认
        if (status.awaiting_confirmation) {
          setAwaitingConfirmation(true)
          setCurrentStepResult(status.current_step_result)
          setIsSubmitting(false)
          if (pollTimerRef.current) clearTimeout(pollTimerRef.current)
          return
        }

        if (status.status === 'completed') {
          setResult(status.result)
          setIsSubmitting(false)
          setAwaitingConfirmation(false)
          if (pollTimerRef.current) clearTimeout(pollTimerRef.current)

          // 保存到 localStorage
          saveToLocalStorage(id, status.result)
        } else if (status.status === 'failed') {
          setError(status.current_step)
          setIsSubmitting(false)
          setAwaitingConfirmation(false)
          if (pollTimerRef.current) clearTimeout(pollTimerRef.current)
        } else {
          pollTimerRef.current = setTimeout(poll, 2000)
        }
      } catch (err) {
        console.error('轮询失败:', err)
        setIsSubmitting(false)
      }
    }
    poll()
  }

  // 保存到 localStorage（本地备份）
  const saveToLocalStorage = (id, resultData) => {
    try {
      const history = JSON.parse(localStorage.getItem('contentGenHistory') || '[]')

      const newEntry = {
        task_id: id,
        created_at: new Date().toISOString(),
        topic: formData.topic,
        result: resultData
      }

      // 添加到历史记录（保留最近 20 条）
      const updatedHistory = [newEntry, ...history].slice(0, 20)
      localStorage.setItem('contentGenHistory', JSON.stringify(updatedHistory))
      console.log('本地备份已保存')
    } catch (err) {
      console.error('保存到 localStorage 失败:', err)
    }
  }

  // 从 API 加载历史记录
  const loadHistoryFromAPI = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/results?limit=20`)
      return response.data.results || []
    } catch (err) {
      console.error('加载历史记录失败:', err)
      return []
    }
  }

  // 加载历史记录（兼容本地和 API）
  const loadHistory = async () => {
    // 优先从 API 加载
    const apiHistory = await loadHistoryFromAPI()
    if (apiHistory.length > 0) {
      return apiHistory
    }
    // 回退到 localStorage
    try {
      return JSON.parse(localStorage.getItem('contentGenHistory') || '[]')
    } catch (err) {
      console.error('加载本地历史记录失败:', err)
      return []
    }
  }

  // 从历史记录加载
  const loadFromHistory = async (selectedTaskId) => {
    // 从 API 获取完整结果
    try {
      const response = await axios.get(`${API_BASE}/api/results/${selectedTaskId}`)
      const result = response.data

      // 重置状态
      setTaskId(selectedTaskId)
      setResult(result.final_output)
      setTaskStatus({
        steps: [
          { name: '调研', status: 'completed', result: result.step_results?.调研 || result.step_results?.research },
          { name: '创作', status: 'completed', result: result.step_results?.创作 || result.step_results?.creator },
          { name: '审核', status: 'completed', result: result.step_results?.审核 || result.step_results?.reviewer },
          { name: '优化', status: 'completed', result: result.step_results?.优化 || result.step_results?.optimizer },
          { name: '配图', status: 'completed', result: result.step_results?.配图 || result.step_results?.image }
        ],
        status: 'completed',
        progress: 100
      })

      // 恢复表单配置
      if (result.config) {
        setFormData(prev => ({
          ...prev,
          topic: result.config.topic || '',
          audience: result.config.audience || '',
          platform: result.config.platform || 'xiaohongshu',
          tone: result.config.tone || 'casual',
          emotion: result.config.emotion || 'hopeful',
          style: result.config.style || 'minimalist',
          brand_keywords: result.config.brand_keywords?.join(', ') || ''
        }))
      }

      setActiveTab('content')
      setAwaitingConfirmation(false)

      // 初始化展开状态
      initExpandedSections('调研')
    } catch (err) {
      console.error('加载历史记录失败:', err)
      // 回退到 localStorage
      const history = JSON.parse(localStorage.getItem('contentGenHistory') || '[]')
      const entry = history.find(h => h.task_id === selectedTaskId)
      if (entry) {
        setTaskId(entry.task_id)
        setResult(entry.result)
        setFormData(prev => ({ ...prev, topic: entry.topic || '' }))
        setActiveTab('content')
      }
    }
  }

  // 删除历史记录
  const deleteHistoryEntry = async (taskId) => {
    try {
      // 删除 API 结果
      await axios.delete(`${API_BASE}/api/results/${taskId}`)
      // 重新渲染
      setHistory(await loadHistoryFromAPI())
    } catch (err) {
      console.error('删除历史记录失败:', err)
      // 回退到 localStorage
      const history = JSON.parse(localStorage.getItem('contentGenHistory') || '[]')
      const updatedHistory = history.filter(h => h.task_id !== taskId)
      localStorage.setItem('contentGenHistory', JSON.stringify(updatedHistory))
      setHistory(updatedHistory)
    }
  }

  // 加载版本历史
  const loadVersionHistory = async (taskId) => {
    try {
      const response = await axios.get(`${API_BASE}/api/conversations/${taskId}/versions`)
      return response.data.versions || []
    } catch (err) {
      console.error('加载版本历史失败:', err)
      return []
    }
  }

  // 获取指定版本
  const getVersion = async (taskId, versionIndex) => {
    try {
      const response = await axios.get(`${API_BASE}/api/conversations/${taskId}/version/${versionIndex}`)
      return response.data
    } catch (err) {
      console.error('获取版本失败:', err)
      return null
    }
  }

  // 恢复到指定版本
  const restoreVersion = async (taskId, versionIndex) => {
    try {
      await axios.post(`${API_BASE}/api/conversations/${taskId}/restore?version_index=${versionIndex}`)
      // 加载恢复后的版本
      const version = await getVersion(taskId, versionIndex)
      if (version) {
        setResult(version.result?.final_output)
        setCurrentVersionIndex(versionIndex)
      }
    } catch (err) {
      console.error('恢复版本失败:', err)
    }
  }

  // 显示版本历史
  const handleShowVersionHistory = async () => {
    if (!taskId) return

    const versions = await loadVersionHistory(taskId)
    setVersionHistory(versions)
    setShowVersionHistory(true)

    // 获取当前版本索引
    try {
      const historyResponse = await axios.get(`${API_BASE}/api/conversations/${taskId}`)
      setCurrentVersionIndex(historyResponse.data.current_version)
    } catch (err) {
      setCurrentVersionIndex(versions.length > 0 ? versions.length - 1 : null)
    }
  }

  // 确认继续下一步
  const handleContinue = async () => {
    if (!taskId) return

    try {
      setAwaitingConfirmation(false)
      setIsSubmitting(true)

      await axios.post(`${API_BASE}/api/task/${taskId}/confirm`, {
        action: 'continue'
      })

      // 继续轮询
      pollTaskStatus(taskId)
    } catch (err) {
      console.error('确认继续失败:', err)
      setError('操作失败，请重试')
      setIsSubmitting(false)
    }
  }

  // 停止工作流
  const handleStop = async () => {
    if (!taskId) return

    try {
      await axios.post(`${API_BASE}/api/task/${taskId}/confirm`, {
        action: 'stop'
      })

      setTaskStatus(prev => ({ ...prev, status: 'cancelled' }))
      setAwaitingConfirmation(false)
      setIsSubmitting(false)
      if (pollTimerRef.current) clearTimeout(pollTimerRef.current)
    } catch (err) {
      console.error('停止失败:', err)
    }
  }

  // 一键复制
  const handleCopy = async () => {
    const content = result?.final_output?.final_content || ''
    await navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  // 切换步骤详情展开状态
  const toggleStepDetails = (stepName) => {
    setStepDetailsExpanded(prev => prev === stepName ? null : stepName)
  }

  // 切换章节展开/收起
  const toggleSection = (sectionKey) => {
    setExpandedSections(prev => ({
      ...prev,
      [sectionKey]: !prev[sectionKey]
    }))
  }

  // 初始化展开状态
  const initExpandedSections = (stepName) => {
    const defaultExpanded = {}
    if (stepName === '调研') {
      defaultExpanded.trend = true
      defaultExpanded.painPoints = true
      defaultExpanded.angles = true
      defaultExpanded.productAnalysis = false
    } else if (stepName === '创作') {
      defaultExpanded.headline = true
      defaultExpanded.body = true
    } else if (stepName === '审核') {
      defaultExpanded.score = true
      defaultExpanded.highlights = true
      defaultExpanded.issues = true
    } else if (stepName === '优化') {
      defaultExpanded.optimized = true
    } else if (stepName === '配图') {
      defaultExpanded.prompts = true
    }
    setExpandedSections(defaultExpanded)
  }

  // 提交修改意见
  const handleModify = async () => {
    if (!taskId || !modificationInput.trim()) return

    setIsModifying(true)
    setModifySuccess(false)
    try {
      const response = await axios.post(`${API_BASE}/api/task/${taskId}/confirm`, {
        action: 'modify',
        modifications: {
          feedback: modificationInput.trim(),
          step: taskStatus?.current_step?.split('完成')[0]
        }
      })

      // 显示成功提示
      setModifySuccess(true)
      setTimeout(() => setModifySuccess(false), 3000)

      // 清空输入框
      setModificationInput('')
      // 继续轮询
      pollTaskStatus(taskId)
    } catch (err) {
      console.error('提交修改意见失败:', err)
      setError('提交修改意见失败：' + (err.response?.data?.detail || err.message))
    } finally {
      setIsModifying(false)
    }
  }

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (pollTimerRef.current) {
        clearTimeout(pollTimerRef.current)
      }
    }
  }, [])

  // 平台选项
  const platformOptions = [
    { value: 'xiaohongshu', label: '小红书' },
    { value: 'wechat', label: '微信公众号' },
    { value: 'blog', label: '博客' }
  ]

  // 语气选项
  const toneOptions = [
    { value: 'casual', label: '轻松随意' },
    { value: 'formal', label: '正式专业' },
    { value: 'passionate', label: '激情澎湃' }
  ]

  // 获取步骤状态
  const getStepStatus = (stepName) => {
    if (!taskStatus?.steps) return 'pending'
    const step = taskStatus.steps.find(s => s.name === stepName)
    return step?.status || 'pending'
  }

  // 获取当前步骤索引
  const getCurrentStepIndex = () => {
    if (!taskStatus?.current_step) return -1
    const index = workflowSteps.findIndex(s => s.name === taskStatus.current_step.split('完成')[0])
    return index >= 0 ? index : -1
  }

  // 渲染进度流
  const renderProgressFlow = () => (
    <div className="bg-white rounded-xl shadow-sm p-6 mb-6" style={{ borderColor: colors.border, borderWidth: 1 }}>
      <h2 className="text-lg font-medium mb-4" style={{ color: colors.text.primary }}>执行进度</h2>

      {/* 总体进度条 */}
      <div className="mb-6">
        <div className="flex justify-between text-sm mb-2" style={{ color: colors.text.tertiary }}>
          <span>总体进度</span>
          <span style={{ color: colors.text.primary }}>{taskStatus?.progress || 0}%</span>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-2">
          <div
            className="h-2 rounded-full transition-all duration-500"
            style={{
              width: `${taskStatus?.progress || 0}%`,
              backgroundColor: colors.blue.dark
            }}
          />
        </div>
      </div>

      {/* 流式节点 */}
      <div className="flex items-center justify-between">
        {workflowSteps.map((step, index) => {
          const status = getStepStatus(step.name)
          const isCompleted = status === 'completed'
          const isRunning = status === 'running'
          const isFailed = status === 'failed'
          const isCurrent = taskStatus?.current_step?.includes(step.name)

          return (
            <div key={step.key} className="flex flex-col items-center flex-1">
              {/* 节点图标 */}
              <div
                className={`w-12 h-12 rounded-xl flex items-center justify-center text-xl transition-all duration-300 ${
                  isRunning || isCurrent ? 'animate-pulse' : ''
                }`}
                style={{
                  backgroundColor: isCompleted
                    ? step.color.light
                    : isRunning || isCurrent
                    ? step.color.light
                    : isFailed
                    ? colors.red.light
                    : '#F5F5F5',
                  border: `2px solid ${
                    isCompleted
                      ? step.color.dark
                      : isRunning || isCurrent
                      ? step.color.dark
                      : isFailed
                      ? colors.red.dark
                      : colors.border
                  }`
                }}
              >
                {step.icon}
              </div>

              {/* 步骤名称 */}
              <span
                className="text-xs mt-2 font-medium"
                style={{
                  color: isCompleted || isRunning || isCurrent ? step.color.dark : colors.text.tertiary
                }}
              >
                {step.name}
              </span>

              {/* 连接线 */}
              {index < workflowSteps.length - 1 && (
                <div
                  className="flex-1 h-0.5 mx-2 mb-6"
                  style={{
                    backgroundColor: isCompleted ? step.color.dark : colors.border,
                    maxWidth: '40px'
                  }}
                />
              )}
            </div>
          )
        })}
      </div>

      {/* 当前步骤提示 */}
      {taskStatus?.current_step && (
        <div
          className="mt-4 p-3 rounded-lg text-sm"
          style={{ backgroundColor: colors.cyan.light, color: colors.cyan.dark }}
        >
          <span className="font-medium">当前:</span> {taskStatus.current_step}
        </div>
      )}
    </div>
  )

  // 渲染阶段详情
  const renderStepDetails = (stepName, stepResult) => {
    if (!stepResult) return null

    return (
      <div className="space-y-3">
        {stepName === '调研' && (
          <>
            {stepResult.trend_analysis && (
              <div className="border rounded-lg overflow-hidden" style={{ borderColor: colors.border }}>
                <button
                  onClick={() => toggleSection('trend')}
                  className="w-full px-4 py-3 text-left text-sm font-medium flex items-center justify-between transition-colors"
                  style={{ backgroundColor: expandedSections.trend ? colors.blue.light : colors.cardBg, color: colors.text.primary }}
                >
                  <span>📊 趋势分析</span>
                  <span className="text-xs">{expandedSections.trend ? '▼' : '▶'}</span>
                </button>
                {expandedSections.trend && (
                  <div className="px-4 py-3 text-sm" style={{ color: colors.text.secondary }}>
                    <p className="whitespace-pre-wrap">{stepResult.trend_analysis}</p>
                  </div>
                )}
              </div>
            )}
            {stepResult.pain_points && stepResult.pain_points.length > 0 && (
              <div className="border rounded-lg overflow-hidden" style={{ borderColor: colors.border }}>
                <button
                  onClick={() => toggleSection('painPoints')}
                  className="w-full px-4 py-3 text-left text-sm font-medium flex items-center justify-between transition-colors"
                  style={{ backgroundColor: expandedSections.painPoints ? colors.blue.light : colors.cardBg, color: colors.text.primary }}
                >
                  <span>💡 用户痛点</span>
                  <span className="text-xs">{expandedSections.painPoints ? '▼' : '▶'}</span>
                </button>
                {expandedSections.painPoints && (
                  <div className="px-4 py-3">
                    <ul className="space-y-2">
                      {stepResult.pain_points.map((pain, i) => (
                        <li key={i} className="text-sm" style={{ color: colors.text.secondary }}>
                          <span className="font-medium" style={{ color: colors.text.primary }}>{pain.title}:</span> {pain.description}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
            {stepResult.angles && stepResult.angles.length > 0 && (
              <div className="border rounded-lg overflow-hidden" style={{ borderColor: colors.border }}>
                <button
                  onClick={() => toggleSection('angles')}
                  className="w-full px-4 py-3 text-left text-sm font-medium flex items-center justify-between transition-colors"
                  style={{ backgroundColor: expandedSections.angles ? colors.blue.light : colors.cardBg, color: colors.text.primary }}
                >
                  <span>🎯 推荐选题角度</span>
                  <span className="text-xs">{expandedSections.angles ? '▼' : '▶'}</span>
                </button>
                {expandedSections.angles && (
                  <div className="px-4 py-3">
                    <ul className="space-y-2">
                      {stepResult.angles.map((angle, i) => (
                        <li key={i} className="text-sm" style={{ color: colors.text.secondary }}>
                          <div className="font-medium" style={{ color: colors.blue.dark }}>{angle.headline}</div>
                          <div className="text-xs" style={{ color: colors.text.tertiary }}>
                            情绪触发：{angle.emotion_trigger} | 置信度：{(angle.confidence_score * 100).toFixed(0)}%
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
            {stepResult.product_analysis && (
              <div className="border rounded-lg overflow-hidden" style={{ borderColor: colors.border }}>
                <button
                  onClick={() => toggleSection('productAnalysis')}
                  className="w-full px-4 py-3 text-left text-sm font-medium flex items-center justify-between transition-colors"
                  style={{ backgroundColor: expandedSections.productAnalysis ? colors.blue.light : colors.cardBg, color: colors.text.primary }}
                >
                  <span>📸 产品分析</span>
                  <span className="text-xs">{expandedSections.productAnalysis ? '▼' : '▶'}</span>
                </button>
                {expandedSections.productAnalysis && (
                  <div className="px-4 py-3 space-y-2">
                    <p className="text-sm" style={{ color: colors.text.secondary }}>{stepResult.product_analysis.description}</p>
                    {stepResult.product_analysis.selling_points && (
                      <div className="mt-2 space-y-2">
                        <p className="text-xs font-medium" style={{ color: colors.text.primary }}>主打卖点:</p>
                        {stepResult.product_analysis.selling_points.map((sp, i) => (
                          <div key={i} className="text-sm" style={{ color: colors.green.dark }}>
                            • {sp.name}: {sp.description}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {stepName === '创作' && (
          <>
            {stepResult.headline && (
              <div className="border rounded-lg overflow-hidden" style={{ borderColor: colors.border }}>
                <button
                  onClick={() => toggleSection('headline')}
                  className="w-full px-4 py-3 text-left text-sm font-medium flex items-center justify-between transition-colors"
                  style={{ backgroundColor: expandedSections.headline ? colors.green.light : colors.cardBg, color: colors.text.primary }}
                >
                  <span>📝 标题</span>
                  <span className="text-xs">{expandedSections.headline ? '▼' : '▶'}</span>
                </button>
                {expandedSections.headline && (
                  <div className="px-4 py-3">
                    <p className="text-sm font-medium" style={{ color: colors.blue.dark }}>{stepResult.headline}</p>
                  </div>
                )}
              </div>
            )}
            {stepResult.body && (
              <div className="border rounded-lg overflow-hidden" style={{ borderColor: colors.border }}>
                <button
                  onClick={() => toggleSection('body')}
                  className="w-full px-4 py-3 text-left text-sm font-medium flex items-center justify-between transition-colors"
                  style={{ backgroundColor: expandedSections.body ? colors.green.light : colors.cardBg, color: colors.text.primary }}
                >
                  <span>📄 文案正文</span>
                  <span className="text-xs">{expandedSections.body ? '▼' : '▶'}</span>
                </button>
                {expandedSections.body && (
                  <div className="px-4 py-3">
                    <div className="p-3 rounded bg-white text-sm whitespace-pre-wrap" style={{ color: colors.text.secondary, border: `1px solid ${colors.border}` }}>
                      {stepResult.body}
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {stepName === '审核' && (
          <>
            <div className="border rounded-lg overflow-hidden" style={{ borderColor: colors.border }}>
              <button
                onClick={() => toggleSection('score')}
                className="w-full px-4 py-3 text-left text-sm font-medium flex items-center justify-between transition-colors"
                style={{ backgroundColor: expandedSections.score ? colors.purple.light : colors.cardBg, color: colors.text.primary }}
              >
                <span>📊 审核评分</span>
                <span className="text-xs">{expandedSections.score ? '▼' : '▶'}</span>
              </button>
              {expandedSections.score && (
                <div className="px-4 py-3">
                  <div className="flex items-center gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold" style={{ color: colors.purple.dark }}>
                        {stepResult.overall_score}/6
                      </div>
                      <div className="text-xs" style={{ color: colors.text.tertiary }}>总体评分</div>
                    </div>
                    <div className="text-center">
                      <div className="text-sm font-medium" style={{ color: colors.text.primary }}>
                        {stepResult.conclusion === 'pass' ? '✅ 通过' : stepResult.conclusion === 'modify' ? '🔧 需修改' : '❌ 需重写'}
                      </div>
                      <div className="text-xs" style={{ color: colors.text.tertiary }}>审核结论</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
            {stepResult.highlights && stepResult.highlights.length > 0 && (
              <div className="border rounded-lg overflow-hidden" style={{ borderColor: colors.border }}>
                <button
                  onClick={() => toggleSection('highlights')}
                  className="w-full px-4 py-3 text-left text-sm font-medium flex items-center justify-between transition-colors"
                  style={{ backgroundColor: expandedSections.highlights ? colors.purple.light : colors.cardBg, color: colors.text.primary }}
                >
                  <span>✨ 亮点</span>
                  <span className="text-xs">{expandedSections.highlights ? '▼' : '▶'}</span>
                </button>
                {expandedSections.highlights && (
                  <div className="px-4 py-3">
                    <ul className="space-y-1">
                      {stepResult.highlights.map((h, i) => (
                        <li key={i} className="text-sm" style={{ color: colors.green.dark }}>• {h}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
            {stepResult.must_fix_issues && stepResult.must_fix_issues.length > 0 && (
              <div className="border rounded-lg overflow-hidden" style={{ borderColor: colors.border }}>
                <button
                  onClick={() => toggleSection('issues')}
                  className="w-full px-4 py-3 text-left text-sm font-medium flex items-center justify-between transition-colors"
                  style={{ backgroundColor: expandedSections.issues ? colors.purple.light : colors.cardBg, color: colors.text.primary }}
                >
                  <span>⚠️ 需改进的问题</span>
                  <span className="text-xs">{expandedSections.issues ? '▼' : '▶'}</span>
                </button>
                {expandedSections.issues && (
                  <div className="px-4 py-3">
                    <ul className="space-y-2">
                      {stepResult.must_fix_issues.map((issue, i) => (
                        <li key={i} className="text-sm" style={{ color: colors.red.dark }}>
                          <span className="font-medium">[{issue.location}]</span> {issue.problem}
                          <div className="text-xs" style={{ color: colors.text.tertiary }}>建议：{issue.suggestion}</div>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {stepName === '优化' && (
          <div className="border rounded-lg overflow-hidden" style={{ borderColor: colors.border }}>
            <button
              onClick={() => toggleSection('optimized')}
              className="w-full px-4 py-3 text-left text-sm font-medium flex items-center justify-between transition-colors"
              style={{ backgroundColor: expandedSections.optimized ? colors.cyan.light : colors.cardBg, color: colors.text.primary }}
            >
              <span>✨ 优化后文案</span>
              <span className="text-xs">{expandedSections.optimized ? '▼' : '▶'}</span>
            </button>
            {expandedSections.optimized && (
              <div className="px-4 py-3">
                {stepResult.status === 'skipped' ? (
                  <p className="text-sm" style={{ color: colors.text.tertiary }}>{stepResult.reason}</p>
                ) : (
                  <div className="p-3 rounded bg-white text-sm whitespace-pre-wrap" style={{ color: colors.text.secondary, border: `1px solid ${colors.border}` }}>
                    {stepResult.optimized_content}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {stepName === '配图' && (
          <div className="space-y-4">
            {/* 生成的实际图片 */}
            {stepResult.generated_images && stepResult.generated_images.length > 0 && (
              <div className="border rounded-lg overflow-hidden" style={{ borderColor: colors.border }}>
                <button
                  onClick={() => toggleSection('generatedImages')}
                  className="w-full px-4 py-3 text-left text-sm font-medium flex items-center justify-between transition-colors"
                  style={{ backgroundColor: expandedSections.generatedImages ? colors.orange.light : colors.cardBg, color: colors.text.primary }}
                >
                  <span>🖼️ 生成的图片</span>
                  <span className="text-xs">{expandedSections.generatedImages ? '▼' : '▶'}</span>
                </button>
                {expandedSections.generatedImages && (
                  <div className="px-4 py-3">
                    <div className="grid grid-cols-2 gap-3">
                      {stepResult.generated_images.map((imgPath, i) => (
                        <div key={i} className="relative">
                          <img
                            src={`${API_BASE}/uploads/${imgPath.split('/').pop()}`}
                            alt={`生成的图片 ${i + 1}`}
                            className="w-full h-48 object-cover rounded-lg"
                          />
                          <a
                            href={`${API_BASE}/uploads/${imgPath.split('/').pop()}`}
                            download
                            className="absolute top-2 right-2 px-2 py-1 rounded text-xs font-medium"
                            style={{ backgroundColor: 'rgba(0,0,0,0.6)', color: '#fff' }}
                          >
                            📥 下载
                          </a>
                        </div>
                      ))}
                    </div>
                    {stepResult.image_metadata && (
                      <div className="mt-3 text-xs" style={{ color: colors.text.tertiary }}>
                        <p>生成模式：{stepResult.image_metadata.image_1?.mode || '文生图'}</p>
                        {stepResult.image_metadata.prompt_cn && (
                          <p className="mt-1">使用 prompt：{stepResult.image_metadata.prompt_cn}</p>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Midjourney 提示词 */}
            <div className="border rounded-lg overflow-hidden" style={{ borderColor: colors.border }}>
              <button
                onClick={() => toggleSection('prompts')}
                className="w-full px-4 py-3 text-left text-sm font-medium flex items-center justify-between transition-colors"
                style={{ backgroundColor: expandedSections.prompts ? colors.orange.light : colors.cardBg, color: colors.text.primary }}
              >
                <span>🎨 Midjourney 配图方案</span>
                <span className="text-xs">{expandedSections.prompts ? '▼' : '▶'}</span>
              </button>
              {expandedSections.prompts && (
                <div className="px-4 py-3 space-y-3">
                  {stepResult.mj_prompts && stepResult.mj_prompts.length > 0 && (
                    stepResult.mj_prompts.map((prompt, i) => (
                      <div key={i} className="p-3 rounded" style={{ backgroundColor: colors.orange.light }}>
                        <div className="text-sm font-medium mb-1" style={{ color: colors.orange.dark }}>
                          🎨 {prompt.style}
                        </div>
                        <div className="text-xs" style={{ color: colors.text.secondary }}>
                          {prompt.prompt_cn}
                        </div>
                        <div className="text-xs mt-1" style={{ color: colors.text.tertiary }}>
                          {prompt.prompt_en}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    )
  }

  // 渲染确认对话框
  const renderConfirmationDialog = () => {
    if (!awaitingConfirmation) return null

    const currentStepName = taskStatus?.current_step?.split('完成')[0] || '当前步骤'
    const stepIndex = workflowSteps.findIndex(s => s.name === currentStepName)
    const step = workflowSteps[stepIndex]

    return (
      <div className="fixed inset-0 bg-black bg-opacity-30 flex items-center justify-center z-50">
        <div className="bg-white rounded-2xl shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
          {/* 头部 */}
          <div
            className="px-6 py-4 rounded-t-2xl sticky top-0 z-10"
            style={{ backgroundColor: step?.color.light }}
          >
            <div className="flex items-center gap-3">
              <span className="text-3xl">{step?.icon}</span>
              <div>
                <h3 className="text-lg font-medium" style={{ color: step?.color.dark }}>
                  {currentStepName} 完成
                </h3>
                <p className="text-sm" style={{ color: step?.color.dark }}>
                  请查看结果并确认是否继续下一阶段
                </p>
              </div>
            </div>
          </div>

          {/* 内容区域 */}
          <div className="p-6 space-y-4">
            {/* 结果详情 */}
            <div>
              <h4 className="text-sm font-medium mb-3" style={{ color: colors.text.primary }}>📋 生成结果</h4>
              {currentStepResult && step && renderStepDetails(currentStepName, currentStepResult)}
            </div>

            {/* 修改意见输入框 */}
            <div className="border-t pt-4" style={{ borderColor: colors.border }}>
              <h4 className="text-sm font-medium mb-3" style={{ color: colors.text.primary }}>💬 需要修改？</h4>

              {/* 成功提示 */}
              {modifySuccess && (
                <div className="mb-3 p-3 rounded-lg text-sm flex items-center gap-2" style={{ backgroundColor: colors.green.light, color: colors.green.dark }}>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  已提交修改意见，正在重新生成...
                </div>
              )}

              <textarea
                value={modificationInput}
                onChange={(e) => setModificationInput(e.target.value)}
                placeholder="请输入您的修改意见，例如：'语气再活泼一些'、'增加一个具体的案例'、'标题不够吸引人'..."
                rows={3}
                className="w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 transition-all resize-none"
                style={{
                  borderColor: colors.border,
                  backgroundColor: colors.bg,
                  '--tw-ring-color': colors.orange.light
                }}
              />
              <div className="flex justify-end mt-2">
                <button
                  onClick={handleModify}
                  disabled={!modificationInput.trim() || isModifying}
                  className="px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2"
                  style={{
                    backgroundColor: (!modificationInput.trim() || isModifying) ? colors.border : colors.orange.dark,
                    color: (!modificationInput.trim() || isModifying) ? colors.text.tertiary : '#FFFFFF'
                  }}
                >
                  {isModifying ? (
                    <>
                      <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      提交中...
                    </>
                  ) : (
                    <>
                      🔄 提交修改意见
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* 操作按钮 */}
          <div className="px-6 py-4 border-t flex justify-between items-center gap-4 sticky bottom-0 bg-white" style={{ borderColor: colors.border }}>
            <button
              onClick={handleStop}
              className="px-4 py-2 rounded-lg text-sm font-medium transition-all"
              style={{ backgroundColor: colors.red.light, color: colors.red.dark }}
            >
              停止工作流
            </button>
            <div className="flex gap-3">
              <button
                onClick={handleContinue}
                className="px-6 py-2 rounded-lg text-sm font-medium transition-all"
                style={{ backgroundColor: step?.color.dark, color: '#FFFFFF' }}
              >
                满意，继续下一步
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: colors.bg }}>
      {/* 头部 */}
      <header className="bg-white shadow-sm">
        <div className="max-w-[1600px] mx-auto px-6 py-5">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-medium" style={{ color: colors.text.primary }}>
                多 Agent 文案生成系统
              </h1>
              <p className="text-sm mt-1" style={{ color: colors.text.tertiary }}>
                AI 驱动的智能文案创作工作流
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={async () => {
                  const hist = await loadHistory()
                  setHistory(hist)
                  setShowHistory(!showHistory)
                }}
                className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5"
                style={{ backgroundColor: colors.purple.light, color: colors.purple.dark }}
              >
                📁 历史记录
              </button>
              <span className="px-3 py-1 rounded-full text-xs font-medium" style={{ backgroundColor: colors.blue.light, color: colors.blue.dark }}>
                调研 → 创作 → 审核 → 优化 → 配图
              </span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-[1600px] mx-auto px-6 py-6">
        <div className="grid grid-cols-12 gap-6">
          {/* 左侧：配置栏 (3 列) */}
          <div className="col-span-3">
            <div className="bg-white rounded-xl shadow-sm p-5" style={{ borderColor: colors.border, borderWidth: 1 }}>
              <h2 className="text-base font-medium mb-4" style={{ color: colors.text.primary }}>
                创作配置
              </h2>

              <form onSubmit={handleSubmit} className="space-y-4">
                {/* 主题 */}
                <div>
                  <label className="block text-xs font-medium mb-1.5" style={{ color: colors.text.secondary }}>
                    内容主题 <span style={{ color: colors.red.dark }}>*</span>
                  </label>
                  <input
                    type="text"
                    name="topic"
                    value={formData.topic}
                    onChange={handleInputChange}
                    required
                    className="w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 transition-all"
                    style={{
                      borderColor: colors.border,
                      '--tw-ring-color': colors.blue.light
                    }}
                    placeholder="例如：AI 写作工具"
                  />
                </div>

                {/* 目标受众 */}
                <div>
                  <label className="block text-xs font-medium mb-1.5" style={{ color: colors.text.secondary }}>
                    目标受众
                  </label>
                  <input
                    type="text"
                    name="audience"
                    value={formData.audience}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 transition-all"
                    style={{ borderColor: colors.border }}
                    placeholder="例如：自媒体创作者"
                  />
                </div>

                {/* 产品图片上传 */}
                <div>
                  <label className="block text-xs font-medium mb-1.5" style={{ color: colors.text.secondary }}>
                    产品图片（可选）
                  </label>
                  <div className="border-2 border-dashed rounded-lg p-4 text-center transition-all"
                    style={{ borderColor: imagePreview ? colors.green.light : colors.border }}>
                    {imagePreview ? (
                      <div className="relative">
                        <img src={imagePreview} alt="预览" className="max-h-32 mx-auto rounded-lg" />
                        <button
                          type="button"
                          onClick={handleRemoveImage}
                          className="absolute -top-2 -right-2 w-6 h-6 rounded-full flex items-center justify-center text-xs"
                          style={{ backgroundColor: colors.red.dark, color: '#fff' }}
                        >
                          ✕
                        </button>
                      </div>
                    ) : (
                      <label className="cursor-pointer block">
                        <span className="text-2xl">📷</span>
                        <p className="text-xs mt-1" style={{ color: colors.text.tertiary }}>
                          点击上传图片
                        </p>
                        <p className="text-xs" style={{ color: colors.text.tertiary }}>
                          支持 JPG、PNG 格式
                        </p>
                        <input
                          type="file"
                          accept="image/*"
                          onChange={handleImageSelect}
                          className="hidden"
                        />
                      </label>
                    )}
                  </div>
                  {isUploading && (
                    <p className="text-xs mt-1" style={{ color: colors.blue.dark }}>
                      正在上传图片...
                    </p>
                  )}
                </div>

                {/* 发布平台 */}
                <div>
                  <label className="block text-xs font-medium mb-1.5" style={{ color: colors.text.secondary }}>
                    发布平台
                  </label>
                  <select
                    name="platform"
                    value={formData.platform}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 transition-all bg-white"
                    style={{ borderColor: colors.border }}
                  >
                    {platformOptions.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>

                {/* 语气风格 */}
                <div>
                  <label className="block text-xs font-medium mb-1.5" style={{ color: colors.text.secondary }}>
                    语气风格
                  </label>
                  <select
                    name="tone"
                    value={formData.tone}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 transition-all bg-white"
                    style={{ borderColor: colors.border }}
                  >
                    {toneOptions.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>

                {/* 情绪基调 */}
                <div>
                  <label className="block text-xs font-medium mb-1.5" style={{ color: colors.text.secondary }}>
                    情绪基调
                  </label>
                  <input
                    type="text"
                    name="emotion"
                    value={formData.emotion}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 transition-all"
                    style={{ borderColor: colors.border }}
                    placeholder="hopeful, inspiring"
                  />
                </div>

                {/* 视觉风格 */}
                <div>
                  <label className="block text-xs font-medium mb-1.5" style={{ color: colors.text.secondary }}>
                    视觉风格
                  </label>
                  <input
                    type="text"
                    name="style"
                    value={formData.style}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 transition-all"
                    style={{ borderColor: colors.border }}
                    placeholder="minimalist"
                  />
                </div>

                {/* 品牌关键词 */}
                <div>
                  <label className="block text-xs font-medium mb-1.5" style={{ color: colors.text.secondary }}>
                    品牌关键词
                  </label>
                  <input
                    type="text"
                    name="brand_keywords"
                    value={formData.brand_keywords}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 text-sm border rounded-lg focus:outline-none focus:ring-2 transition-all"
                    style={{ borderColor: colors.border }}
                    placeholder="用逗号分隔"
                  />
                </div>

                {/* 提交按钮 */}
                <button
                  type="submit"
                  disabled={isSubmitting || awaitingConfirmation}
                  className="w-full py-2.5 px-4 rounded-lg font-medium text-sm transition-all mt-2"
                  style={{
                    backgroundColor: (isSubmitting || awaitingConfirmation) ? colors.border : colors.blue.dark,
                    color: '#FFFFFF',
                    opacity: (isSubmitting || awaitingConfirmation) ? 0.6 : 1,
                    cursor: (isSubmitting || awaitingConfirmation) ? 'not-allowed' : 'pointer'
                  }}
                >
                  {isSubmitting ? (
                    <span className="flex items-center justify-center gap-2">
                      <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      生成中...
                    </span>
                  ) : awaitingConfirmation ? (
                    '等待确认中...'
                  ) : (
                    '开始生成'
                  )}
                </button>
              </form>

              {/* 历史记录列表 */}
              {showHistory && (
                <div className="mt-4 pt-4 border-t" style={{ borderColor: colors.border }}>
                  <h3 className="text-xs font-medium mb-2" style={{ color: colors.text.secondary }}>
                    最近历史记录
                  </h3>
                  {history.length === 0 ? (
                    <p className="text-xs" style={{ color: colors.text.tertiary }}>暂无历史记录</p>
                  ) : (
                    <div className="space-y-2 max-h-64 overflow-y-auto">
                      {history.map((item) => (
                        <div
                          key={item.task_id}
                          className="p-2 rounded-lg text-xs cursor-pointer transition-all hover:bg-gray-50"
                          style={{ backgroundColor: colors.bg, border: `1px solid ${colors.border}` }}
                          onClick={() => loadFromHistory(item.task_id)}
                        >
                          <div className="flex justify-between items-start gap-2">
                            <div className="flex-1 min-w-0">
                              <span className="font-medium block truncate" style={{ color: colors.text.primary }}>
                                {item.topic || item.config?.topic || '未命名'}
                              </span>
                              <div className="text-xs mt-0.5 flex items-center gap-1" style={{ color: colors.text.tertiary }}>
                                <span>{item.platform || item.config?.platform || ''}</span>
                                <span>•</span>
                                <span>{new Date(item.created_at).toLocaleString('zh-CN')}</span>
                              </div>
                              {item.final_content_preview && (
                                <div className="text-xs mt-1 truncate" style={{ color: colors.text.tertiary }}>
                                  {item.final_content_preview}
                                </div>
                              )}
                            </div>
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                deleteHistoryEntry(item.task_id)
                              }}
                              className="text-xs px-1.5 py-1 rounded flex-shrink-0"
                              style={{ backgroundColor: colors.red.light, color: colors.red.dark }}
                            >
                              ×
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* 中间：进度流 (4 列) */}
          <div className="col-span-4">
            {/* 空状态 */}
            {!taskStatus && !result && !error && (
              <div className="bg-white rounded-xl shadow-sm p-8 h-full flex flex-col items-center justify-center" style={{ borderColor: colors.border, borderWidth: 1 }}>
                <div className="text-5xl mb-4">📝</div>
                <h3 className="text-base font-medium mb-2" style={{ color: colors.text.primary }}>
                  准备开始创作
                </h3>
                <p className="text-sm text-center max-w-xs" style={{ color: colors.text.tertiary }}>
                  在左侧配置创作参数，可上传产品图片，工作流将依次执行 5 个 Agent 步骤，每步需确认
                </p>
                <div className="mt-6 grid grid-cols-5 gap-2">
                  {workflowSteps.map(step => (
                    <div
                      key={step.key}
                      className="w-10 h-10 rounded-lg flex items-center justify-center text-lg"
                      style={{ backgroundColor: step.color.light }}
                      title={step.name}
                    >
                      {step.icon}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 进度流 */}
            {taskStatus && taskStatus.status !== 'completed' && !awaitingConfirmation && renderProgressFlow()}

            {/* 等待确认状态 */}
            {awaitingConfirmation && (
              <div className="bg-white rounded-xl shadow-sm p-6" style={{ borderColor: colors.border, borderWidth: 1 }}>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-full flex items-center justify-center text-xl" style={{ backgroundColor: colors.cyan.light }}>
                    ⏸️
                  </div>
                  <div>
                    <h3 className="text-base font-medium" style={{ color: colors.text.primary }}>
                      等待您的确认
                    </h3>
                    <p className="text-sm" style={{ color: colors.text.tertiary }}>
                      {taskStatus?.current_step}，请查看结果后决定是否继续
                    </p>
                  </div>
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={handleStop}
                    className="flex-1 py-2 rounded-lg text-sm font-medium transition-all"
                    style={{ backgroundColor: colors.red.light, color: colors.red.dark }}
                  >
                    停止
                  </button>
                  <button
                    onClick={handleContinue}
                    className="flex-1 py-2 rounded-lg text-sm font-medium transition-all"
                    style={{ backgroundColor: colors.blue.dark, color: '#FFFFFF' }}
                  >
                    继续
                  </button>
                </div>
              </div>
            )}

            {/* 错误提示 */}
            {error && (
              <div
                className="bg-white rounded-xl shadow-sm p-6"
                style={{ border: `1px solid ${colors.red.light}` }}
              >
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-8 h-8 rounded-full flex items-center justify-center text-lg" style={{ backgroundColor: colors.red.light }}>
                    ✕
                  </div>
                  <h3 className="text-base font-medium" style={{ color: colors.red.dark }}>
                    生成失败
                  </h3>
                </div>
                <p className="text-sm" style={{ color: colors.text.tertiary }}>{error}</p>
              </div>
            )}

            {/* 完成后显示进度摘要 */}
            {result && !awaitingConfirmation && (
              <div className="bg-white rounded-xl shadow-sm p-6" style={{ borderColor: colors.border, borderWidth: 1 }}>
                <h2 className="text-base font-medium mb-4" style={{ color: colors.text.primary }}>
                  执行完成
                </h2>
                <div className="space-y-2">
                  {workflowSteps.map(step => (
                    <div key={step.key} className="flex items-center gap-3 p-2 rounded-lg" style={{ backgroundColor: step.color.light }}>
                      <span className="text-lg">{step.icon}</span>
                      <span className="text-sm font-medium" style={{ color: step.color.dark }}>{step.name}</span>
                      <span className="ml-auto text-xs" style={{ color: step.color.dark }}>✓ 已完成</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* 右侧：结果区 (5 列) */}
          <div className="col-span-5">
            {!result && !awaitingConfirmation ? (
              <div
                className="bg-white rounded-xl shadow-sm p-8 h-full flex flex-col items-center justify-center"
                style={{ borderColor: colors.border, borderWidth: 1, minHeight: '400px' }}
              >
                <div className="text-5xl mb-4">📄</div>
                <h3 className="text-base font-medium mb-2" style={{ color: colors.text.primary }}>
                  结果将显示在这里
                </h3>
                <p className="text-sm text-center" style={{ color: colors.text.tertiary }}>
                  每个阶段完成后会暂停，确认后即可看到该阶段的详细结果
                </p>
              </div>
            ) : (
              <div className="bg-white rounded-xl shadow-sm h-full flex flex-col" style={{ borderColor: colors.border, borderWidth: 1 }}>
                {/* Tab 切换 */}
                <div className="flex border-b" style={{ borderColor: colors.border }}>
                  <button
                    onClick={() => setActiveTab('content')}
                    className="flex-1 px-4 py-3 text-sm font-medium transition-colors"
                    style={{
                      color: activeTab === 'content' ? colors.blue.dark : colors.text.tertiary,
                      backgroundColor: activeTab === 'content' ? colors.blue.light : 'transparent',
                      borderBottom: activeTab === 'content' ? `2px solid ${colors.blue.dark}` : '2px solid transparent'
                    }}
                  >
                    📝 文案内容
                  </button>
                  <button
                    onClick={() => setActiveTab('review')}
                    className="flex-1 px-4 py-3 text-sm font-medium transition-colors"
                    style={{
                      color: activeTab === 'review' ? colors.purple.dark : colors.text.tertiary,
                      backgroundColor: activeTab === 'review' ? colors.purple.light : 'transparent',
                      borderBottom: activeTab === 'review' ? `2px solid ${colors.purple.dark}` : '2px solid transparent'
                    }}
                  >
                    📊 审核报告
                  </button>
                  <button
                    onClick={() => setActiveTab('image')}
                    className="flex-1 px-4 py-3 text-sm font-medium transition-colors"
                    style={{
                      color: activeTab === 'image' ? colors.orange.dark : colors.text.tertiary,
                      backgroundColor: activeTab === 'image' ? colors.orange.light : 'transparent',
                      borderBottom: activeTab === 'image' ? `2px solid ${colors.orange.dark}` : '2px solid transparent'
                    }}
                  >
                    🎨 配图方案
                  </button>
                  {versionHistory.length > 0 && (
                    <button
                      onClick={() => {
                        setActiveTab('history')
                        handleShowVersionHistory()
                      }}
                      className="flex-1 px-4 py-3 text-sm font-medium transition-colors"
                      style={{
                        color: activeTab === 'history' ? colors.cyan.dark : colors.text.tertiary,
                        backgroundColor: activeTab === 'history' ? colors.cyan.light : 'transparent',
                        borderBottom: activeTab === 'history' ? `2px solid ${colors.cyan.dark}` : '2px solid transparent'
                      }}
                    >
                      📜 版本历史
                    </button>
                  )}
                </div>

                {/* Tab 内容 */}
                <div className="flex-1 p-5 overflow-auto">
                  {/* 文案内容 */}
                  {activeTab === 'content' && (
                    <div>
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-sm font-medium" style={{ color: colors.text.primary }}>最终文案</h3>
                        <button
                          onClick={handleCopy}
                          className="px-3 py-1.5 text-xs font-medium rounded-lg transition-all flex items-center gap-1.5"
                          style={{
                            backgroundColor: copied ? colors.green.light : colors.border,
                            color: copied ? colors.green.dark : colors.text.secondary
                          }}
                        >
                          {copied ? '✓ 已复制' : '📋 复制'}
                        </button>
                      </div>
                      <div
                        className="p-4 rounded-lg text-sm leading-relaxed"
                        style={{ backgroundColor: colors.bg }}
                      >
                        <p className="whitespace-pre-wrap" style={{ color: colors.text.primary }}>
                          {result?.final_output?.final_content || '暂无内容'}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* 审核报告 */}
                  {activeTab === 'review' && result?.final_output?.reviewer && (
                    <div>
                      {/* 总体评分 */}
                      <div className="mb-6 p-4 rounded-lg" style={{ backgroundColor: colors.purple.light }}>
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-xs font-medium mb-1" style={{ color: colors.purple.dark }}>总体评分</p>
                            <p className="text-3xl font-bold" style={{ color: colors.purple.dark }}>
                              {result.final_output.reviewer.overall_score}
                              <span className="text-lg font-normal">/6</span>
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-xs font-medium mb-1" style={{ color: colors.purple.dark }}>审核结论</p>
                            <p className="text-sm font-medium" style={{ color: colors.purple.dark }}>
                              {result.final_output.reviewer.conclusion}
                            </p>
                          </div>
                        </div>
                      </div>

                      {/* 亮点 */}
                      {result.final_output.reviewer.highlights?.length > 0 && (
                        <div>
                          <h4 className="text-sm font-medium mb-3" style={{ color: colors.text.primary }}>✨ 亮点</h4>
                          <ul className="space-y-2">
                            {result.final_output.reviewer.highlights.map((highlight, i) => (
                              <li
                                key={i}
                                className="flex items-start gap-2 p-2.5 rounded-lg"
                                style={{ backgroundColor: colors.green.light }}
                              >
                                <span className="text-green-600">✓</span>
                                <span className="text-sm" style={{ color: colors.green.dark }}>{highlight}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}

                  {/* 配图方案 */}
                  {activeTab === 'image' && result?.final_output?.image && (
                    <div className="space-y-4">
                      {/* 生成的实际图片 */}
                      {result.final_output.image.generated_images && result.final_output.image.generated_images.length > 0 && (
                        <div>
                          <h3 className="text-sm font-medium mb-3" style={{ color: colors.text.primary }}>🖼️ 生成的图片</h3>
                          <div className="grid grid-cols-2 gap-3">
                            {result.final_output.image.generated_images.map((imgPath, i) => (
                              <div key={i} className="relative">
                                <img
                                  src={`${API_BASE}/uploads/${imgPath.split('/').pop()}`}
                                  alt={`生成的图片 ${i + 1}`}
                                  className="w-full h-48 object-cover rounded-lg"
                                />
                                <a
                                  href={`${API_BASE}/uploads/${imgPath.split('/').pop()}`}
                                  download
                                  className="absolute top-2 right-2 px-2 py-1 rounded text-xs font-medium"
                                  style={{ backgroundColor: 'rgba(0,0,0,0.6)', color: '#fff' }}
                                >
                                  📥 下载
                                </a>
                              </div>
                            ))}
                          </div>
                          {result.final_output.image.image_metadata && (
                            <div className="mt-3 text-xs" style={{ color: colors.text.tertiary }}>
                              <p>生成模式：{result.final_output.image.image_metadata.image_1?.mode || '文生图'}</p>
                              {result.final_output.image.image_metadata.prompt_cn && (
                                <p className="mt-1">使用 prompt：{result.final_output.image.image_metadata.prompt_cn}</p>
                              )}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Midjourney 提示词 */}
                      {result.final_output.image.mj_prompts && result.final_output.image.mj_prompts.length > 0 && (
                        <div>
                          <h3 className="text-sm font-medium mb-3" style={{ color: colors.text.primary }}>🎨 Midjourney 配图方案</h3>
                          {result.final_output.image.mj_prompts.map((prompt, i) => (
                            <div
                              key={i}
                              className="p-4 rounded-lg"
                              style={{ backgroundColor: colors.orange.light, borderColor: colors.orange.dark, borderWidth: 1 }}
                            >
                              <div className="flex items-center gap-2 mb-2">
                                <span className="text-lg">🎨</span>
                                <h4 className="text-sm font-medium" style={{ color: colors.orange.dark }}>
                                  方案 {i + 1}: {prompt.style}
                                </h4>
                              </div>
                              <p className="text-sm font-medium" style={{ color: colors.orange.dark }}>
                                {prompt.prompt_cn}
                              </p>
                              <p className="text-xs leading-relaxed mt-1" style={{ color: colors.text.secondary }}>
                                {prompt.prompt_en}
                              </p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* 版本历史 */}
                  {activeTab === 'history' && versionHistory.length > 0 && (
                    <div className="space-y-4">
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-sm font-medium" style={{ color: colors.text.primary }}>
                          对话历史（{versionHistory.length}个版本）
                        </h3>
                        {currentVersionIndex !== null && (
                          <span className="text-xs px-2 py-1 rounded" style={{ backgroundColor: colors.blue.light, color: colors.blue.dark }}>
                            当前版本：V{currentVersionIndex + 1}
                          </span>
                        )}
                      </div>

                      {versionHistory.map((version) => (
                        <div
                          key={version.version}
                          className="p-4 rounded-lg border transition-all"
                          style={{
                            backgroundColor: version.version === currentVersionIndex ? colors.blue.light : colors.bg,
                            borderColor: version.version === currentVersionIndex ? colors.blue.dark : colors.border
                          }}
                        >
                          <div className="flex items-start justify-between gap-3 mb-2">
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium" style={{ color: colors.text.primary }}>
                                版本 {version.version + 1}
                              </span>
                              {version.version === currentVersionIndex && (
                                <span className="text-xs px-1.5 py-0.5 rounded" style={{ backgroundColor: colors.green.light, color: colors.green.dark }}>
                                  当前
                                </span>
                              )}
                            </div>
                            <span className="text-xs" style={{ color: colors.text.tertiary }}>
                              {new Date(version.created_at).toLocaleString('zh-CN')}
                            </span>
                          </div>

                          {version.feedback_preview && version.feedback_preview !== '初始版本' && (
                            <div className="mb-3 text-sm" style={{ color: colors.text.secondary }}>
                              <span style={{ color: colors.orange.dark }}>修改意见：</span>{version.feedback_preview}
                            </div>
                          )}

                          {version.version !== currentVersionIndex && (
                            <button
                              onClick={() => restoreVersion(taskId, version.version)}
                              className="text-xs px-3 py-1.5 rounded transition-all"
                              style={{ backgroundColor: colors.blue.dark, color: '#fff' }}
                            >
                              恢复到这个版本
                            </button>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* 阶段确认对话框 */}
      {renderConfirmationDialog()}
    </div>
  )
}

export default App
