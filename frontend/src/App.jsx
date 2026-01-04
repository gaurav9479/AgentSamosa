import { useState, useEffect, useRef, useCallback } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar } from 'recharts'

const COLORS = ['#3b82f6', '#22c55e', '#f97316', '#8b5cf6', '#ef4444', '#06b6d4']
const PAGE_SIZE = 20

// Theme toggle component
const ThemeToggle = ({ theme, toggleTheme }) => (
  <button className="theme-toggle" onClick={toggleTheme} title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}>
    <span className="theme-toggle-icon">{theme === 'dark' ? '☀️' : '🌙'}</span>
    <span>{theme === 'dark' ? 'Light' : 'Dark'}</span>
  </button>
)

// Voice recognition hook - simplified and more robust
const useVoiceRecognition = () => {
  const [isListening, setIsListening] = useState(false)
  const [isSupported, setIsSupported] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [error, setError] = useState(null)
  const recognitionRef = useRef(null)

  // Initialize speech recognition once
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition

    if (!SpeechRecognition) {
      console.log('Speech recognition not supported')
      setIsSupported(false)
      return
    }

    setIsSupported(true)
    const recognition = new SpeechRecognition()

    // Configuration
    recognition.continuous = false  // Stop after one result
    recognition.interimResults = true
    recognition.lang = 'en-IN'  // English-India (supports Hindi too)

    recognition.onstart = () => {
      console.log('🎤 Recognition started')
      setIsListening(true)
      setError(null)
      setTranscript('')
    }

    recognition.onresult = (event) => {
      console.log('🎤 Got result:', event.results)
      let finalText = ''
      let interimText = ''

      for (let i = 0; i < event.results.length; i++) {
        const result = event.results[i]
        if (result.isFinal) {
          finalText += result[0].transcript
        } else {
          interimText += result[0].transcript
        }
      }

      // Update transcript with whatever we have
      setTranscript(finalText || interimText)
      console.log('🎤 Transcript:', finalText || interimText)
    }

    recognition.onerror = (event) => {
      console.error('🎤 Error:', event.error)
      setError(event.error)
      setIsListening(false)
    }

    recognition.onend = () => {
      console.log('🎤 Recognition ended')
      setIsListening(false)
    }

    recognitionRef.current = recognition

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort()
      }
    }
  }, [])

  const startListening = useCallback(() => {
    if (!recognitionRef.current) {
      console.log('🎤 Recognition not available')
      return
    }

    // Reset state
    setTranscript('')
    setError(null)

    try {
      recognitionRef.current.start()
      console.log('🎤 Starting...')
    } catch (err) {
      console.error('🎤 Start failed:', err)
      // Already started? Stop and restart
      if (err.name === 'InvalidStateError') {
        recognitionRef.current.stop()
      }
    }
  }, [])

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop()
    }
  }, [])

  const toggleListening = useCallback(() => {
    if (isListening) {
      stopListening()
    } else {
      startListening()
    }
  }, [isListening, startListening, stopListening])

  return {
    isListening,
    isSupported,
    transcript,
    error,
    startListening,
    stopListening,
    toggleListening
  }
}

// Voice button component with SVG icons
const VoiceButton = ({ isListening, isSupported, onClick, disabled }) => {
  if (!isSupported) return null

  return (
    <button
      type="button"
      className={`voice-btn ${isListening ? 'listening' : ''}`}
      onClick={onClick}
      disabled={disabled}
      title={isListening ? 'Listening... (click to stop)' : 'Click to speak (Hindi/English)'}
    >
      {isListening ? (
        // Stop/recording icon
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor" />
        </svg>
      ) : (
        // Microphone icon
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
          <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
          <line x1="12" x2="12" y1="19" y2="22" />
        </svg>
      )}
      {isListening && <span className="voice-pulse"></span>}
    </button>
  )
}

const getPasswordStrength = (password) => {
  if (!password) return { score: 0, label: '', color: '' }

  let score = 0

  // Length checks
  if (password.length >= 6) score += 1
  if (password.length >= 8) score += 1
  if (password.length >= 12) score += 1

  // Character variety checks
  if (/[a-z]/.test(password)) score += 1
  if (/[A-Z]/.test(password)) score += 1
  if (/[0-9]/.test(password)) score += 1
  if (/[^a-zA-Z0-9]/.test(password)) score += 1

  // Map score to strength level
  if (score <= 2) return { score: 1, label: 'Weak', color: '#ef4444' }
  if (score <= 4) return { score: 2, label: 'Fair', color: '#f97316' }
  if (score <= 5) return { score: 3, label: 'Good', color: '#eab308' }
  if (score <= 6) return { score: 4, label: 'Strong', color: '#22c55e' }
  return { score: 5, label: 'Very Strong', color: '#10b981' }
}

function App() {
  // Theme state
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('kommandai_theme')
    return saved || 'light'
  })

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark')
  }

  // Apply theme to document
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('kommandai_theme', theme)
  }, [theme])

  // Auth state
  const [user, setUser] = useState(null)
  const [loginForm, setLoginForm] = useState({ email: '', password: '' })
  const [rememberMe, setRememberMe] = useState(false)
  const [loginLoading, setLoginLoading] = useState(false)
  const [loginError, setLoginError] = useState('')
  const [showRegister, setShowRegister] = useState(false)
  const [registerForm, setRegisterForm] = useState({ name: '', email: '', password: '', phone: '' })
  const [registerLoading, setRegisterLoading] = useState(false)
  const [showLoginPassword, setShowLoginPassword] = useState(false)
  const [showRegisterPassword, setShowRegisterPassword] = useState(false)
  const [showForgotPassword, setShowForgotPassword] = useState(false)
  const [forgotEmail, setForgotEmail] = useState('')
  const [forgotMessage, setForgotMessage] = useState('')
  const [forgotLoading, setForgotLoading] = useState(false)
  const [resetToken, setResetToken] = useState('')
  const [showResetPassword, setShowResetPassword] = useState(false)
  const [resetForm, setResetForm] = useState({ password: '', confirmPassword: '' })
  const [showResetNewPassword, setShowResetNewPassword] = useState(false)
  const [resetMessage, setResetMessage] = useState('')
  const [resetLoading, setResetLoading] = useState(false)

  // Customer view states
  const [shopCategories, setShopCategories] = useState([])
  const [shops, setShops] = useState([])
  const [shopsHasMore, setShopsHasMore] = useState(true)
  const [shopsPage, setShopsPage] = useState(0)
  const [shopsSearch, setShopsSearch] = useState('')
  const [selectedShopCategory, setSelectedShopCategory] = useState(null)
  const [selectedShop, setSelectedShop] = useState(null)
  const [shopProducts, setShopProducts] = useState([])
  const [productsHasMore, setProductsHasMore] = useState(true)
  const [productsPage, setProductsPage] = useState(0)
  const [cart, setCart] = useState([])
  const [searchQuery, setSearchQuery] = useState('')

  // Admin view states
  const [activeTab, setActiveTab] = useState('dashboard')
  const [dashboardStats, setDashboardStats] = useState({})
  const [products, setProducts] = useState([])
  const [adminProductsPage, setAdminProductsPage] = useState(0)
  const [adminProductsHasMore, setAdminProductsHasMore] = useState(true)
  const [adminProductSearch, setAdminProductSearch] = useState('')
  const [orders, setOrders] = useState([])
  const [ordersPage, setOrdersPage] = useState(0)
  const [ordersHasMore, setOrdersHasMore] = useState(true)
  const [orderSearch, setOrderSearch] = useState('')
  const [orderStatusFilter, setOrderStatusFilter] = useState('')
  const [lowStockProducts, setLowStockProducts] = useState([])
  const [categories, setCategories] = useState([])

  // Super Admin states
  const [platformStats, setPlatformStats] = useState({})
  const [allShops, setAllShops] = useState([])
  const [allShopsPage, setAllShopsPage] = useState(0)
  const [allShopsHasMore, setAllShopsHasMore] = useState(true)
  const [shopSearch, setShopSearch] = useState('')
  const [allUsers, setAllUsers] = useState([])
  const [usersPage, setUsersPage] = useState(0)
  const [usersHasMore, setUsersHasMore] = useState(true)
  const [userSearch, setUserSearch] = useState('')
  const [userRoleFilter, setUserRoleFilter] = useState('')
  const [superAdminTab, setSuperAdminTab] = useState('overview')
  const [showShopForm, setShowShopForm] = useState(false)
  const [shopForm, setShopForm] = useState({
    name: '', description: '', category_id: '',
    owner_name: '', owner_email: '', owner_phone: '',
    address: '', city: '', pincode: '', gst_number: ''
  })
  const [editingShop, setEditingShop] = useState(null)
  // Category detail view states
  const [selectedAdminCategory, setSelectedAdminCategory] = useState(null)
  const [categoryShops, setCategoryShops] = useState([])
  const [categoryInfo, setCategoryInfo] = useState(null)
  // Shop detail modal states
  const [showShopDetailModal, setShowShopDetailModal] = useState(false)
  const [shopDetailStats, setShopDetailStats] = useState(null)
  const [loadingShopDetail, setLoadingShopDetail] = useState(false)

  // UI states
  const [isConnected, setIsConnected] = useState(false)
  const [logs, setLogs] = useState([])
  const [command, setCommand] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [suggestions, setSuggestions] = useState([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [quickActions, setQuickActions] = useState([])
  const [selectedSuggestion, setSelectedSuggestion] = useState(-1)

  // Form states
  const [productForm, setProductForm] = useState({
    name: '', description: '', brand: '', sku: '', barcode: '',
    price: '', cost_price: '', min_price: '', compare_at_price: '',
    quantity: '', min_stock_level: '5', category_id: '',
    tags: '', unit: 'piece', is_featured: false
  })
  const [editingProduct, setEditingProduct] = useState(null)

  const wsRef = useRef(null)
  const observerRef = useRef(null)

  // Voice recognition
  const {
    isListening,
    isSupported: voiceSupported,
    transcript: voiceTranscript,
    error: voiceError,
    toggleListening
  } = useVoiceRecognition()

  // Update command when voice transcript changes
  useEffect(() => {
    if (voiceTranscript) {
      setCommand(voiceTranscript)
    }
  }, [voiceTranscript])

  // Log voice errors
  useEffect(() => {
    if (voiceError) {
      if (voiceError === 'not-allowed') {
        addLog('🎤 Microphone access denied. Please allow in browser settings.', 'error')
      } else if (voiceError === 'network') {
        addLog('🎤 Network error. Speech recognition requires internet.', 'error')
      } else if (voiceError === 'audio-capture') {
        addLog('🎤 No microphone found.', 'error')
      } else if (voiceError !== 'aborted' && voiceError !== 'no-speech') {
        addLog(`🎤 Voice error: ${voiceError}`, 'error')
      }
    }
  }, [voiceError])

  // Infinite scroll callback
  const lastItemRef = useCallback(node => {
    if (isLoading) return
    if (observerRef.current) observerRef.current.disconnect()
    observerRef.current = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting) {
        // Trigger load more based on current context
      }
    })
    if (node) observerRef.current.observe(node)
  }, [isLoading])

  useEffect(() => {
    connectWebSocket()
    fetchShopCategories()
    // Check localStorage first (remember me), then sessionStorage
    const savedUser = localStorage.getItem('kommandai_user') || sessionStorage.getItem('kommandai_user')
    if (savedUser) {
      setUser(JSON.parse(savedUser))
    }
    return () => { if (wsRef.current) wsRef.current.close() }
  }, [])

  useEffect(() => {
    if (selectedShopCategory) {
      setShops([])
      setShopsPage(0)
      setShopsHasMore(true)
      fetchShopsByCategory(selectedShopCategory, 0, true)
    }
  }, [selectedShopCategory])

  useEffect(() => {
    if (selectedShop) {
      setShopProducts([])
      setProductsPage(0)
      setProductsHasMore(true)
      fetchShopProducts(selectedShop, 0, true)
    }
  }, [selectedShop])

  useEffect(() => {
    if (user) {
      if (user.role === 'super_admin') {
        fetchPlatformStats()
        fetchAllShops(0, true)
        fetchAllUsers(0, true)
      } else if (user.role === 'admin' && user.shop_id) {
        fetchAdminDashboard(user.shop_id)
        fetchAdminProducts(user.shop_id, 0, true)
        fetchAdminOrders(user.shop_id, 0, true)
      }
      // Fetch quick actions for the user's role
      fetchQuickActions(user.role)
    }
  }, [user])

  // Fetch suggestions as user types
  useEffect(() => {
    if (!user || !command.trim()) {
      setSuggestions([])
      setShowSuggestions(false)
      return
    }
    const timer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/command/suggestions?query=${encodeURIComponent(command)}&role=${user.role}&limit=5`)
        const data = await res.json()
        setSuggestions(data.suggestions || [])
        setShowSuggestions(data.suggestions?.length > 0)
        setSelectedSuggestion(-1)
      } catch (err) {
        console.error('Error fetching suggestions:', err)
      }
    }, 150)
    return () => clearTimeout(timer)
  }, [command, user])

  // Debounced search effects
  useEffect(() => {
    const timer = setTimeout(() => {
      if (selectedShop) {
        setShopProducts([])
        setProductsPage(0)
        fetchShopProducts(selectedShop, 0, true)
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [searchQuery])

  useEffect(() => {
    const timer = setTimeout(() => {
      if (user?.role === 'admin' && user.shop_id) {
        setProducts([])
        setAdminProductsPage(0)
        fetchAdminProducts(user.shop_id, 0, true)
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [adminProductSearch])

  useEffect(() => {
    const timer = setTimeout(() => {
      if (user?.role === 'admin' && user.shop_id) {
        setOrders([])
        setOrdersPage(0)
        fetchAdminOrders(user.shop_id, 0, true)
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [orderSearch, orderStatusFilter])

  useEffect(() => {
    const timer = setTimeout(() => {
      if (user?.role === 'super_admin') {
        setAllShops([])
        setAllShopsPage(0)
        fetchAllShops(0, true)
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [shopSearch])

  useEffect(() => {
    const timer = setTimeout(() => {
      if (user?.role === 'super_admin') {
        setAllUsers([])
        setUsersPage(0)
        fetchAllUsers(0, true)
      }
    }, 300)
    return () => clearTimeout(timer)
  }, [userSearch, userRoleFilter])

  const connectWebSocket = () => {
    const ws = new WebSocket(`ws://${window.location.hostname}:8000/api/ws`)
    ws.onopen = () => { setIsConnected(true); addLog('Connected to server', 'info') }
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data)
      if (data.type === 'action_result' || data.type === 'data_update') {
        if (user?.role === 'admin' && user.shop_id) {
          fetchAdminDashboard(user.shop_id)
        }
        if (user?.role === 'super_admin') fetchPlatformStats()
      }
    }
    ws.onclose = () => { setIsConnected(false); setTimeout(connectWebSocket, 3000) }
    wsRef.current = ws
  }

  // Auth functions
  const handleLogin = async (e) => {
    e.preventDefault()
    setLoginError('')
    setLoginLoading(true)
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(loginForm)
      })
      if (res.ok) {
        const data = await res.json()
        setUser(data.user)
        // Save to localStorage if remember me, otherwise sessionStorage
        if (rememberMe) {
          localStorage.setItem('kommandai_user', JSON.stringify(data.user))
        } else {
          sessionStorage.setItem('kommandai_user', JSON.stringify(data.user))
        }
        setLoginForm({ email: '', password: '' })
        addLog(`Welcome, ${data.user.name}!`, 'success')
      } else {
        const err = await res.json()
        setLoginError(err.detail || 'Login failed')
      }
    } catch (err) {
      setLoginError('Connection error')
    } finally {
      setLoginLoading(false)
    }
  }

  const handleRegister = async (e) => {
    e.preventDefault()
    setLoginError('')
    setRegisterLoading(true)
    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(registerForm)
      })
      if (res.ok) {
        const data = await res.json()
        setUser(data)
        localStorage.setItem('kommandai_user', JSON.stringify(data))
        setShowRegister(false)
        addLog(`Welcome, ${data.name}!`, 'success')
      } else {
        const err = await res.json()
        setLoginError(err.detail || 'Registration failed')
      }
    } catch (err) {
      setLoginError('Connection error')
    } finally {
      setRegisterLoading(false)
    }
  }

  const logout = () => {
    setUser(null)
    localStorage.removeItem('kommandai_user')
    sessionStorage.removeItem('kommandai_user')
    addLog('Logged out', 'info')
  }

  const handleForgotPassword = async (e) => {
    e.preventDefault()
    setForgotMessage('')
    setForgotLoading(true)
    try {
      const res = await fetch('/api/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: forgotEmail })
      })
      const data = await res.json()
      if (res.ok) {
        setForgotMessage(data.message)
        if (data.reset_token) {
          setResetToken(data.reset_token)
        }
      } else {
        setForgotMessage(data.detail || 'Failed to send reset email')
      }
    } catch (err) {
      setForgotMessage('Connection error')
    } finally {
      setForgotLoading(false)
    }
  }

  const handleResetPassword = async (e) => {
    e.preventDefault()
    setResetMessage('')

    if (resetForm.password !== resetForm.confirmPassword) {
      setResetMessage('Passwords do not match')
      return
    }

    if (resetForm.password.length < 6) {
      setResetMessage('Password must be at least 6 characters')
      return
    }

    setResetLoading(true)
    try {
      const res = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: resetToken, new_password: resetForm.password })
      })
      const data = await res.json()
      if (res.ok) {
        setResetMessage(data.message)
        // After 2 seconds, go back to login
        setTimeout(() => {
          setShowResetPassword(false)
          setShowForgotPassword(false)
          setResetToken('')
          setResetForm({ password: '', confirmPassword: '' })
          setForgotEmail('')
          setForgotMessage('')
          setResetMessage('')
        }, 2000)
      } else {
        setResetMessage(data.detail || 'Failed to reset password')
      }
    } catch (err) {
      setResetMessage('Connection error')
    } finally {
      setResetLoading(false)
    }
  }

  const goToResetPassword = () => {
    setShowResetPassword(true)
  }

  const backToLogin = () => {
    setShowForgotPassword(false)
    setShowResetPassword(false)
    setForgotEmail('')
    setForgotMessage('')
    setResetToken('')
    setResetForm({ password: '', confirmPassword: '' })
    setResetMessage('')
  }

  const fetchShopCategories = async () => {
    try {
      const res = await fetch('/api/shop-categories/with-counts')
      if (res.ok) setShopCategories(await res.json())
    } catch (err) { console.error('Error fetching shop categories:', err) }
  }

  const fetchQuickActions = async (role) => {
    try {
      const res = await fetch(`/api/command/quick-actions?role=${role}`)
      if (res.ok) {
        const data = await res.json()
        setQuickActions(data.quick_actions || [])
      }
    } catch (err) { console.error('Error fetching quick actions:', err) }
  }

  const handleSuggestionSelect = (suggestion) => {
    // Use the first example as the command template
    if (suggestion.examples && suggestion.examples.length > 0) {
      setCommand(suggestion.examples[0])
    } else {
      setCommand(suggestion.template)
    }
    setShowSuggestions(false)
    setSelectedSuggestion(-1)
  }

  const handleQuickAction = (action) => {
    setCommand(action.command)
    // If the command ends with a space or quote, focus on input for user to complete
  }

  const handleCommandKeyDown = (e) => {
    if (!showSuggestions || suggestions.length === 0) return

    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedSuggestion(prev => Math.min(prev + 1, suggestions.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedSuggestion(prev => Math.max(prev - 1, -1))
    } else if (e.key === 'Enter' && selectedSuggestion >= 0) {
      e.preventDefault()
      handleSuggestionSelect(suggestions[selectedSuggestion])
    } else if (e.key === 'Escape') {
      setShowSuggestions(false)
    }
  }

  const fetchShopsByCategory = async (categoryId, page = 0, reset = false) => {
    if (isLoading) return
    setIsLoading(true)
    try {
      let url = `/api/shops/by-category/${categoryId}?skip=${page * PAGE_SIZE}&limit=${PAGE_SIZE}`
      if (shopsSearch) url += `&search=${encodeURIComponent(shopsSearch)}`
      const res = await fetch(url)
      if (res.ok) {
        const data = await res.json()
        setShops(prev => reset ? data : [...prev, ...data])
        setShopsHasMore(data.length === PAGE_SIZE)
        setShopsPage(page)
      }
    } catch (err) { console.error('Error fetching shops:', err) }
    finally { setIsLoading(false) }
  }

  const fetchShopProducts = async (shopId, page = 0, reset = false) => {
    if (isLoading) return
    setIsLoading(true)
    try {
      let url = `/api/shops/${shopId}/products?skip=${page * PAGE_SIZE}&limit=${PAGE_SIZE}`
      if (searchQuery) url += `&search=${encodeURIComponent(searchQuery)}`
      const res = await fetch(url)
      if (res.ok) {
        const data = await res.json()
        setShopProducts(prev => reset ? data : [...prev, ...data])
        setProductsHasMore(data.length === PAGE_SIZE)
        setProductsPage(page)
      }
    } catch (err) { console.error('Error fetching products:', err) }
    finally { setIsLoading(false) }
  }

  const fetchAdminDashboard = async (shopId) => {
    try {
      const [dashRes, lowRes, catRes] = await Promise.all([
        fetch(`/api/shops/${shopId}/dashboard`),
        fetch(`/api/shops/${shopId}/low-stock`),
        fetch('/api/categories')
      ])
      if (dashRes.ok) setDashboardStats(await dashRes.json())
      if (lowRes.ok) setLowStockProducts(await lowRes.json())
      if (catRes.ok) setCategories(await catRes.json())
    } catch (err) { console.error('Error fetching dashboard:', err) }
  }

  const fetchAdminProducts = async (shopId, page = 0, reset = false) => {
    if (isLoading) return
    setIsLoading(true)
    try {
      let url = `/api/shops/${shopId}/products?include_inactive=true&skip=${page * PAGE_SIZE}&limit=${PAGE_SIZE}`
      if (adminProductSearch) url += `&search=${encodeURIComponent(adminProductSearch)}`
      const res = await fetch(url)
      if (res.ok) {
        const data = await res.json()
        setProducts(prev => reset ? data : [...prev, ...data])
        setAdminProductsHasMore(data.length === PAGE_SIZE)
        setAdminProductsPage(page)
      }
    } catch (err) { console.error('Error fetching products:', err) }
    finally { setIsLoading(false) }
  }

  const fetchAdminOrders = async (shopId, page = 0, reset = false) => {
    if (isLoading) return
    setIsLoading(true)
    try {
      let url = `/api/shops/${shopId}/orders?skip=${page * PAGE_SIZE}&limit=${PAGE_SIZE}`
      if (orderStatusFilter) url += `&status=${orderStatusFilter}`
      const res = await fetch(url)
      if (res.ok) {
        let data = await res.json()
        if (orderSearch) {
          data = data.filter(o =>
            o.customer_name?.toLowerCase().includes(orderSearch.toLowerCase()) ||
            o.product_name?.toLowerCase().includes(orderSearch.toLowerCase()) ||
            o.id.toString().includes(orderSearch)
          )
        }
        setOrders(prev => reset ? data : [...prev, ...data])
        setOrdersHasMore(data.length === PAGE_SIZE)
        setOrdersPage(page)
      }
    } catch (err) { console.error('Error fetching orders:', err) }
    finally { setIsLoading(false) }
  }

  const fetchPlatformStats = async () => {
    try {
      const res = await fetch('/api/platform/stats')
      if (res.ok) setPlatformStats(await res.json())
    } catch (err) { console.error('Error fetching platform stats:', err) }
  }

  const fetchAllShops = async (page = 0, reset = false) => {
    if (isLoading) return
    setIsLoading(true)
    try {
      let url = `/api/platform/shops?skip=${page * PAGE_SIZE}&limit=${PAGE_SIZE}`
      if (shopSearch) url += `&search=${encodeURIComponent(shopSearch)}`
      const res = await fetch(url)
      if (res.ok) {
        let data = await res.json()
        if (shopSearch) {
          data = data.filter(s =>
            s.name?.toLowerCase().includes(shopSearch.toLowerCase()) ||
            s.owner_email?.toLowerCase().includes(shopSearch.toLowerCase()) ||
            s.city?.toLowerCase().includes(shopSearch.toLowerCase())
          )
        }
        setAllShops(prev => reset ? data : [...prev, ...data])
        setAllShopsHasMore(data.length === PAGE_SIZE)
        setAllShopsPage(page)
      }
    } catch (err) { console.error('Error fetching shops:', err) }
    finally { setIsLoading(false) }
  }

  const fetchAllUsers = async (page = 0, reset = false) => {
    if (isLoading) return
    setIsLoading(true)
    try {
      let url = `/api/users?skip=${page * PAGE_SIZE}&limit=${PAGE_SIZE}`
      if (userRoleFilter) url += `&role=${userRoleFilter}`
      const res = await fetch(url)
      if (res.ok) {
        let data = await res.json()
        if (userSearch) {
          data = data.filter(u =>
            u.name?.toLowerCase().includes(userSearch.toLowerCase()) ||
            u.email?.toLowerCase().includes(userSearch.toLowerCase())
          )
        }
        setAllUsers(prev => reset ? data : [...prev, ...data])
        setUsersHasMore(data.length === PAGE_SIZE)
        setUsersPage(page)
      }
    } catch (err) { console.error('Error fetching users:', err) }
    finally { setIsLoading(false) }
  }

  const fetchCategoryShops = async (categoryId) => {
    setIsLoading(true)
    try {
      const res = await fetch(`/api/shop-categories/${categoryId}/shops-with-stats`)
      if (res.ok) {
        const data = await res.json()
        setCategoryInfo(data.category)
        setCategoryShops(data.shops)
      }
    } catch (err) { console.error('Error fetching category shops:', err) }
    finally { setIsLoading(false) }
  }

  const fetchShopDetailStats = async (shopId) => {
    setLoadingShopDetail(true)
    try {
      const res = await fetch(`/api/shops/${shopId}/admin-stats`)
      if (res.ok) {
        const data = await res.json()
        setShopDetailStats(data)
        setShowShopDetailModal(true)
      }
    } catch (err) { console.error('Error fetching shop details:', err) }
    finally { setLoadingShopDetail(false) }
  }

  const openCategoryDetail = (categoryId) => {
    setSelectedAdminCategory(categoryId)
    fetchCategoryShops(categoryId)
  }

  const closeCategoryDetail = () => {
    setSelectedAdminCategory(null)
    setCategoryShops([])
    setCategoryInfo(null)
  }

  const closeShopDetailModal = () => {
    setShowShopDetailModal(false)
    setShopDetailStats(null)
  }

  const addLog = (message, type = 'info') => {
    setLogs(prev => [{ message, type, time: new Date().toLocaleTimeString() }, ...prev].slice(0, 30))
  }

  // AI Command
  const sendCommand = async (e) => {
    e?.preventDefault()
    if (!command.trim() || isProcessing) return
    setIsProcessing(true)
    addLog(`Processing: "${command}"`, 'info')
    try {
      const res = await fetch('/api/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: command.trim() })
      })
      const data = await res.json()
      if (res.ok) {
        addLog(`Done: ${data.message || 'Command executed'}`, 'success')

        // Handle form pre-fill response (e.g., add shop command)
        if (data.data?.action_type === 'prefill_form') {
          if (data.data.form_type === 'shop_registration') {
            // Pre-fill shop form and open it
            const formData = data.data.form_data
            setShopForm({
              name: formData.name || '',
              description: formData.description || '',
              category_id: formData.category_id || '',
              owner_name: formData.owner_name || '',
              owner_email: formData.owner_email || '',
              owner_phone: formData.owner_phone || '',
              address: formData.address || '',
              city: formData.city || '',
              pincode: formData.pincode || '',
              gst_number: formData.gst_number || ''
            })
            setEditingShop(null)
            setShowShopForm(true)
            setSuperAdminTab('shops')
            addLog('Form pre-filled. Please review and submit.', 'info')
          }
        }

        // Refresh data based on role
        if (user?.role === 'admin' && user.shop_id) {
          fetchAdminDashboard(user.shop_id)
          fetchAdminProducts(user.shop_id, 0, true)
          fetchAdminOrders(user.shop_id, 0, true)
        }
        if (user?.role === 'super_admin') {
          fetchPlatformStats()
          fetchAllShops(0, true)
        }
      } else {
        addLog(`Error: ${data.detail || 'Failed'}`, 'error')
      }
    } catch (err) { addLog(`Error: ${err.message}`, 'error') }
    finally { setIsProcessing(false); setCommand('') }
  }

  // Product CRUD
  const createProduct = async (e) => {
    e.preventDefault()
    if (!user?.shop_id) return
    try {
      const data = {
        name: productForm.name,
        price: parseFloat(productForm.price),
        shop_id: user.shop_id,
        description: productForm.description || null,
        brand: productForm.brand || null,
        sku: productForm.sku || null,
        cost_price: productForm.cost_price ? parseFloat(productForm.cost_price) : null,
        min_price: productForm.min_price ? parseFloat(productForm.min_price) : null,
        quantity: parseInt(productForm.quantity) || 0,
        min_stock_level: parseInt(productForm.min_stock_level) || 5,
        category_id: productForm.category_id ? parseInt(productForm.category_id) : null,
        tags: productForm.tags || null,
        unit: productForm.unit,
        is_featured: productForm.is_featured
      }
      const res = await fetch('/api/products', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      if (res.ok) {
        addLog(`Product "${productForm.name}" created`, 'success')
        resetProductForm()
        fetchAdminProducts(user.shop_id, 0, true)
        fetchAdminDashboard(user.shop_id)
      } else {
        const err = await res.json()
        addLog(`Error: ${err.detail}`, 'error')
      }
    } catch (err) { addLog(`Error: ${err.message}`, 'error') }
  }

  const updateProduct = async (e) => {
    e.preventDefault()
    if (!editingProduct) return
    try {
      const data = {
        name: productForm.name,
        price: parseFloat(productForm.price),
        description: productForm.description || null,
        brand: productForm.brand || null,
        sku: productForm.sku || null,
        cost_price: productForm.cost_price ? parseFloat(productForm.cost_price) : null,
        min_price: productForm.min_price ? parseFloat(productForm.min_price) : null,
        quantity: parseInt(productForm.quantity) || 0,
        min_stock_level: parseInt(productForm.min_stock_level) || 5,
        category_id: productForm.category_id ? parseInt(productForm.category_id) : null,
        tags: productForm.tags || null,
        unit: productForm.unit,
        is_featured: productForm.is_featured
      }
      const res = await fetch(`/api/products/${editingProduct.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })
      if (res.ok) {
        addLog(`Product "${productForm.name}" updated`, 'success')
        setEditingProduct(null)
        resetProductForm()
        fetchAdminProducts(user.shop_id, 0, true)
        fetchAdminDashboard(user.shop_id)
      }
    } catch (err) { addLog(`Error: ${err.message}`, 'error') }
  }

  const deleteProduct = async (id) => {
    if (!confirm('Delete this product?')) return
    await fetch(`/api/products/${id}`, { method: 'DELETE' })
    addLog('Product deleted', 'success')
    fetchAdminProducts(user.shop_id, 0, true)
    fetchAdminDashboard(user.shop_id)
  }

  const editProduct = (p) => {
    setEditingProduct(p)
    setProductForm({
      name: p.name, description: p.description || '', brand: p.brand || '',
      sku: p.sku || '', barcode: p.barcode || '',
      price: p.price.toString(), cost_price: p.cost_price?.toString() || '',
      min_price: p.min_price?.toString() || '',
      compare_at_price: p.compare_at_price?.toString() || '',
      quantity: p.quantity.toString(), min_stock_level: p.min_stock_level.toString(),
      category_id: p.category_id?.toString() || '', tags: p.tags || '',
      unit: p.unit, is_featured: p.is_featured
    })
    setActiveTab('products')
  }

  const resetProductForm = () => {
    setProductForm({
      name: '', description: '', brand: '', sku: '', barcode: '',
      price: '', cost_price: '', min_price: '', compare_at_price: '',
      quantity: '', min_stock_level: '5', category_id: '',
      tags: '', unit: 'piece', is_featured: false
    })
    setEditingProduct(null)
  }

  // Super Admin actions
  const verifyShop = async (shopId) => {
    const res = await fetch(`/api/platform/shops/${shopId}/verify`, { method: 'PATCH' })
    if (res.ok) {
      addLog('Shop verified', 'success')
      fetchAllShops(0, true)
      fetchPlatformStats()
    }
  }

  const suspendShop = async (shopId) => {
    if (!confirm('Suspend this shop?')) return
    const res = await fetch(`/api/platform/shops/${shopId}/suspend`, { method: 'PATCH' })
    if (res.ok) {
      addLog('Shop suspended', 'success')
      fetchAllShops(0, true)
    }
  }

  const activateShop = async (shopId) => {
    const res = await fetch(`/api/platform/shops/${shopId}/activate`, { method: 'PATCH' })
    if (res.ok) {
      addLog('Shop activated', 'success')
      fetchAllShops(0, true)
    }
  }

  const resetShopForm = () => {
    setShopForm({
      name: '', description: '', category_id: '',
      owner_name: '', owner_email: '', owner_phone: '',
      address: '', city: '', pincode: '', gst_number: ''
    })
    setEditingShop(null)
    setShowShopForm(false)
  }

  const submitShopForm = async (e) => {
    e.preventDefault()
    const payload = {
      ...shopForm,
      category_id: shopForm.category_id ? parseInt(shopForm.category_id) : null
    }

    let res
    if (editingShop) {
      res = await fetch(`/api/shops/${editingShop.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
    } else {
      res = await fetch('/api/shops', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
    }

    if (res.ok) {
      addLog(editingShop ? 'Shop updated' : 'Shop registered', 'success')
      resetShopForm()
      fetchAllShops(0, true)
      fetchPlatformStats()
    } else {
      addLog('Failed to save shop', 'error')
    }
  }

  const startEditShop = (shop) => {
    setShopForm({
      name: shop.name || '',
      description: shop.description || '',
      category_id: shop.category_id?.toString() || '',
      owner_name: shop.owner_name || '',
      owner_email: shop.owner_email || '',
      owner_phone: shop.owner_phone || '',
      address: shop.address || '',
      city: shop.city || '',
      pincode: shop.pincode || '',
      gst_number: shop.gst_number || ''
    })
    setEditingShop(shop)
    setShowShopForm(true)
  }

  const deleteShop = async (shopId) => {
    if (!confirm('Delete this shop? This cannot be undone.')) return
    const res = await fetch(`/api/shops/${shopId}`, { method: 'DELETE' })
    if (res.ok) {
      addLog('Shop deleted', 'success')
      fetchAllShops(0, true)
      fetchPlatformStats()
    }
  }

  // Cart functions
  const addToCart = (product) => {
    setCart(prev => {
      const existing = prev.find(i => i.id === product.id)
      if (existing) {
        return prev.map(i => i.id === product.id ? { ...i, qty: i.qty + 1 } : i)
      }
      return [...prev, { ...product, qty: 1 }]
    })
    addLog(`Added ${product.name} to cart`, 'success')
  }

  const removeFromCart = (id) => setCart(prev => prev.filter(i => i.id !== id))
  const cartTotal = cart.reduce((sum, i) => sum + i.price * i.qty, 0)

  // Search/Filter bar component
  const SearchFilterBar = ({ search, setSearch, placeholder, filters }) => (
    <div className="search-filter-bar">
      <div className="search-input-wrapper">
        <span className="search-icon">🔍</span>
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder={placeholder}
          className="search-input"
        />
        {search && <button className="clear-btn" onClick={() => setSearch('')}>×</button>}
      </div>
      {filters}
    </div>
  )

  // Load More button component
  const LoadMoreButton = ({ hasMore, isLoading, onClick }) => (
    hasMore && (
      <div className="load-more-wrapper">
        <button className="load-more-btn" onClick={onClick} disabled={isLoading}>
          {isLoading ? 'Loading...' : 'Load More'}
        </button>
      </div>
    )
  )

  // ============== LOGIN PAGE ==============
  if (!user) {
    return (
      <div className="login-page">
        <div className="login-container">
          <div className="login-header">
            <h1>KommandAI</h1>
            <p>Multi-Vendor Marketplace Platform</p>
            <div style={{ marginTop: '16px' }}>
              <ThemeToggle theme={theme} toggleTheme={toggleTheme} />
            </div>
          </div>

          {showForgotPassword ? (
            showResetPassword ? (
              // Reset Password Form
              <form onSubmit={handleResetPassword} className="login-form">
                <h2>Reset Password</h2>
                {resetMessage && <div className={resetMessage.includes('successfully') ? 'success-msg' : 'error-msg'}>{resetMessage}</div>}
                <div className="form-group">
                  <label>New Password</label>
                  <div className="password-input-wrapper">
                    <input
                      type={showResetNewPassword ? "text" : "password"}
                      value={resetForm.password}
                      onChange={e => setResetForm({...resetForm, password: e.target.value})}
                      required
                      minLength={6}
                    />
                    <button type="button" className="password-toggle" onClick={() => setShowResetNewPassword(!showResetNewPassword)}>
                      {showResetNewPassword ? "🙈" : "👁"}
                    </button>
                  </div>
                  {resetForm.password && (
                    <div className="password-strength">
                      <div className="strength-bars">
                        {[1, 2, 3, 4, 5].map(level => (
                          <div
                            key={level}
                            className={`strength-bar ${level <= getPasswordStrength(resetForm.password).score ? 'active' : ''}`}
                            style={{ backgroundColor: level <= getPasswordStrength(resetForm.password).score ? getPasswordStrength(resetForm.password).color : '' }}
                          />
                        ))}
                      </div>
                      <span className="strength-label" style={{ color: getPasswordStrength(resetForm.password).color }}>
                        {getPasswordStrength(resetForm.password).label}
                      </span>
                    </div>
                  )}
                </div>
                <div className="form-group">
                  <label>Confirm Password</label>
                  <div className="password-input-wrapper">
                    <input
                      type={showResetNewPassword ? "text" : "password"}
                      value={resetForm.confirmPassword}
                      onChange={e => setResetForm({...resetForm, confirmPassword: e.target.value})}
                      required
                    />
                  </div>
                  {resetForm.confirmPassword && (
                    <div className={`password-match ${resetForm.password === resetForm.confirmPassword ? 'match' : 'no-match'}`}>
                      {resetForm.password === resetForm.confirmPassword ? '✓ Passwords match' : '✗ Passwords do not match'}
                    </div>
                  )}
                </div>
                <button type="submit" className="login-btn" disabled={resetLoading}>
                  {resetLoading ? <><span className="spinner"></span> Resetting...</> : 'Reset Password'}
                </button>
                <p className="switch-auth"><button type="button" onClick={backToLogin}>Back to Login</button></p>
              </form>
            ) : (
              // Forgot Password Form
              <form onSubmit={handleForgotPassword} className="login-form">
                <h2>Forgot Password</h2>
                <p className="form-description">Enter your email address and we'll send you a link to reset your password.</p>
                {forgotMessage && (
                  <div className={forgotMessage.includes('generated') ? 'success-msg' : 'info-msg'}>
                    {forgotMessage}
                  </div>
                )}
                {resetToken && (
                  <div className="reset-token-box">
                    <p>Demo Mode: Use this token to reset your password</p>
                    <code>{resetToken}</code>
                    <button type="button" className="login-btn" onClick={goToResetPassword} style={{marginTop: '15px'}}>
                      Reset Password Now
                    </button>
                  </div>
                )}
                {!resetToken && (
                  <>
                    <div className="form-group">
                      <label>Email</label>
                      <input type="email" value={forgotEmail} onChange={e => setForgotEmail(e.target.value)} required />
                    </div>
                    <button type="submit" className="login-btn" disabled={forgotLoading}>
                      {forgotLoading ? <><span className="spinner"></span> Sending...</> : 'Send Reset Link'}
                    </button>
                  </>
                )}
                <p className="switch-auth"><button type="button" onClick={backToLogin}>Back to Login</button></p>
              </form>
            )
          ) : showRegister ? (
            <form onSubmit={handleRegister} className="login-form">
              <h2>Create Account</h2>
              {loginError && <div className="error-msg">{loginError}</div>}
              <div className="form-group">
                <label>Name</label>
                <input type="text" value={registerForm.name} onChange={e => setRegisterForm({...registerForm, name: e.target.value})} required />
              </div>
              <div className="form-group">
                <label>Email</label>
                <input type="email" value={registerForm.email} onChange={e => setRegisterForm({...registerForm, email: e.target.value})} required />
              </div>
              <div className="form-group">
                <label>Phone</label>
                <input type="tel" value={registerForm.phone} onChange={e => setRegisterForm({...registerForm, phone: e.target.value})} />
              </div>
              <div className="form-group">
                <label>Password</label>
                <div className="password-input-wrapper">
                  <input type={showRegisterPassword ? "text" : "password"} value={registerForm.password} onChange={e => setRegisterForm({...registerForm, password: e.target.value})} required />
                  <button type="button" className="password-toggle" onClick={() => setShowRegisterPassword(!showRegisterPassword)}>
                    {showRegisterPassword ? "🙈" : "👁"}
                  </button>
                </div>
                {registerForm.password && (
                  <div className="password-strength">
                    <div className="strength-bars">
                      {[1, 2, 3, 4, 5].map(level => (
                        <div
                          key={level}
                          className={`strength-bar ${level <= getPasswordStrength(registerForm.password).score ? 'active' : ''}`}
                          style={{ backgroundColor: level <= getPasswordStrength(registerForm.password).score ? getPasswordStrength(registerForm.password).color : '' }}
                        />
                      ))}
                    </div>
                    <span className="strength-label" style={{ color: getPasswordStrength(registerForm.password).color }}>
                      {getPasswordStrength(registerForm.password).label}
                    </span>
                  </div>
                )}
              </div>
              <button type="submit" className="login-btn" disabled={registerLoading}>
                {registerLoading ? <><span className="spinner"></span> Registering...</> : 'Register'}
              </button>
              <p className="switch-auth">Already have an account? <button type="button" onClick={() => setShowRegister(false)}>Login</button></p>
            </form>
          ) : (
            <form onSubmit={handleLogin} className="login-form">
              <h2>Login</h2>
              {loginError && <div className="error-msg">{loginError}</div>}
              <div className="form-group">
                <label>Email</label>
                <input type="email" value={loginForm.email} onChange={e => setLoginForm({...loginForm, email: e.target.value})} required />
              </div>
              <div className="form-group">
                <label>Password</label>
                <div className="password-input-wrapper">
                  <input type={showLoginPassword ? "text" : "password"} value={loginForm.password} onChange={e => setLoginForm({...loginForm, password: e.target.value})} required />
                  <button type="button" className="password-toggle" onClick={() => setShowLoginPassword(!showLoginPassword)}>
                    {showLoginPassword ? "🙈" : "👁"}
                  </button>
                </div>
              </div>
              <div className="login-options">
                <label className="remember-me">
                  <input type="checkbox" checked={rememberMe} onChange={e => setRememberMe(e.target.checked)} />
                  <span>Remember me</span>
                </label>
                <button type="button" className="forgot-link" onClick={() => setShowForgotPassword(true)}>Forgot Password?</button>
              </div>
              <button type="submit" className="login-btn" disabled={loginLoading}>
                {loginLoading ? <><span className="spinner"></span> Logging in...</> : 'Login'}
              </button>
              <p className="switch-auth">New here? <button type="button" onClick={() => setShowRegister(true)}>Create Account</button></p>
            </form>
          )}

          {!showForgotPassword && (
            <div className="demo-accounts">
              <h3>Demo Accounts</h3>
              <div className="demo-list">
                <button onClick={() => setLoginForm({ email: 'superadmin@kommandai.com', password: 'qwert12345' })}>Super Admin</button>
                <button onClick={() => setLoginForm({ email: 'admin@kommandai.com', password: 'qwert12345' })}>Admin</button>
                <button onClick={() => setLoginForm({ email: 'customer@kommandai.com', password: 'qwert12345' })}>Customer</button>
              </div>
            </div>
          )}
        </div>
      </div>
    )
  }

  // ============== SUPER ADMIN VIEW ==============
  if (user.role === 'super_admin') {
    return (
      <div className="super-admin-app">
        <header className="super-header">
          <div className="header-left">
            <h1>KommandAI Platform</h1>
            <p>Super Admin Dashboard</p>
          </div>
          <div className="header-right">
            <ThemeToggle theme={theme} toggleTheme={toggleTheme} />
            <span className="user-info">{user.name}</span>
            <button className="logout-btn" onClick={logout}>Logout</button>
          </div>
        </header>

        <div className="command-panel">
          {quickActions.length > 0 && (
            <div className="quick-actions">
              {quickActions.map((action, i) => (
                <button key={i} className="quick-action-btn" onClick={() => handleQuickAction(action)} title={action.command}>
                  <span className="qa-label">{action.label}</span>
                  {action.label_hi && <span className="qa-label-hi">{action.label_hi}</span>}
                </button>
              ))}
            </div>
          )}
          <form onSubmit={sendCommand} className="command-form">
            <div className="command-input-wrapper">
              <span className="command-icon">🤖</span>
              <input
                type="text"
                value={command}
                onChange={e => setCommand(e.target.value)}
                onKeyDown={handleCommandKeyDown}
                onFocus={() => command.trim() && suggestions.length > 0 && setShowSuggestions(true)}
                onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
                placeholder={isListening ? "🎤 Listening... speak now" : "Type or speak... (Hindi/English दोनों चलेगा)"}
                disabled={isProcessing}
                className={`command-input ${isListening ? 'listening' : ''}`}
              />
              <VoiceButton
                isListening={isListening}
                isSupported={voiceSupported}
                onClick={toggleListening}
                disabled={isProcessing}
              />
              <button type="submit" disabled={isProcessing || !command.trim()} className="command-btn">{isProcessing ? '...' : 'Go'}</button>
            </div>
            {showSuggestions && suggestions.length > 0 && (
              <div className="suggestions-dropdown">
                {suggestions.map((s, i) => (
                  <div
                    key={i}
                    className={`suggestion-item ${selectedSuggestion === i ? 'selected' : ''}`}
                    onClick={() => handleSuggestionSelect(s)}
                  >
                    <div className="suggestion-header">
                      <span className="suggestion-category">{s.category} {s.category_hi && `| ${s.category_hi}`}</span>
                      <span className="suggestion-command">{s.description}</span>
                    </div>
                    <div className="suggestion-desc-hi">{s.description_hi}</div>
                    <div className="suggestion-example">{s.examples?.[0] || s.template}</div>
                    {s.examples_hi?.[0] && <div className="suggestion-example-hi">{s.examples_hi[0]}</div>}
                  </div>
                ))}
              </div>
            )}
          </form>
        </div>

        <div className="stats-grid platform-stats">
          <div className="stat-card primary"><div className="stat-value">{platformStats.total_shops || 0}</div><div className="stat-label">Total Shops</div></div>
          <div className="stat-card success"><div className="stat-value">{platformStats.verified_shops || 0}</div><div className="stat-label">Verified Shops</div></div>
          <div className="stat-card"><div className="stat-value">{platformStats.total_shop_owners || 0}</div><div className="stat-label">Shop Owners</div></div>
          <div className="stat-card"><div className="stat-value">{platformStats.total_customers || 0}</div><div className="stat-label">Customers</div></div>
          <div className="stat-card success"><div className="stat-value">${platformStats.platform_revenue?.toLocaleString() || 0}</div><div className="stat-label">Total Revenue</div></div>
          <div className="stat-card"><div className="stat-value">{platformStats.total_users || 0}</div><div className="stat-label">Total Users</div></div>
        </div>

        <div className="tabs">
          {['overview', 'shops', 'users', 'categories'].map(tab => (
            <button key={tab} className={`tab ${superAdminTab === tab ? 'active' : ''}`} onClick={() => setSuperAdminTab(tab)}>
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {superAdminTab === 'overview' && (
          <div className="dashboard-grid">
            <div className="panel">
              <h2>Pending Verification</h2>
              <div className="shop-list">
                {allShops.filter(s => !s.is_verified).slice(0, 5).map(shop => (
                  <div key={shop.id} className="shop-item">
                    <div className="shop-info"><strong>{shop.name}</strong><span>{shop.owner_email}</span><span className="city">{shop.city}</span></div>
                    <div className="shop-actions"><button className="verify-btn" onClick={() => verifyShop(shop.id)}>Verify</button></div>
                  </div>
                ))}
                {allShops.filter(s => !s.is_verified).length === 0 && <p className="empty">No shops pending verification</p>}
              </div>
            </div>
            <div className="panel logs-panel">
              <h2>Activity Log</h2>
              <div className="log-list">
                {logs.slice(0, 10).map((log, i) => (
                  <div key={i} className={`log-item ${log.type}`}><span className="log-time">{log.time}</span><span>{log.message}</span></div>
                ))}
              </div>
            </div>
          </div>
        )}

        {superAdminTab === 'shops' && (
          <div className="tab-content">
            {showShopForm ? (
              <div className="form-panel">
                <h2>{editingShop ? 'Edit Shop' : 'Register New Shop'}</h2>
                <form onSubmit={submitShopForm}>
                  <div className="form-section">
                    <h3>Shop Details</h3>
                    <div className="form-group">
                      <label>Shop Name *</label>
                      <input type="text" value={shopForm.name} onChange={e => setShopForm({...shopForm, name: e.target.value})} required />
                    </div>
                    <div className="form-group">
                      <label>Description</label>
                      <textarea value={shopForm.description} onChange={e => setShopForm({...shopForm, description: e.target.value})} />
                    </div>
                    <div className="form-group">
                      <label>Category</label>
                      <select value={shopForm.category_id} onChange={e => setShopForm({...shopForm, category_id: e.target.value})}>
                        <option value="">Select Category</option>
                        {shopCategories.map(cat => <option key={cat.id} value={cat.id}>{cat.name}</option>)}
                      </select>
                    </div>
                  </div>
                  <div className="form-section">
                    <h3>Owner Information</h3>
                    <div className="form-group">
                      <label>Owner Name</label>
                      <input type="text" value={shopForm.owner_name} onChange={e => setShopForm({...shopForm, owner_name: e.target.value})} />
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>Owner Email</label>
                        <input type="email" value={shopForm.owner_email} onChange={e => setShopForm({...shopForm, owner_email: e.target.value})} />
                      </div>
                      <div className="form-group">
                        <label>Owner Phone</label>
                        <input type="text" value={shopForm.owner_phone} onChange={e => setShopForm({...shopForm, owner_phone: e.target.value})} />
                      </div>
                    </div>
                  </div>
                  <div className="form-section">
                    <h3>Location</h3>
                    <div className="form-group">
                      <label>Address</label>
                      <textarea value={shopForm.address} onChange={e => setShopForm({...shopForm, address: e.target.value})} />
                    </div>
                    <div className="form-row">
                      <div className="form-group">
                        <label>City</label>
                        <input type="text" value={shopForm.city} onChange={e => setShopForm({...shopForm, city: e.target.value})} />
                      </div>
                      <div className="form-group">
                        <label>Pincode</label>
                        <input type="text" value={shopForm.pincode} onChange={e => setShopForm({...shopForm, pincode: e.target.value})} />
                      </div>
                    </div>
                    <div className="form-group">
                      <label>GST Number</label>
                      <input type="text" value={shopForm.gst_number} onChange={e => setShopForm({...shopForm, gst_number: e.target.value})} placeholder="Optional" />
                    </div>
                  </div>
                  <div className="form-actions">
                    <button type="submit" className="submit-btn">{editingShop ? 'Update Shop' : 'Register Shop'}</button>
                    <button type="button" className="cancel-btn" onClick={resetShopForm}>Cancel</button>
                  </div>
                </form>
              </div>
            ) : (
              <div style={{display: 'flex', justifyContent: 'flex-end', marginBottom: '15px'}}>
                <button className="submit-btn" onClick={() => setShowShopForm(true)}>+ Register New Shop</button>
              </div>
            )}
            <div className="data-panel">
              <SearchFilterBar search={shopSearch} setSearch={setShopSearch} placeholder="Search shops by name, email, city..." />
              <h2>All Shops ({allShops.length})</h2>
              <div className="data-table">
                <table>
                  <thead>
                    <tr><th>Shop Name</th><th>Owner</th><th>City</th><th>Orders</th><th>Revenue</th><th>Status</th><th>Actions</th></tr>
                  </thead>
                  <tbody>
                    {allShops.map(shop => (
                      <tr key={shop.id} className={!shop.is_active ? 'suspended' : ''}>
                        <td><div className="shop-cell"><strong>{shop.name}</strong>{shop.is_verified && <span className="verified-badge">✓</span>}</div></td>
                        <td>{shop.owner_email || '-'}</td>
                        <td>{shop.city || '-'}</td>
                        <td>{shop.total_orders}</td>
                        <td>${shop.total_revenue?.toLocaleString()}</td>
                        <td><span className={`status ${shop.is_active ? 'active' : 'suspended'}`}>{shop.is_active ? 'Active' : 'Suspended'}</span></td>
                        <td>
                          <button className="edit-btn" onClick={() => startEditShop(shop)}>Edit</button>
                          {!shop.is_verified && <button className="verify-btn" onClick={() => verifyShop(shop.id)}>Verify</button>}
                          {shop.is_active ? <button className="suspend-btn" onClick={() => suspendShop(shop.id)}>Suspend</button> : <button className="activate-btn" onClick={() => activateShop(shop.id)}>Activate</button>}
                          <button className="delete-btn" onClick={() => deleteShop(shop.id)}>Delete</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <LoadMoreButton hasMore={allShopsHasMore} isLoading={isLoading} onClick={() => fetchAllShops(allShopsPage + 1)} />
            </div>
          </div>
        )}

        {superAdminTab === 'users' && (
          <div className="data-panel">
            <SearchFilterBar
              search={userSearch}
              setSearch={setUserSearch}
              placeholder="Search users by name or email..."
              filters={
                <select value={userRoleFilter} onChange={e => setUserRoleFilter(e.target.value)} className="filter-select">
                  <option value="">All Roles</option>
                  <option value="super_admin">Super Admin</option>
                  <option value="admin">Admin</option>
                  <option value="customer">Customer</option>
                </select>
              }
            />
            <h2>All Users ({allUsers.length})</h2>
            <div className="data-table">
              <table>
                <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Phone</th><th>Status</th><th>Created</th></tr></thead>
                <tbody>
                  {allUsers.map(u => (
                    <tr key={u.id}>
                      <td>{u.name}</td>
                      <td>{u.email}</td>
                      <td><span className={`role ${u.role}`}>{u.role}</span></td>
                      <td>{u.phone || '-'}</td>
                      <td><span className={`status ${u.is_active ? 'active' : 'inactive'}`}>{u.is_active ? 'Active' : 'Inactive'}</span></td>
                      <td>{new Date(u.created_at).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <LoadMoreButton hasMore={usersHasMore} isLoading={isLoading} onClick={() => fetchAllUsers(usersPage + 1)} />
          </div>
        )}

        {superAdminTab === 'categories' && (
          <div className="data-panel">
            {selectedAdminCategory && categoryInfo ? (
              // Category Detail View
              <div className="category-detail-view">
                <div className="category-detail-header">
                  <button className="back-btn" onClick={closeCategoryDetail}>← Back to Categories</button>
                  <div className="category-title">
                    <span className="cat-icon-large">{categoryInfo.icon}</span>
                    <div>
                      <h2>{categoryInfo.name}</h2>
                      <p>{categoryInfo.description}</p>
                    </div>
                  </div>
                </div>

                <div className="category-stats-bar">
                  <div className="cat-stat"><span className="cat-stat-value">{categoryShops.length}</span><span className="cat-stat-label">Total Shops</span></div>
                  <div className="cat-stat"><span className="cat-stat-value">{categoryShops.filter(s => s.is_active).length}</span><span className="cat-stat-label">Active</span></div>
                  <div className="cat-stat"><span className="cat-stat-value">{categoryShops.filter(s => s.is_verified).length}</span><span className="cat-stat-label">Verified</span></div>
                  <div className="cat-stat success"><span className="cat-stat-value">₹{categoryShops.reduce((sum, s) => sum + (s.stats?.total_revenue || 0), 0).toLocaleString()}</span><span className="cat-stat-label">Total Revenue</span></div>
                  <div className="cat-stat profit"><span className="cat-stat-value">₹{categoryShops.reduce((sum, s) => sum + (s.stats?.total_profit || 0), 0).toLocaleString()}</span><span className="cat-stat-label">Total Profit</span></div>
                </div>

                <h3>Shops in {categoryInfo.name}</h3>
                <div className="data-table">
                  <table>
                    <thead>
                      <tr>
                        <th>Shop Name</th>
                        <th>Owner</th>
                        <th>City</th>
                        <th>Rating</th>
                        <th>Orders</th>
                        <th>Revenue</th>
                        <th>Profit</th>
                        <th>Margin</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {categoryShops.map(shop => (
                        <tr key={shop.id} className={!shop.is_active ? 'suspended' : ''}>
                          <td>
                            <div className="shop-cell">
                              <strong>{shop.name}</strong>
                              {shop.is_verified && <span className="verified-badge">✓</span>}
                            </div>
                          </td>
                          <td>
                            <div className="owner-cell">
                              <span className="owner-name">{shop.owner_name || '-'}</span>
                              <span className="owner-email">{shop.owner_email || '-'}</span>
                            </div>
                          </td>
                          <td>{shop.city || '-'}</td>
                          <td><span className="rating-badge">★ {shop.rating?.toFixed(1) || '-'}</span></td>
                          <td>{shop.stats?.total_orders || 0}</td>
                          <td className="revenue">₹{(shop.stats?.total_revenue || 0).toLocaleString()}</td>
                          <td className={`profit ${(shop.stats?.total_profit || 0) >= 0 ? 'positive' : 'negative'}`}>
                            ₹{(shop.stats?.total_profit || 0).toLocaleString()}
                          </td>
                          <td className={`margin ${(shop.stats?.profit_margin || 0) > 20 ? 'good' : (shop.stats?.profit_margin || 0) > 0 ? 'ok' : 'low'}`}>
                            {shop.stats?.profit_margin || 0}%
                          </td>
                          <td>
                            <span className={`status ${shop.is_active ? 'active' : 'suspended'}`}>
                              {shop.is_active ? 'Active' : 'Suspended'}
                            </span>
                          </td>
                          <td>
                            <button className="view-btn" onClick={() => fetchShopDetailStats(shop.id)} disabled={loadingShopDetail}>
                              {loadingShopDetail ? '...' : 'View Details'}
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {categoryShops.length === 0 && <p className="empty">No shops in this category</p>}
              </div>
            ) : (
              // Categories Grid
              <>
                <h2>Shop Categories</h2>
                <p className="subtitle">Click on a category to view all shops and their performance metrics</p>
                <div className="categories-admin clickable">
                  {shopCategories.map(cat => (
                    <div key={cat.id} className="category-admin-card" onClick={() => openCategoryDetail(cat.id)}>
                      <span className="cat-icon">{cat.icon}</span>
                      <div className="cat-info">
                        <h3>{cat.name}</h3>
                        <p>{cat.description}</p>
                        <span className="shop-count">{cat.shop_count} shops</span>
                      </div>
                      <span className="view-arrow">→</span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        )}

        {/* Shop Detail Modal */}
        {showShopDetailModal && shopDetailStats && (
          <div className="modal-overlay" onClick={closeShopDetailModal}>
            <div className="shop-detail-modal" onClick={e => e.stopPropagation()}>
              <button className="modal-close" onClick={closeShopDetailModal}>×</button>

              <div className="shop-modal-header">
                <div className="shop-info-main">
                  <span className="cat-icon-large">{shopDetailStats.shop.category_icon || '🏪'}</span>
                  <div>
                    <h2>{shopDetailStats.shop.name}</h2>
                    <p className="shop-category">{shopDetailStats.shop.category || 'Uncategorized'}</p>
                    <div className="shop-badges">
                      {shopDetailStats.shop.is_verified && <span className="badge verified">Verified</span>}
                      <span className={`badge ${shopDetailStats.shop.is_active ? 'active' : 'suspended'}`}>
                        {shopDetailStats.shop.is_active ? 'Active' : 'Suspended'}
                      </span>
                      <span className="badge rating">★ {shopDetailStats.shop.rating?.toFixed(1)}</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="shop-modal-stats">
                <div className="stats-section">
                  <h3>Financial Overview</h3>
                  <div className="stats-grid-modal">
                    <div className="stat-box revenue">
                      <span className="stat-label">Total Revenue</span>
                      <span className="stat-value">₹{shopDetailStats.financials.total_revenue.toLocaleString()}</span>
                    </div>
                    <div className="stat-box cost">
                      <span className="stat-label">Total Cost</span>
                      <span className="stat-value">₹{shopDetailStats.financials.total_cost.toLocaleString()}</span>
                    </div>
                    <div className="stat-box profit">
                      <span className="stat-label">Total Profit</span>
                      <span className="stat-value">₹{shopDetailStats.financials.total_profit.toLocaleString()}</span>
                    </div>
                    <div className="stat-box margin">
                      <span className="stat-label">Profit Margin</span>
                      <span className="stat-value">{shopDetailStats.financials.profit_margin}%</span>
                    </div>
                    <div className="stat-box">
                      <span className="stat-label">Total Orders</span>
                      <span className="stat-value">{shopDetailStats.total_orders}</span>
                    </div>
                    <div className="stat-box">
                      <span className="stat-label">Avg Order Value</span>
                      <span className="stat-value">₹{shopDetailStats.financials.avg_order_value.toLocaleString()}</span>
                    </div>
                  </div>
                </div>

                <div className="stats-row">
                  <div className="stats-section half">
                    <h3>Today's Performance</h3>
                    <div className="today-stats">
                      <div><span>Orders:</span><strong>{shopDetailStats.today.orders}</strong></div>
                      <div><span>Revenue:</span><strong>₹{shopDetailStats.today.revenue.toLocaleString()}</strong></div>
                      <div><span>Profit:</span><strong className="profit positive">₹{shopDetailStats.today.profit.toLocaleString()}</strong></div>
                    </div>
                  </div>
                  <div className="stats-section half">
                    <h3>This Month</h3>
                    <div className="month-stats">
                      <div><span>Orders:</span><strong>{shopDetailStats.this_month.orders}</strong></div>
                      <div><span>Revenue:</span><strong>₹{shopDetailStats.this_month.revenue.toLocaleString()}</strong></div>
                      <div><span>Growth:</span><strong className={shopDetailStats.this_month.revenue_growth >= 0 ? 'positive' : 'negative'}>
                        {shopDetailStats.this_month.revenue_growth >= 0 ? '+' : ''}{shopDetailStats.this_month.revenue_growth}%
                      </strong></div>
                    </div>
                  </div>
                </div>

                <div className="stats-section">
                  <h3>Inventory</h3>
                  <div className="inventory-stats">
                    <div><span>Total Products:</span><strong>{shopDetailStats.products.total}</strong></div>
                    <div><span>Active:</span><strong>{shopDetailStats.products.active}</strong></div>
                    <div><span>Low Stock:</span><strong className="warning">{shopDetailStats.products.low_stock}</strong></div>
                    <div><span>Out of Stock:</span><strong className="danger">{shopDetailStats.products.out_of_stock}</strong></div>
                    <div><span>Inventory Value:</span><strong>₹{shopDetailStats.products.inventory_value.toLocaleString()}</strong></div>
                  </div>
                </div>

                {shopDetailStats.top_products.length > 0 && (
                  <div className="stats-section">
                    <h3>Top Selling Products</h3>
                    <table className="top-products-table">
                      <thead>
                        <tr><th>Product</th><th>Units Sold</th><th>Revenue</th><th>Profit</th></tr>
                      </thead>
                      <tbody>
                        {shopDetailStats.top_products.map((p, i) => (
                          <tr key={i}>
                            <td>{p.name}</td>
                            <td>{p.units_sold}</td>
                            <td>₹{p.revenue.toLocaleString()}</td>
                            <td className="profit positive">₹{p.profit.toLocaleString()}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                <div className="stats-section">
                  <h3>Owner Information</h3>
                  <div className="owner-info">
                    <div><span>Name:</span><strong>{shopDetailStats.shop.owner_name || '-'}</strong></div>
                    <div><span>Email:</span><strong>{shopDetailStats.shop.owner_email || '-'}</strong></div>
                    <div><span>Phone:</span><strong>{shopDetailStats.shop.owner_phone || '-'}</strong></div>
                    <div><span>Address:</span><strong>{shopDetailStats.shop.address || '-'}, {shopDetailStats.shop.city || ''} {shopDetailStats.shop.pincode || ''}</strong></div>
                  </div>
                </div>
              </div>

              <div className="modal-actions">
                {!shopDetailStats.shop.is_verified && (
                  <button className="verify-btn" onClick={() => { verifyShop(shopDetailStats.shop.id); closeShopDetailModal(); }}>Verify Shop</button>
                )}
                {shopDetailStats.shop.is_active ? (
                  <button className="suspend-btn" onClick={() => { suspendShop(shopDetailStats.shop.id); closeShopDetailModal(); }}>Suspend Shop</button>
                ) : (
                  <button className="activate-btn" onClick={() => { activateShop(shopDetailStats.shop.id); closeShopDetailModal(); }}>Activate Shop</button>
                )}
                <button className="edit-btn" onClick={() => { startEditShop(shopDetailStats.shop); closeShopDetailModal(); }}>Edit Shop</button>
              </div>
            </div>
          </div>
        )}
      </div>
    )
  }

  // ============== SHOP OWNER (ADMIN) VIEW ==============
  if (user.role === 'admin') {
    return (
      <div className="admin-app">
        <header className="admin-header">
          <div className="header-left">
            <h1>Shop Dashboard</h1>
            <p>Manage your shop</p>
          </div>
          <div className="header-right">
            <div className="connection-status"><span className={`dot ${isConnected ? 'connected' : ''}`}></span>{isConnected ? 'Live' : 'Offline'}</div>
            <ThemeToggle theme={theme} toggleTheme={toggleTheme} />
            <span className="user-info">{user.name}</span>
            <button className="logout-btn" onClick={logout}>Logout</button>
          </div>
        </header>

        <div className="command-panel">
          {quickActions.length > 0 && (
            <div className="quick-actions">
              {quickActions.map((action, i) => (
                <button key={i} className="quick-action-btn" onClick={() => handleQuickAction(action)} title={action.command}>
                  <span className="qa-label">{action.label}</span>
                  {action.label_hi && <span className="qa-label-hi">{action.label_hi}</span>}
                </button>
              ))}
            </div>
          )}
          <form onSubmit={sendCommand} className="command-form">
            <div className="command-input-wrapper">
              <span className="command-icon">🤖</span>
              <input
                type="text"
                value={command}
                onChange={e => setCommand(e.target.value)}
                onKeyDown={handleCommandKeyDown}
                onFocus={() => command.trim() && suggestions.length > 0 && setShowSuggestions(true)}
                onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
                placeholder={isListening ? "🎤 सुन रहा हूं... बोलिए" : "बोलो या टाइप करो... (Hindi/English दोनों चलेगा)"}
                disabled={isProcessing}
                className={`command-input ${isListening ? 'listening' : ''}`}
              />
              <VoiceButton
                isListening={isListening}
                isSupported={voiceSupported}
                onClick={toggleListening}
                disabled={isProcessing}
              />
              <button type="submit" disabled={isProcessing || !command.trim()} className="command-btn">{isProcessing ? '...' : 'Go'}</button>
            </div>
            {showSuggestions && suggestions.length > 0 && (
              <div className="suggestions-dropdown">
                {suggestions.map((s, i) => (
                  <div
                    key={i}
                    className={`suggestion-item ${selectedSuggestion === i ? 'selected' : ''}`}
                    onClick={() => handleSuggestionSelect(s)}
                  >
                    <div className="suggestion-header">
                      <span className="suggestion-category">{s.category} {s.category_hi && `| ${s.category_hi}`}</span>
                      <span className="suggestion-command">{s.description}</span>
                    </div>
                    <div className="suggestion-desc-hi">{s.description_hi}</div>
                    <div className="suggestion-example">{s.examples?.[0] || s.template}</div>
                    {s.examples_hi?.[0] && <div className="suggestion-example-hi">{s.examples_hi[0]}</div>}
                  </div>
                ))}
              </div>
            )}
          </form>
        </div>

        <div className="stats-grid">
          <div className="stat-card"><div className="stat-value">{dashboardStats.total_products || 0}</div><div className="stat-label">Products</div></div>
          <div className="stat-card success"><div className="stat-value">${dashboardStats.total_revenue?.toLocaleString() || 0}</div><div className="stat-label">Total Revenue</div></div>
          <div className="stat-card"><div className="stat-value">{dashboardStats.total_orders || 0}</div><div className="stat-label">Orders</div></div>
          <div className="stat-card warning"><div className="stat-value">{dashboardStats.pending_orders || 0}</div><div className="stat-label">Pending</div></div>
          <div className="stat-card danger"><div className="stat-value">{dashboardStats.low_stock_count || 0}</div><div className="stat-label">Low Stock</div></div>
          <div className="stat-card"><div className="stat-value">${dashboardStats.inventory_value?.toLocaleString() || 0}</div><div className="stat-label">Inventory Value</div></div>
        </div>

        <div className="tabs">
          {['dashboard', 'products', 'orders'].map(tab => (
            <button key={tab} className={`tab ${activeTab === tab ? 'active' : ''}`} onClick={() => setActiveTab(tab)}>
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {activeTab === 'dashboard' && (
          <div className="dashboard-grid">
            <div className="panel alerts-panel">
              <h2>Low Stock Alerts</h2>
              {lowStockProducts.length === 0 ? <p className="empty">All products are well stocked</p> : (
                <div className="alert-list">
                  {lowStockProducts.map(p => (
                    <div key={p.id} className="alert-item">
                      <span className="alert-name">{p.name}</span>
                      <span className="alert-sku">{p.sku}</span>
                      <span className={`alert-qty ${p.quantity === 0 ? 'zero' : ''}`}>{p.quantity} left</span>
                      <button onClick={() => editProduct(products.find(prod => prod.id === p.id))}>Restock</button>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="panel logs-panel">
              <h2>Recent Activity</h2>
              <div className="log-list">
                {logs.slice(0, 10).map((log, i) => (
                  <div key={i} className={`log-item ${log.type}`}><span className="log-time">{log.time}</span><span>{log.message}</span></div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'products' && (
          <div className="tab-content">
            <div className="form-panel">
              <h2>{editingProduct ? 'Edit Product' : 'Add New Product'}</h2>
              <form onSubmit={editingProduct ? updateProduct : createProduct}>
                <div className="form-section">
                  <div className="form-group"><label>Product Name *</label><input type="text" value={productForm.name} onChange={e => setProductForm({...productForm, name: e.target.value})} required /></div>
                  <div className="form-row">
                    <div className="form-group"><label>Brand</label><input type="text" value={productForm.brand} onChange={e => setProductForm({...productForm, brand: e.target.value})} /></div>
                    <div className="form-group"><label>SKU</label><input type="text" value={productForm.sku} onChange={e => setProductForm({...productForm, sku: e.target.value})} /></div>
                  </div>
                  <div className="form-group"><label>Description</label><textarea value={productForm.description} onChange={e => setProductForm({...productForm, description: e.target.value})} /></div>
                </div>
                <div className="form-section">
                  <h3>Pricing</h3>
                  <div className="form-row">
                    <div className="form-group"><label>Cost Price</label><input type="number" step="0.01" value={productForm.cost_price} onChange={e => setProductForm({...productForm, cost_price: e.target.value})} placeholder="Your purchase cost" /></div>
                    <div className="form-group"><label>MRP / Selling Price *</label><input type="number" step="0.01" value={productForm.price} onChange={e => setProductForm({...productForm, price: e.target.value})} required /></div>
                    <div className="form-group"><label>Min Bargain Price</label><input type="number" step="0.01" value={productForm.min_price} onChange={e => setProductForm({...productForm, min_price: e.target.value})} placeholder="Lowest acceptable price" /></div>
                  </div>
                  {productForm.cost_price && productForm.price && (
                    <div className="pricing-summary">
                      <span className="profit-margin">Margin: {(((parseFloat(productForm.price) - parseFloat(productForm.cost_price)) / parseFloat(productForm.cost_price)) * 100).toFixed(1)}%</span>
                      <span className="profit-amount">Profit: ₹{(parseFloat(productForm.price) - parseFloat(productForm.cost_price)).toFixed(2)}</span>
                    </div>
                  )}
                </div>
                <div className="form-section">
                  <h3>Inventory</h3>
                  <div className="form-row">
                    <div className="form-group"><label>Quantity *</label><input type="number" value={productForm.quantity} onChange={e => setProductForm({...productForm, quantity: e.target.value})} required /></div>
                    <div className="form-group"><label>Low Stock Alert</label><input type="number" value={productForm.min_stock_level} onChange={e => setProductForm({...productForm, min_stock_level: e.target.value})} /></div>
                  </div>
                </div>
                <div className="form-group"><label>Tags (comma-separated)</label><input type="text" value={productForm.tags} onChange={e => setProductForm({...productForm, tags: e.target.value})} placeholder="e.g. lipstick, makeup" /></div>
                <div className="form-actions">
                  {editingProduct && <button type="button" className="cancel-btn" onClick={resetProductForm}>Cancel</button>}
                  <button type="submit" className="submit-btn">{editingProduct ? 'Update' : 'Add Product'}</button>
                </div>
              </form>
            </div>

            <div className="data-panel">
              <SearchFilterBar search={adminProductSearch} setSearch={setAdminProductSearch} placeholder="Search products..." />
              <h2>Products ({products.length})</h2>
              <div className="data-table">
                <table>
                  <thead><tr><th>Product</th><th>SKU</th><th>Cost</th><th>MRP</th><th>Min Price</th><th>Margin</th><th>Stock</th><th>Sold</th><th>Actions</th></tr></thead>
                  <tbody>
                    {products.map(p => {
                      const margin = p.cost_price && p.price ? Math.round(((p.price - p.cost_price) / p.cost_price) * 100) : null
                      return (
                        <tr key={p.id} className={!p.is_active ? 'inactive' : ''}>
                          <td><div className="product-cell"><strong>{p.name}</strong>{p.brand && <span className="brand">{p.brand}</span>}</div></td>
                          <td>{p.sku || '-'}</td>
                          <td className="cost">{p.cost_price ? `₹${p.cost_price}` : '-'}</td>
                          <td className="price">₹{p.price}</td>
                          <td>{p.min_price ? `₹${p.min_price}` : '-'}</td>
                          <td className={`margin ${margin && margin > 20 ? 'good' : margin && margin > 0 ? 'ok' : 'low'}`}>
                            {margin != null ? `${margin}%` : '-'}
                          </td>
                          <td className={p.quantity <= p.min_stock_level ? 'low-stock' : ''}>{p.quantity}</td>
                          <td>{p.sold_count}</td>
                          <td>
                            <button className="edit-btn" onClick={() => editProduct(p)}>Edit</button>
                            <button className="delete-btn" onClick={() => deleteProduct(p.id)}>Delete</button>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
              <LoadMoreButton hasMore={adminProductsHasMore} isLoading={isLoading} onClick={() => fetchAdminProducts(user.shop_id, adminProductsPage + 1)} />
            </div>
          </div>
        )}

        {activeTab === 'orders' && (
          <div className="orders-panel">
            <SearchFilterBar
              search={orderSearch}
              setSearch={setOrderSearch}
              placeholder="Search orders..."
              filters={
                <select value={orderStatusFilter} onChange={e => setOrderStatusFilter(e.target.value)} className="filter-select">
                  <option value="">All Status</option>
                  <option value="pending">Pending</option>
                  <option value="confirmed">Confirmed</option>
                  <option value="shipped">Shipped</option>
                  <option value="delivered">Delivered</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              }
            />
            <h2>Orders ({orders.length})</h2>
            {orders.length === 0 ? <p className="empty">No orders found</p> : (
              <div className="data-table">
                <table>
                  <thead><tr><th>Order #</th><th>Customer</th><th>Product</th><th>Qty</th><th>MRP</th><th>Sold At</th><th>Profit</th><th>Status</th><th>Date</th></tr></thead>
                  <tbody>
                    {orders.map(o => (
                      <tr key={o.id}>
                        <td>#{o.id}</td>
                        <td>{o.customer_name}</td>
                        <td>{o.product_name}</td>
                        <td>{o.quantity}</td>
                        <td className="price">₹{o.listed_price || o.unit_price}</td>
                        <td className="price">₹{o.final_price || o.unit_price}</td>
                        <td className={`profit ${(o.profit || 0) >= 0 ? 'positive' : 'negative'}`}>
                          ₹{o.profit != null ? o.profit.toFixed(2) : '-'}
                        </td>
                        <td><span className={`status ${o.status}`}>{o.status}</span></td>
                        <td>{new Date(o.created_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            <LoadMoreButton hasMore={ordersHasMore} isLoading={isLoading} onClick={() => fetchAdminOrders(user.shop_id, ordersPage + 1)} />
          </div>
        )}
      </div>
    )
  }

  // ============== CUSTOMER VIEW ==============
  if (!selectedShopCategory && !selectedShop) {
    return (
      <div className="marketplace">
        <header className="marketplace-header">
          <div className="header-left"><h1>KommandAI Marketplace</h1><p>Shop from your favorite stores</p></div>
          <div className="header-right">
            <ThemeToggle theme={theme} toggleTheme={toggleTheme} />
            <span className="user-info">Hi, {user.name}</span>
            <button className="logout-btn" onClick={logout}>Logout</button>
          </div>
        </header>
        <div className="command-panel customer-command">
          {quickActions.length > 0 && (
            <div className="quick-actions">
              {quickActions.map((action, i) => (
                <button key={i} className="quick-action-btn" onClick={() => handleQuickAction(action)} title={action.command}>
                  <span className="qa-label">{action.label}</span>
                  {action.label_hi && <span className="qa-label-hi">{action.label_hi}</span>}
                </button>
              ))}
            </div>
          )}
          <form onSubmit={sendCommand} className="command-form">
            <div className="command-input-wrapper">
              <span className="command-icon">🔍</span>
              <input
                type="text"
                value={command}
                onChange={e => setCommand(e.target.value)}
                onKeyDown={handleCommandKeyDown}
                onFocus={() => command.trim() && suggestions.length > 0 && setShowSuggestions(true)}
                onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
                placeholder={isListening ? "🎤 सुन रहा हूं..." : "खोजो या बोलो... (Hindi/English)"}
                disabled={isProcessing}
                className={`command-input ${isListening ? 'listening' : ''}`}
              />
              <VoiceButton
                isListening={isListening}
                isSupported={voiceSupported}
                onClick={toggleListening}
                disabled={isProcessing}
              />
              <button type="submit" disabled={isProcessing || !command.trim()} className="command-btn">{isProcessing ? '...' : 'Go'}</button>
            </div>
            {showSuggestions && suggestions.length > 0 && (
              <div className="suggestions-dropdown">
                {suggestions.map((s, i) => (
                  <div
                    key={i}
                    className={`suggestion-item ${selectedSuggestion === i ? 'selected' : ''}`}
                    onClick={() => handleSuggestionSelect(s)}
                  >
                    <div className="suggestion-header">
                      <span className="suggestion-category">{s.category} {s.category_hi && `| ${s.category_hi}`}</span>
                      <span className="suggestion-command">{s.description}</span>
                    </div>
                    <div className="suggestion-desc-hi">{s.description_hi}</div>
                    <div className="suggestion-example">{s.examples?.[0] || s.template}</div>
                    {s.examples_hi?.[0] && <div className="suggestion-example-hi">{s.examples_hi[0]}</div>}
                  </div>
                ))}
              </div>
            )}
          </form>
        </div>
        <div className="categories-grid">
          {shopCategories.map(cat => (
            <div key={cat.id} className="category-card" onClick={() => setSelectedShopCategory(cat.id)}>
              <span className="category-icon">{cat.icon}</span>
              <h3>{cat.name}</h3>
              <p>{cat.description}</p>
              <span className="shop-count">{cat.shop_count} shops</span>
            </div>
          ))}
        </div>
        {cart.length > 0 && <div className="floating-cart"><span>{cart.reduce((sum, i) => sum + i.qty, 0)} items</span><span>${cartTotal.toFixed(2)}</span></div>}
      </div>
    )
  }

  if (selectedShopCategory && !selectedShop) {
    const category = shopCategories.find(c => c.id === selectedShopCategory)
    return (
      <div className="marketplace">
        <header className="marketplace-header">
          <button className="back-btn" onClick={() => { setSelectedShopCategory(null); setShops([]) }}>← Back</button>
          <h1>{category?.icon} {category?.name}</h1>
          <div className="header-right">
            <ThemeToggle theme={theme} toggleTheme={toggleTheme} />
            <span className="user-info">Hi, {user.name}</span>
            <button className="logout-btn" onClick={logout}>Logout</button>
          </div>
        </header>
        <div className="search-bar">
          <input type="text" placeholder="Search shops..." value={shopsSearch} onChange={e => setShopsSearch(e.target.value)} />
        </div>
        <div className="shops-grid">
          {shops.filter(s => !shopsSearch || s.name.toLowerCase().includes(shopsSearch.toLowerCase())).map(shop => (
            <div key={shop.id} className="shop-card" onClick={() => setSelectedShop(shop.id)}>
              <div className="shop-logo">{shop.name[0]}</div>
              <div className="shop-info">
                <h3>{shop.name}</h3>
                <p>{shop.description}</p>
                <div className="shop-meta"><span className="rating">★ {shop.rating.toFixed(1)}</span><span className="city">{shop.city}</span></div>
              </div>
            </div>
          ))}
          {shops.length === 0 && <p className="empty">No shops in this category yet</p>}
        </div>
        <LoadMoreButton hasMore={shopsHasMore} isLoading={isLoading} onClick={() => fetchShopsByCategory(selectedShopCategory, shopsPage + 1)} />
      </div>
    )
  }

  if (selectedShop) {
    const shop = shops.find(s => s.id === selectedShop)
    return (
      <div className="marketplace">
        <header className="shop-header">
          <button className="back-btn" onClick={() => { setSelectedShop(null); setShopProducts([]); setSearchQuery('') }}>← Back</button>
          <div className="shop-title"><h1>{shop?.name}</h1><span className="rating">★ {shop?.rating.toFixed(1)}</span></div>
          <div className="header-right">
            <ThemeToggle theme={theme} toggleTheme={toggleTheme} />
            <span className="user-info">Hi, {user.name}</span>
            <button className="logout-btn" onClick={logout}>Logout</button>
          </div>
        </header>
        <div className="search-bar">
          <input type="text" placeholder={`Search in ${shop?.name}...`} value={searchQuery} onChange={e => setSearchQuery(e.target.value)} />
        </div>
        <div className="products-grid">
          {shopProducts.map((p, index) => (
            <div key={p.id} className="product-card" ref={index === shopProducts.length - 1 ? lastItemRef : null}>
              <div className="product-image">
                {p.image_url ? <img src={p.image_url} alt={p.name} /> : <div className="placeholder">{p.name[0]}</div>}
                {p.compare_at_price && <span className="sale-badge">Sale</span>}
              </div>
              <div className="product-info">
                {p.brand && <span className="product-brand">{p.brand}</span>}
                <h3>{p.name}</h3>
                <div className="product-price">
                  <span className="current-price">${p.price}</span>
                  {p.compare_at_price && <span className="original-price">${p.compare_at_price}</span>}
                </div>
                <button className="add-to-cart" onClick={() => addToCart(p)} disabled={p.quantity === 0}>
                  {p.quantity === 0 ? 'Out of Stock' : 'Add to Cart'}
                </button>
              </div>
            </div>
          ))}
          {shopProducts.length === 0 && <p className="empty">No products found</p>}
        </div>
        <LoadMoreButton hasMore={productsHasMore} isLoading={isLoading} onClick={() => fetchShopProducts(selectedShop, productsPage + 1)} />
        {cart.length > 0 && (
          <div className="cart-panel">
            <h3>Cart ({cart.reduce((sum, i) => sum + i.qty, 0)} items)</h3>
            <div className="cart-items">
              {cart.map(item => (
                <div key={item.id} className="cart-item">
                  <span>{item.name} x{item.qty}</span>
                  <span>${(item.price * item.qty).toFixed(2)}</span>
                  <button onClick={() => removeFromCart(item.id)}>×</button>
                </div>
              ))}
            </div>
            <div className="cart-total"><span>Total:</span><span>${cartTotal.toFixed(2)}</span></div>
            <button className="checkout-btn">Checkout</button>
          </div>
        )}
      </div>
    )
  }

  return null
}

export default App
