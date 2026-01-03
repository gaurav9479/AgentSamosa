import { useState, useEffect, useRef } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar } from 'recharts'

const COLORS = ['#3b82f6', '#22c55e', '#f97316', '#8b5cf6', '#ef4444', '#06b6d4']

function App() {
  // Auth state
  const [user, setUser] = useState(null)
  const [loginForm, setLoginForm] = useState({ email: '', password: '' })
  const [loginError, setLoginError] = useState('')
  const [showRegister, setShowRegister] = useState(false)
  const [registerForm, setRegisterForm] = useState({ name: '', email: '', password: '', phone: '' })

  // Customer view states
  const [shopCategories, setShopCategories] = useState([])
  const [shops, setShops] = useState([])
  const [selectedShopCategory, setSelectedShopCategory] = useState(null)
  const [selectedShop, setSelectedShop] = useState(null)
  const [shopProducts, setShopProducts] = useState([])
  const [cart, setCart] = useState([])
  const [searchQuery, setSearchQuery] = useState('')

  // Admin view states
  const [activeTab, setActiveTab] = useState('dashboard')
  const [dashboardStats, setDashboardStats] = useState({})
  const [products, setProducts] = useState([])
  const [orders, setOrders] = useState([])
  const [lowStockProducts, setLowStockProducts] = useState([])
  const [categories, setCategories] = useState([])

  // Super Admin states
  const [platformStats, setPlatformStats] = useState({})
  const [allShops, setAllShops] = useState([])
  const [allUsers, setAllUsers] = useState([])
  const [superAdminTab, setSuperAdminTab] = useState('overview')

  // UI states
  const [isConnected, setIsConnected] = useState(false)
  const [logs, setLogs] = useState([])
  const [command, setCommand] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)

  // Form states
  const [productForm, setProductForm] = useState({
    name: '', description: '', brand: '', sku: '', barcode: '',
    price: '', cost_price: '', compare_at_price: '',
    quantity: '', min_stock_level: '5', category_id: '',
    tags: '', unit: 'piece', is_featured: false
  })
  const [editingProduct, setEditingProduct] = useState(null)

  const wsRef = useRef(null)

  useEffect(() => {
    connectWebSocket()
    fetchShopCategories()
    // Check for saved user
    const savedUser = localStorage.getItem('kommandai_user')
    if (savedUser) {
      setUser(JSON.parse(savedUser))
    }
    return () => { if (wsRef.current) wsRef.current.close() }
  }, [])

  useEffect(() => {
    if (selectedShopCategory) {
      fetchShopsByCategory(selectedShopCategory)
    }
  }, [selectedShopCategory])

  useEffect(() => {
    if (selectedShop) {
      fetchShopProducts(selectedShop)
    }
  }, [selectedShop])

  useEffect(() => {
    if (user) {
      if (user.role === 'super_admin') {
        fetchPlatformData()
      } else if (user.role === 'admin' && user.shop_id) {
        fetchAdminData(user.shop_id)
      }
    }
  }, [user])

  const connectWebSocket = () => {
    const ws = new WebSocket(`ws://${window.location.hostname}:8000/api/ws`)
    ws.onopen = () => { setIsConnected(true); addLog('Connected to server', 'info') }
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data)
      if (data.type === 'action_result' || data.type === 'data_update') {
        if (user?.role === 'admin' && user.shop_id) fetchAdminData(user.shop_id)
        if (user?.role === 'super_admin') fetchPlatformData()
        if (selectedShop) fetchShopProducts(selectedShop)
      }
    }
    ws.onclose = () => { setIsConnected(false); setTimeout(connectWebSocket, 3000) }
    wsRef.current = ws
  }

  // Auth functions
  const handleLogin = async (e) => {
    e.preventDefault()
    setLoginError('')
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(loginForm)
      })
      if (res.ok) {
        const data = await res.json()
        setUser(data.user)
        localStorage.setItem('kommandai_user', JSON.stringify(data.user))
        setLoginForm({ email: '', password: '' })
        addLog(`Welcome, ${data.user.name}!`, 'success')
      } else {
        const err = await res.json()
        setLoginError(err.detail || 'Login failed')
      }
    } catch (err) {
      setLoginError('Connection error')
    }
  }

  const handleRegister = async (e) => {
    e.preventDefault()
    setLoginError('')
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
    }
  }

  const logout = () => {
    setUser(null)
    localStorage.removeItem('kommandai_user')
    addLog('Logged out', 'info')
  }

  const fetchShopCategories = async () => {
    try {
      const res = await fetch('/api/shop-categories/with-counts')
      if (res.ok) setShopCategories(await res.json())
    } catch (err) { console.error('Error fetching shop categories:', err) }
  }

  const fetchShopsByCategory = async (categoryId) => {
    try {
      const res = await fetch(`/api/shops/by-category/${categoryId}`)
      if (res.ok) setShops(await res.json())
    } catch (err) { console.error('Error fetching shops:', err) }
  }

  const fetchShopProducts = async (shopId) => {
    try {
      let url = `/api/shops/${shopId}/products`
      if (searchQuery) url += `?search=${encodeURIComponent(searchQuery)}`
      const res = await fetch(url)
      if (res.ok) setShopProducts(await res.json())
    } catch (err) { console.error('Error fetching products:', err) }
  }

  const fetchAdminData = async (shopId) => {
    if (!shopId) return
    try {
      const [dashRes, prodRes, ordRes, lowRes, catRes] = await Promise.all([
        fetch(`/api/shops/${shopId}/dashboard`),
        fetch(`/api/shops/${shopId}/products?include_inactive=true`),
        fetch(`/api/shops/${shopId}/orders`),
        fetch(`/api/shops/${shopId}/low-stock`),
        fetch('/api/categories')
      ])
      if (dashRes.ok) setDashboardStats(await dashRes.json())
      if (prodRes.ok) setProducts(await prodRes.json())
      if (ordRes.ok) setOrders(await ordRes.json())
      if (lowRes.ok) setLowStockProducts(await lowRes.json())
      if (catRes.ok) setCategories(await catRes.json())
    } catch (err) { console.error('Error fetching admin data:', err) }
  }

  const fetchPlatformData = async () => {
    try {
      const [statsRes, shopsRes, usersRes] = await Promise.all([
        fetch('/api/platform/stats'),
        fetch('/api/platform/shops'),
        fetch('/api/users')
      ])
      if (statsRes.ok) setPlatformStats(await statsRes.json())
      if (shopsRes.ok) setAllShops(await shopsRes.json())
      if (usersRes.ok) setAllUsers(await usersRes.json())
    } catch (err) { console.error('Error fetching platform data:', err) }
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
        if (user?.role === 'admin' && user.shop_id) fetchAdminData(user.shop_id)
        if (user?.role === 'super_admin') fetchPlatformData()
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
        fetchAdminData(user.shop_id)
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
        fetchAdminData(user.shop_id)
      }
    } catch (err) { addLog(`Error: ${err.message}`, 'error') }
  }

  const deleteProduct = async (id) => {
    if (!confirm('Delete this product?')) return
    await fetch(`/api/products/${id}`, { method: 'DELETE' })
    addLog('Product deleted', 'success')
    fetchAdminData(user.shop_id)
  }

  const editProduct = (p) => {
    setEditingProduct(p)
    setProductForm({
      name: p.name, description: p.description || '', brand: p.brand || '',
      sku: p.sku || '', barcode: p.barcode || '',
      price: p.price.toString(), cost_price: p.cost_price?.toString() || '',
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
      price: '', cost_price: '', compare_at_price: '',
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
      fetchPlatformData()
    }
  }

  const suspendShop = async (shopId) => {
    if (!confirm('Suspend this shop?')) return
    const res = await fetch(`/api/platform/shops/${shopId}/suspend`, { method: 'PATCH' })
    if (res.ok) {
      addLog('Shop suspended', 'success')
      fetchPlatformData()
    }
  }

  const activateShop = async (shopId) => {
    const res = await fetch(`/api/platform/shops/${shopId}/activate`, { method: 'PATCH' })
    if (res.ok) {
      addLog('Shop activated', 'success')
      fetchPlatformData()
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

  // Filtered products for search
  const filteredProducts = searchQuery
    ? shopProducts.filter(p =>
        p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.brand?.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : shopProducts

  // ============== LOGIN PAGE ==============
  if (!user) {
    return (
      <div className="login-page">
        <div className="login-container">
          <div className="login-header">
            <h1>KommandAI</h1>
            <p>Multi-Vendor Marketplace Platform</p>
          </div>

          {showRegister ? (
            <form onSubmit={handleRegister} className="login-form">
              <h2>Create Account</h2>
              {loginError && <div className="error-msg">{loginError}</div>}
              <div className="form-group">
                <label>Name</label>
                <input
                  type="text"
                  value={registerForm.name}
                  onChange={e => setRegisterForm({...registerForm, name: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={registerForm.email}
                  onChange={e => setRegisterForm({...registerForm, email: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Phone</label>
                <input
                  type="tel"
                  value={registerForm.phone}
                  onChange={e => setRegisterForm({...registerForm, phone: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>Password</label>
                <input
                  type="password"
                  value={registerForm.password}
                  onChange={e => setRegisterForm({...registerForm, password: e.target.value})}
                  required
                />
              </div>
              <button type="submit" className="login-btn">Register</button>
              <p className="switch-auth">
                Already have an account? <button type="button" onClick={() => setShowRegister(false)}>Login</button>
              </p>
            </form>
          ) : (
            <form onSubmit={handleLogin} className="login-form">
              <h2>Login</h2>
              {loginError && <div className="error-msg">{loginError}</div>}
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={loginForm.email}
                  onChange={e => setLoginForm({...loginForm, email: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Password</label>
                <input
                  type="password"
                  value={loginForm.password}
                  onChange={e => setLoginForm({...loginForm, password: e.target.value})}
                  required
                />
              </div>
              <button type="submit" className="login-btn">Login</button>
              <p className="switch-auth">
                New here? <button type="button" onClick={() => setShowRegister(true)}>Create Account</button>
              </p>
            </form>
          )}

          <div className="demo-accounts">
            <h3>Demo Accounts</h3>
            <div className="demo-list">
              <button onClick={() => setLoginForm({ email: 'superadmin@kommandai.com', password: 'qwert12345' })}>
                Super Admin
              </button>
              <button onClick={() => setLoginForm({ email: 'admin@kommandai.com', password: 'qwert12345' })}>
                Admin
              </button>
              <button onClick={() => setLoginForm({ email: 'customer@kommandai.com', password: 'qwert12345' })}>
                Customer
              </button>
            </div>
          </div>
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
            <span className="user-info">{user.name}</span>
            <button className="logout-btn" onClick={logout}>Logout</button>
          </div>
        </header>

        {/* AI Command Panel */}
        <div className="command-panel">
          <form onSubmit={sendCommand} className="command-form">
            <div className="command-input-wrapper">
              <span className="command-icon">🤖</span>
              <input
                type="text"
                value={command}
                onChange={e => setCommand(e.target.value)}
                placeholder="Platform commands... (e.g., 'Show all unverified shops')"
                disabled={isProcessing}
                className="command-input"
              />
              <button type="submit" disabled={isProcessing || !command.trim()} className="command-btn">
                {isProcessing ? '...' : 'Go'}
              </button>
            </div>
          </form>
        </div>

        {/* Platform Stats */}
        <div className="stats-grid platform-stats">
          <div className="stat-card primary">
            <div className="stat-value">{platformStats.total_shops || 0}</div>
            <div className="stat-label">Total Shops</div>
          </div>
          <div className="stat-card success">
            <div className="stat-value">{platformStats.verified_shops || 0}</div>
            <div className="stat-label">Verified Shops</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{platformStats.total_shop_owners || 0}</div>
            <div className="stat-label">Shop Owners</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{platformStats.total_customers || 0}</div>
            <div className="stat-label">Customers</div>
          </div>
          <div className="stat-card success">
            <div className="stat-value">${platformStats.platform_revenue?.toLocaleString() || 0}</div>
            <div className="stat-label">Total Revenue</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{platformStats.total_users || 0}</div>
            <div className="stat-label">Total Users</div>
          </div>
        </div>

        {/* Super Admin Tabs */}
        <div className="tabs">
          {['overview', 'shops', 'users', 'categories'].map(tab => (
            <button
              key={tab}
              className={`tab ${superAdminTab === tab ? 'active' : ''}`}
              onClick={() => setSuperAdminTab(tab)}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Overview Tab */}
        {superAdminTab === 'overview' && (
          <div className="dashboard-grid">
            <div className="panel">
              <h2>Pending Verification</h2>
              <div className="shop-list">
                {allShops.filter(s => !s.is_verified).map(shop => (
                  <div key={shop.id} className="shop-item">
                    <div className="shop-info">
                      <strong>{shop.name}</strong>
                      <span>{shop.owner_email}</span>
                      <span className="city">{shop.city}</span>
                    </div>
                    <div className="shop-actions">
                      <button className="verify-btn" onClick={() => verifyShop(shop.id)}>Verify</button>
                    </div>
                  </div>
                ))}
                {allShops.filter(s => !s.is_verified).length === 0 && (
                  <p className="empty">No shops pending verification</p>
                )}
              </div>
            </div>

            <div className="panel logs-panel">
              <h2>Activity Log</h2>
              <div className="log-list">
                {logs.slice(0, 10).map((log, i) => (
                  <div key={i} className={`log-item ${log.type}`}>
                    <span className="log-time">{log.time}</span>
                    <span>{log.message}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Shops Tab */}
        {superAdminTab === 'shops' && (
          <div className="data-panel">
            <h2>All Shops ({allShops.length})</h2>
            <div className="data-table">
              <table>
                <thead>
                  <tr>
                    <th>Shop Name</th>
                    <th>Owner</th>
                    <th>City</th>
                    <th>Orders</th>
                    <th>Revenue</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {allShops.map(shop => (
                    <tr key={shop.id} className={!shop.is_active ? 'suspended' : ''}>
                      <td>
                        <div className="shop-cell">
                          <strong>{shop.name}</strong>
                          {shop.is_verified && <span className="verified-badge">✓</span>}
                        </div>
                      </td>
                      <td>{shop.owner_email || '-'}</td>
                      <td>{shop.city || '-'}</td>
                      <td>{shop.total_orders}</td>
                      <td>${shop.total_revenue?.toLocaleString()}</td>
                      <td>
                        <span className={`status ${shop.is_active ? 'active' : 'suspended'}`}>
                          {shop.is_active ? 'Active' : 'Suspended'}
                        </span>
                      </td>
                      <td>
                        {!shop.is_verified && (
                          <button className="verify-btn" onClick={() => verifyShop(shop.id)}>Verify</button>
                        )}
                        {shop.is_active ? (
                          <button className="suspend-btn" onClick={() => suspendShop(shop.id)}>Suspend</button>
                        ) : (
                          <button className="activate-btn" onClick={() => activateShop(shop.id)}>Activate</button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Users Tab */}
        {superAdminTab === 'users' && (
          <div className="data-panel">
            <h2>All Users ({allUsers.length})</h2>
            <div className="data-table">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Phone</th>
                    <th>Status</th>
                    <th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {allUsers.map(u => (
                    <tr key={u.id}>
                      <td>{u.name}</td>
                      <td>{u.email}</td>
                      <td><span className={`role ${u.role}`}>{u.role}</span></td>
                      <td>{u.phone || '-'}</td>
                      <td>
                        <span className={`status ${u.is_active ? 'active' : 'inactive'}`}>
                          {u.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td>{new Date(u.created_at).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Categories Tab */}
        {superAdminTab === 'categories' && (
          <div className="data-panel">
            <h2>Shop Categories</h2>
            <div className="categories-admin">
              {shopCategories.map(cat => (
                <div key={cat.id} className="category-admin-card">
                  <span className="cat-icon">{cat.icon}</span>
                  <div className="cat-info">
                    <h3>{cat.name}</h3>
                    <p>{cat.description}</p>
                    <span className="shop-count">{cat.shop_count} shops</span>
                  </div>
                </div>
              ))}
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
            <div className="connection-status">
              <span className={`dot ${isConnected ? 'connected' : ''}`}></span>
              {isConnected ? 'Live' : 'Offline'}
            </div>
            <span className="user-info">{user.name}</span>
            <button className="logout-btn" onClick={logout}>Logout</button>
          </div>
        </header>

        {/* AI Command Panel */}
        <div className="command-panel">
          <form onSubmit={sendCommand} className="command-form">
            <div className="command-input-wrapper">
              <span className="command-icon">🤖</span>
              <input
                type="text"
                value={command}
                onChange={e => setCommand(e.target.value)}
                placeholder="Tell me what to do... (e.g., 'Add product Swiss Beauty Lipstick price 299')"
                disabled={isProcessing}
                className="command-input"
              />
              <button type="submit" disabled={isProcessing || !command.trim()} className="command-btn">
                {isProcessing ? '...' : 'Go'}
              </button>
            </div>
          </form>
        </div>

        {/* Stats Dashboard */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-value">{dashboardStats.total_products || 0}</div>
            <div className="stat-label">Products</div>
          </div>
          <div className="stat-card success">
            <div className="stat-value">${dashboardStats.total_revenue?.toLocaleString() || 0}</div>
            <div className="stat-label">Total Revenue</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{dashboardStats.total_orders || 0}</div>
            <div className="stat-label">Orders</div>
          </div>
          <div className="stat-card warning">
            <div className="stat-value">{dashboardStats.pending_orders || 0}</div>
            <div className="stat-label">Pending</div>
          </div>
          <div className="stat-card danger">
            <div className="stat-value">{dashboardStats.low_stock_count || 0}</div>
            <div className="stat-label">Low Stock</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">${dashboardStats.inventory_value?.toLocaleString() || 0}</div>
            <div className="stat-label">Inventory Value</div>
          </div>
        </div>

        {/* Admin Tabs */}
        <div className="tabs">
          {['dashboard', 'products', 'orders'].map(tab => (
            <button key={tab} className={`tab ${activeTab === tab ? 'active' : ''}`} onClick={() => setActiveTab(tab)}>
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && (
          <div className="dashboard-grid">
            <div className="panel alerts-panel">
              <h2>Low Stock Alerts</h2>
              {lowStockProducts.length === 0 ? (
                <p className="empty">All products are well stocked</p>
              ) : (
                <div className="alert-list">
                  {lowStockProducts.map(p => (
                    <div key={p.id} className="alert-item">
                      <span className="alert-name">{p.name}</span>
                      <span className="alert-sku">{p.sku}</span>
                      <span className={`alert-qty ${p.quantity === 0 ? 'zero' : ''}`}>
                        {p.quantity} left
                      </span>
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
                  <div key={i} className={`log-item ${log.type}`}>
                    <span className="log-time">{log.time}</span>
                    <span>{log.message}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Products Tab */}
        {activeTab === 'products' && (
          <div className="tab-content">
            <div className="form-panel">
              <h2>{editingProduct ? 'Edit Product' : 'Add New Product'}</h2>
              <form onSubmit={editingProduct ? updateProduct : createProduct}>
                <div className="form-section">
                  <div className="form-group">
                    <label>Product Name *</label>
                    <input type="text" value={productForm.name} onChange={e => setProductForm({...productForm, name: e.target.value})} required />
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label>Brand</label>
                      <input type="text" value={productForm.brand} onChange={e => setProductForm({...productForm, brand: e.target.value})} />
                    </div>
                    <div className="form-group">
                      <label>SKU</label>
                      <input type="text" value={productForm.sku} onChange={e => setProductForm({...productForm, sku: e.target.value})} />
                    </div>
                  </div>
                  <div className="form-group">
                    <label>Description</label>
                    <textarea value={productForm.description} onChange={e => setProductForm({...productForm, description: e.target.value})} />
                  </div>
                </div>

                <div className="form-section">
                  <h3>Pricing</h3>
                  <div className="form-row">
                    <div className="form-group">
                      <label>Selling Price *</label>
                      <input type="number" step="0.01" value={productForm.price} onChange={e => setProductForm({...productForm, price: e.target.value})} required />
                    </div>
                    <div className="form-group">
                      <label>Cost Price</label>
                      <input type="number" step="0.01" value={productForm.cost_price} onChange={e => setProductForm({...productForm, cost_price: e.target.value})} />
                    </div>
                  </div>
                  {productForm.cost_price && productForm.price && (
                    <div className="profit-margin">
                      Profit Margin: {(((parseFloat(productForm.price) - parseFloat(productForm.cost_price)) / parseFloat(productForm.cost_price)) * 100).toFixed(1)}%
                    </div>
                  )}
                </div>

                <div className="form-section">
                  <h3>Inventory</h3>
                  <div className="form-row">
                    <div className="form-group">
                      <label>Quantity *</label>
                      <input type="number" value={productForm.quantity} onChange={e => setProductForm({...productForm, quantity: e.target.value})} required />
                    </div>
                    <div className="form-group">
                      <label>Low Stock Alert</label>
                      <input type="number" value={productForm.min_stock_level} onChange={e => setProductForm({...productForm, min_stock_level: e.target.value})} />
                    </div>
                  </div>
                </div>

                <div className="form-group">
                  <label>Tags (comma-separated)</label>
                  <input type="text" value={productForm.tags} onChange={e => setProductForm({...productForm, tags: e.target.value})} placeholder="e.g. lipstick, makeup" />
                </div>

                <div className="form-actions">
                  {editingProduct && <button type="button" className="cancel-btn" onClick={resetProductForm}>Cancel</button>}
                  <button type="submit" className="submit-btn">{editingProduct ? 'Update' : 'Add Product'}</button>
                </div>
              </form>
            </div>

            <div className="data-panel">
              <h2>Products ({products.length})</h2>
              <div className="data-table">
                <table>
                  <thead>
                    <tr>
                      <th>Product</th>
                      <th>SKU</th>
                      <th>Cost</th>
                      <th>Price</th>
                      <th>Stock</th>
                      <th>Sold</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {products.map(p => (
                      <tr key={p.id} className={!p.is_active ? 'inactive' : ''}>
                        <td>
                          <div className="product-cell">
                            <strong>{p.name}</strong>
                            {p.brand && <span className="brand">{p.brand}</span>}
                          </div>
                        </td>
                        <td>{p.sku || '-'}</td>
                        <td>{p.cost_price ? `$${p.cost_price}` : '-'}</td>
                        <td className="price">${p.price}</td>
                        <td className={p.quantity <= p.min_stock_level ? 'low-stock' : ''}>{p.quantity}</td>
                        <td>{p.sold_count}</td>
                        <td>
                          <button className="edit-btn" onClick={() => editProduct(p)}>Edit</button>
                          <button className="delete-btn" onClick={() => deleteProduct(p.id)}>Delete</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Orders Tab */}
        {activeTab === 'orders' && (
          <div className="orders-panel">
            <h2>Orders ({orders.length})</h2>
            {orders.length === 0 ? (
              <p className="empty">No orders yet</p>
            ) : (
              <div className="data-table">
                <table>
                  <thead>
                    <tr>
                      <th>Order #</th>
                      <th>Customer</th>
                      <th>Product</th>
                      <th>Qty</th>
                      <th>Total</th>
                      <th>Status</th>
                      <th>Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {orders.map(o => (
                      <tr key={o.id}>
                        <td>#{o.id}</td>
                        <td>{o.customer_name}</td>
                        <td>{o.product_name}</td>
                        <td>{o.quantity}</td>
                        <td className="price">${o.total_amount}</td>
                        <td><span className={`status ${o.status}`}>{o.status}</span></td>
                        <td>{new Date(o.created_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    )
  }

  // ============== CUSTOMER VIEW (MARKETPLACE) ==============
  // Home - Show shop categories
  if (!selectedShopCategory && !selectedShop) {
    return (
      <div className="marketplace">
        <header className="marketplace-header">
          <div className="header-left">
            <h1>KommandAI Marketplace</h1>
            <p>Shop from your favorite stores</p>
          </div>
          <div className="header-right">
            <span className="user-info">Hi, {user.name}</span>
            <button className="logout-btn" onClick={logout}>Logout</button>
          </div>
        </header>

        {/* AI Command Panel */}
        <div className="command-panel customer-command">
          <form onSubmit={sendCommand} className="command-form">
            <div className="command-input-wrapper">
              <span className="command-icon">🔍</span>
              <input
                type="text"
                value={command}
                onChange={e => setCommand(e.target.value)}
                placeholder="Search products, shops... (e.g., 'Find lipstick in beauty shops')"
                disabled={isProcessing}
                className="command-input"
              />
              <button type="submit" disabled={isProcessing || !command.trim()} className="command-btn">
                {isProcessing ? '...' : 'Go'}
              </button>
            </div>
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

        {cart.length > 0 && (
          <div className="floating-cart">
            <span>{cart.reduce((sum, i) => sum + i.qty, 0)} items</span>
            <span>${cartTotal.toFixed(2)}</span>
          </div>
        )}
      </div>
    )
  }

  // Show shops in selected category
  if (selectedShopCategory && !selectedShop) {
    const category = shopCategories.find(c => c.id === selectedShopCategory)
    return (
      <div className="marketplace">
        <header className="marketplace-header">
          <button className="back-btn" onClick={() => setSelectedShopCategory(null)}>← Back</button>
          <h1>{category?.icon} {category?.name}</h1>
          <div className="header-right">
            <span className="user-info">Hi, {user.name}</span>
            <button className="logout-btn" onClick={logout}>Logout</button>
          </div>
        </header>

        <div className="shops-grid">
          {shops.map(shop => (
            <div key={shop.id} className="shop-card" onClick={() => setSelectedShop(shop.id)}>
              <div className="shop-logo">{shop.name[0]}</div>
              <div className="shop-info">
                <h3>{shop.name}</h3>
                <p>{shop.description}</p>
                <div className="shop-meta">
                  <span className="rating">★ {shop.rating.toFixed(1)}</span>
                  <span className="city">{shop.city}</span>
                </div>
              </div>
            </div>
          ))}
          {shops.length === 0 && <p className="empty">No shops in this category yet</p>}
        </div>
      </div>
    )
  }

  // Show products in selected shop
  if (selectedShop) {
    const shop = shops.find(s => s.id === selectedShop)
    return (
      <div className="marketplace">
        <header className="shop-header">
          <button className="back-btn" onClick={() => { setSelectedShop(null); setShopProducts([]) }}>← Back</button>
          <div className="shop-title">
            <h1>{shop?.name}</h1>
            <span className="rating">★ {shop?.rating.toFixed(1)}</span>
          </div>
          <div className="header-right">
            <span className="user-info">Hi, {user.name}</span>
            <button className="logout-btn" onClick={logout}>Logout</button>
          </div>
        </header>

        <div className="search-bar">
          <input
            type="text"
            placeholder={`Search in ${shop?.name}...`}
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="products-grid">
          {filteredProducts.map(p => (
            <div key={p.id} className="product-card">
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
                <button
                  className="add-to-cart"
                  onClick={() => addToCart(p)}
                  disabled={p.quantity === 0}
                >
                  {p.quantity === 0 ? 'Out of Stock' : 'Add to Cart'}
                </button>
              </div>
            </div>
          ))}
          {filteredProducts.length === 0 && (
            <p className="empty">No products found</p>
          )}
        </div>

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
            <div className="cart-total">
              <span>Total:</span>
              <span>${cartTotal.toFixed(2)}</span>
            </div>
            <button className="checkout-btn">Checkout</button>
          </div>
        )}
      </div>
    )
  }

  return null
}

export default App
