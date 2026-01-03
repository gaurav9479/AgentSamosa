import { useState, useEffect, useRef } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar } from 'recharts'

const COLORS = ['#3b82f6', '#22c55e', '#f97316', '#8b5cf6', '#ef4444', '#06b6d4']

function App() {
  // View mode: 'admin' or 'shop'
  const [viewMode, setViewMode] = useState('admin')

  // Data states
  const [products, setProducts] = useState([])
  const [categories, setCategories] = useState([])
  const [orders, setOrders] = useState([])
  const [customers, setCustomers] = useState([])
  const [lowStockProducts, setLowStockProducts] = useState([])
  const [inventoryStats, setInventoryStats] = useState({})

  // UI states
  const [activeTab, setActiveTab] = useState('dashboard')
  const [isConnected, setIsConnected] = useState(false)
  const [logs, setLogs] = useState([])
  const [selectedCategory, setSelectedCategory] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')

  // Form states
  const [productForm, setProductForm] = useState({
    name: '', description: '', brand: '', sku: '', barcode: '',
    price: '', cost_price: '', compare_at_price: '',
    quantity: '', min_stock_level: '5', category_id: '',
    tags: '', unit: 'piece', is_featured: false
  })
  const [categoryForm, setCategoryForm] = useState({ name: '', description: '' })
  const [editingProduct, setEditingProduct] = useState(null)
  const [editingCategory, setEditingCategory] = useState(null)

  // Cart state (for shop view)
  const [cart, setCart] = useState([])

  // AI Command state
  const [command, setCommand] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)

  // Analytics
  const [revenueData, setRevenueData] = useState([])
  const [orderStatusData, setOrderStatusData] = useState([])

  const wsRef = useRef(null)

  useEffect(() => {
    connectWebSocket()
    fetchData()
    return () => { if (wsRef.current) wsRef.current.close() }
  }, [])

  const connectWebSocket = () => {
    const ws = new WebSocket(`ws://${window.location.hostname}:8000/api/ws`)
    ws.onopen = () => { setIsConnected(true); addLog('Connected to server', 'info') }
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data)
      if (data.type === 'action_result' || data.type === 'data_update') {
        fetchData()
      }
    }
    ws.onclose = () => { setIsConnected(false); setTimeout(connectWebSocket, 3000) }
    wsRef.current = ws
  }

  const fetchData = async () => {
    try {
      const [prodRes, catRes, ordRes, custRes, lowStockRes, invRes, revRes, statusRes] = await Promise.all([
        fetch('/api/products?include_inactive=true'),
        fetch('/api/categories/with-counts'),
        fetch('/api/orders'),
        fetch('/api/customers'),
        fetch('/api/products/low-stock'),
        fetch('/api/products/inventory-stats'),
        fetch('/api/analytics/revenue?days=7'),
        fetch('/api/analytics/order-status')
      ])
      if (prodRes.ok) setProducts(await prodRes.json())
      if (catRes.ok) setCategories(await catRes.json())
      if (ordRes.ok) setOrders(await ordRes.json())
      if (custRes.ok) setCustomers(await custRes.json())
      if (lowStockRes.ok) setLowStockProducts(await lowStockRes.json())
      if (invRes.ok) setInventoryStats(await invRes.json())
      if (revRes.ok) setRevenueData(await revRes.json())
      if (statusRes.ok) setOrderStatusData(await statusRes.json())
    } catch (err) { console.error('Fetch error:', err) }
  }

  const addLog = (message, type = 'info') => {
    setLogs(prev => [{ message, type, time: new Date().toLocaleTimeString() }, ...prev].slice(0, 30))
  }

  // Product CRUD
  const createProduct = async (e) => {
    e.preventDefault()
    try {
      const data = {
        name: productForm.name,
        price: parseFloat(productForm.price),
        description: productForm.description || null,
        brand: productForm.brand || null,
        sku: productForm.sku || null,
        barcode: productForm.barcode || null,
        cost_price: productForm.cost_price ? parseFloat(productForm.cost_price) : null,
        compare_at_price: productForm.compare_at_price ? parseFloat(productForm.compare_at_price) : null,
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
        fetchData()
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
        barcode: productForm.barcode || null,
        cost_price: productForm.cost_price ? parseFloat(productForm.cost_price) : null,
        compare_at_price: productForm.compare_at_price ? parseFloat(productForm.compare_at_price) : null,
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
        fetchData()
      }
    } catch (err) { addLog(`Error: ${err.message}`, 'error') }
  }

  const deleteProduct = async (id) => {
    if (!confirm('Delete this product?')) return
    await fetch(`/api/products/${id}`, { method: 'DELETE' })
    addLog(`Product deleted`, 'success')
    fetchData()
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

  // Category CRUD
  const createCategory = async (e) => {
    e.preventDefault()
    const res = await fetch('/api/categories', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(categoryForm)
    })
    if (res.ok) {
      addLog(`Category "${categoryForm.name}" created`, 'success')
      setCategoryForm({ name: '', description: '' })
      fetchData()
    }
  }

  const deleteCategory = async (id) => {
    if (!confirm('Delete this category?')) return
    await fetch(`/api/categories/${id}`, { method: 'DELETE' })
    addLog('Category deleted', 'success')
    fetchData()
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
  }

  const removeFromCart = (id) => {
    setCart(prev => prev.filter(i => i.id !== id))
  }

  const cartTotal = cart.reduce((sum, i) => sum + i.price * i.qty, 0)

  // AI Command Examples
  const EXAMPLE_COMMANDS = [
    "Create a product called iPhone 15 with price 999",
    "List all products",
    "Update product iPhone to price 899",
    "Create category Electronics",
    "Create customer John with email john@email.com",
    "List all customers",
    "Create order for product iPhone quantity 2",
    "Show low stock products"
  ]

  // Send AI command
  const sendCommand = async (e) => {
    e?.preventDefault()
    if (!command.trim() || isProcessing) return

    setIsProcessing(true)
    addLog(`Processing: "${command}"`, 'info')

    try {
      const res = await fetch('/api/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: command.trim() })
      })
      const data = await res.json()

      if (res.ok) {
        addLog(`✓ ${data.message || 'Command executed successfully'}`, 'success')
        if (data.result) {
          if (Array.isArray(data.result)) {
            addLog(`Found ${data.result.length} items`, 'info')
          } else if (typeof data.result === 'object') {
            addLog(`Result: ${JSON.stringify(data.result).slice(0, 100)}...`, 'info')
          }
        }
        fetchData()
      } else {
        addLog(`✗ ${data.detail || 'Command failed'}`, 'error')
      }
    } catch (err) {
      addLog(`Error: ${err.message}`, 'error')
    } finally {
      setIsProcessing(false)
      setCommand('')
    }
  }

  // Filtered products for shop view
  const filteredProducts = products.filter(p => {
    if (!p.is_active) return false
    if (selectedCategory && p.category_id !== selectedCategory) return false
    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      return p.name.toLowerCase().includes(q) || p.brand?.toLowerCase().includes(q)
    }
    return true
  })

  // Calculate stats
  const totalRevenue = orders.reduce((sum, o) => o.status !== 'cancelled' ? sum + o.total_amount : sum, 0)
  const pendingOrders = orders.filter(o => o.status === 'pending').length

  // ============== ADMIN VIEW ==============
  if (viewMode === 'admin') {
    return (
      <div className="app">
        <header>
          <div className="header-content">
            <div>
              <h1>KommandAI</h1>
              <p>Shop Management System</p>
            </div>
            <div className="header-actions">
              <button className="mode-switch" onClick={() => setViewMode('shop')}>
                View as Customer
              </button>
              <div className="connection-status">
                <span className={`dot ${isConnected ? 'connected' : ''}`}></span>
                {isConnected ? 'Live' : 'Offline'}
              </div>
            </div>
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
                placeholder="Tell me what to do... (e.g., 'Create a product called iPhone with price 999')"
                disabled={isProcessing}
                className="command-input"
              />
              <button type="submit" disabled={isProcessing || !command.trim()} className="command-btn">
                {isProcessing ? 'Processing...' : 'Execute'}
              </button>
            </div>
            <div className="command-examples">
              <span>Try:</span>
              {EXAMPLE_COMMANDS.slice(0, 4).map((ex, i) => (
                <button key={i} type="button" onClick={() => setCommand(ex)} className="example-btn">
                  {ex}
                </button>
              ))}
            </div>
          </form>
        </div>

        {/* Stats Dashboard */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-value">{inventoryStats.total_products || 0}</div>
            <div className="stat-label">Products</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">${inventoryStats.inventory_value?.toLocaleString() || 0}</div>
            <div className="stat-label">Inventory Value</div>
          </div>
          <div className="stat-card warning">
            <div className="stat-value">{inventoryStats.low_stock || 0}</div>
            <div className="stat-label">Low Stock</div>
          </div>
          <div className="stat-card danger">
            <div className="stat-value">{inventoryStats.out_of_stock || 0}</div>
            <div className="stat-label">Out of Stock</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{orders.length}</div>
            <div className="stat-label">Total Orders</div>
          </div>
          <div className="stat-card success">
            <div className="stat-value">${totalRevenue.toFixed(2)}</div>
            <div className="stat-label">Revenue</div>
          </div>
        </div>

        {/* Admin Tabs */}
        <div className="tabs">
          {['dashboard', 'products', 'categories', 'orders', 'customers'].map(tab => (
            <button key={tab} className={`tab ${activeTab === tab ? 'active' : ''}`} onClick={() => setActiveTab(tab)}>
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Dashboard Tab */}
        {activeTab === 'dashboard' && (
          <div className="dashboard-grid">
            {/* Low Stock Alerts */}
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

            {/* Revenue Chart */}
            <div className="panel chart-panel">
              <h2>Revenue (Last 7 Days)</h2>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={revenueData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="date" stroke="#94a3b8" tick={{ fontSize: 12 }} />
                  <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} />
                  <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155' }} />
                  <Line type="monotone" dataKey="revenue" stroke="#22c55e" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Order Status */}
            <div className="panel chart-panel">
              <h2>Order Status</h2>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={orderStatusData} dataKey="count" nameKey="status" cx="50%" cy="50%" outerRadius={70}
                    label={({ status, count }) => `${status}: ${count}`}>
                    {orderStatusData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Recent Activity */}
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
                  <h3>Basic Info</h3>
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
                      <label>Category</label>
                      <select value={productForm.category_id} onChange={e => setProductForm({...productForm, category_id: e.target.value})}>
                        <option value="">No Category</option>
                        {categories.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                      </select>
                    </div>
                  </div>
                  <div className="form-group">
                    <label>Description</label>
                    <textarea value={productForm.description} onChange={e => setProductForm({...productForm, description: e.target.value})} />
                  </div>
                </div>

                <div className="form-section">
                  <h3>Pricing</h3>
                  <div className="form-row three">
                    <div className="form-group">
                      <label>Selling Price *</label>
                      <input type="number" step="0.01" value={productForm.price} onChange={e => setProductForm({...productForm, price: e.target.value})} required />
                    </div>
                    <div className="form-group">
                      <label>Cost Price</label>
                      <input type="number" step="0.01" value={productForm.cost_price} onChange={e => setProductForm({...productForm, cost_price: e.target.value})} />
                    </div>
                    <div className="form-group">
                      <label>Compare at Price</label>
                      <input type="number" step="0.01" value={productForm.compare_at_price} onChange={e => setProductForm({...productForm, compare_at_price: e.target.value})} />
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
                  <div className="form-row three">
                    <div className="form-group">
                      <label>SKU</label>
                      <input type="text" value={productForm.sku} onChange={e => setProductForm({...productForm, sku: e.target.value})} />
                    </div>
                    <div className="form-group">
                      <label>Barcode</label>
                      <input type="text" value={productForm.barcode} onChange={e => setProductForm({...productForm, barcode: e.target.value})} />
                    </div>
                    <div className="form-group">
                      <label>Unit</label>
                      <select value={productForm.unit} onChange={e => setProductForm({...productForm, unit: e.target.value})}>
                        <option value="piece">Piece</option>
                        <option value="kg">Kilogram</option>
                        <option value="liter">Liter</option>
                        <option value="meter">Meter</option>
                        <option value="box">Box</option>
                      </select>
                    </div>
                  </div>
                  <div className="form-row">
                    <div className="form-group">
                      <label>Quantity in Stock *</label>
                      <input type="number" value={productForm.quantity} onChange={e => setProductForm({...productForm, quantity: e.target.value})} required />
                    </div>
                    <div className="form-group">
                      <label>Low Stock Alert Level</label>
                      <input type="number" value={productForm.min_stock_level} onChange={e => setProductForm({...productForm, min_stock_level: e.target.value})} />
                    </div>
                  </div>
                </div>

                <div className="form-section">
                  <h3>Additional</h3>
                  <div className="form-group">
                    <label>Tags (comma-separated)</label>
                    <input type="text" value={productForm.tags} onChange={e => setProductForm({...productForm, tags: e.target.value})} placeholder="e.g. electronics, sale, new" />
                  </div>
                  <div className="form-group checkbox">
                    <label>
                      <input type="checkbox" checked={productForm.is_featured} onChange={e => setProductForm({...productForm, is_featured: e.target.checked})} />
                      Featured Product
                    </label>
                  </div>
                </div>

                <div className="form-actions">
                  {editingProduct && <button type="button" className="cancel-btn" onClick={resetProductForm}>Cancel</button>}
                  <button type="submit" className="submit-btn">{editingProduct ? 'Update Product' : 'Create Product'}</button>
                </div>
              </form>
            </div>

            <div className="data-panel">
              <h2>All Products ({products.length})</h2>
              <div className="data-table">
                <table>
                  <thead>
                    <tr>
                      <th>Product</th>
                      <th>SKU</th>
                      <th>Category</th>
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
                            {p.is_featured && <span className="badge featured">Featured</span>}
                          </div>
                        </td>
                        <td>{p.sku || '-'}</td>
                        <td>{categories.find(c => c.id === p.category_id)?.name || '-'}</td>
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

        {/* Categories Tab */}
        {activeTab === 'categories' && (
          <div className="tab-content">
            <div className="form-panel small">
              <h2>Add Category</h2>
              <form onSubmit={createCategory}>
                <div className="form-group">
                  <label>Category Name *</label>
                  <input type="text" value={categoryForm.name} onChange={e => setCategoryForm({...categoryForm, name: e.target.value})} required />
                </div>
                <div className="form-group">
                  <label>Description</label>
                  <textarea value={categoryForm.description} onChange={e => setCategoryForm({...categoryForm, description: e.target.value})} />
                </div>
                <button type="submit" className="submit-btn">Create Category</button>
              </form>
            </div>

            <div className="data-panel">
              <h2>Categories</h2>
              <div className="category-grid">
                {categories.map(c => (
                  <div key={c.id} className="category-card">
                    <h3>{c.name}</h3>
                    <p>{c.description || 'No description'}</p>
                    <div className="category-stats">
                      <span>{c.product_count} products</span>
                    </div>
                    <button className="delete-btn" onClick={() => deleteCategory(c.id)}>Delete</button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Orders Tab */}
        {activeTab === 'orders' && (
          <div className="orders-panel">
            <h2>Orders ({orders.length})</h2>
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
          </div>
        )}

        {/* Customers Tab */}
        {activeTab === 'customers' && (
          <div className="customers-panel">
            <h2>Customers ({customers.length})</h2>
            <div className="data-table">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Phone</th>
                    <th>Orders</th>
                    <th>Total Spent</th>
                  </tr>
                </thead>
                <tbody>
                  {customers.map(c => (
                    <tr key={c.id}>
                      <td>{c.name}</td>
                      <td>{c.email}</td>
                      <td>{c.phone || '-'}</td>
                      <td>{c.total_orders}</td>
                      <td className="price">${c.total_spent.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    )
  }

  // ============== SHOP/CUSTOMER VIEW ==============
  return (
    <div className="shop-app">
      <header className="shop-header">
        <div className="shop-header-content">
          <h1>KommandAI Shop</h1>
          <div className="shop-actions">
            <button className="mode-switch admin" onClick={() => setViewMode('admin')}>
              Admin Panel
            </button>
            <div className="cart-icon" onClick={() => setActiveTab('cart')}>
              Cart ({cart.reduce((sum, i) => sum + i.qty, 0)})
            </div>
          </div>
        </div>
      </header>

      {/* AI Command Panel for Shop */}
      <div className="command-panel shop-command">
        <form onSubmit={sendCommand} className="command-form">
          <div className="command-input-wrapper">
            <span className="command-icon">🤖</span>
            <input
              type="text"
              value={command}
              onChange={e => setCommand(e.target.value)}
              placeholder="Ask me anything... (e.g., 'Show me electronics', 'Find products under $50')"
              disabled={isProcessing}
              className="command-input"
            />
            <button type="submit" disabled={isProcessing || !command.trim()} className="command-btn">
              {isProcessing ? '...' : 'Go'}
            </button>
          </div>
        </form>
      </div>

      {/* Search Bar */}
      <div className="shop-search">
        <input
          type="text"
          placeholder="Search products..."
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
        />
      </div>

      {/* Category Filter */}
      <div className="category-filter">
        <button className={!selectedCategory ? 'active' : ''} onClick={() => setSelectedCategory(null)}>
          All
        </button>
        {categories.map(c => (
          <button key={c.id} className={selectedCategory === c.id ? 'active' : ''} onClick={() => setSelectedCategory(c.id)}>
            {c.name} ({c.product_count})
          </button>
        ))}
      </div>

      {activeTab !== 'cart' ? (
        /* Product Grid */
        <div className="product-grid">
          {filteredProducts.map(p => (
            <div key={p.id} className="product-card">
              <div className="product-image">
                {p.image_url ? <img src={p.image_url} alt={p.name} /> : <div className="placeholder">No Image</div>}
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
        </div>
      ) : (
        /* Cart View */
        <div className="cart-view">
          <h2>Your Cart</h2>
          {cart.length === 0 ? (
            <p className="empty-cart">Your cart is empty</p>
          ) : (
            <>
              <div className="cart-items">
                {cart.map(item => (
                  <div key={item.id} className="cart-item">
                    <div className="cart-item-info">
                      <h4>{item.name}</h4>
                      <span>${item.price} x {item.qty}</span>
                    </div>
                    <div className="cart-item-total">
                      ${(item.price * item.qty).toFixed(2)}
                      <button onClick={() => removeFromCart(item.id)}>Remove</button>
                    </div>
                  </div>
                ))}
              </div>
              <div className="cart-summary">
                <div className="cart-total">
                  <span>Total:</span>
                  <span>${cartTotal.toFixed(2)}</span>
                </div>
                <button className="checkout-btn">Proceed to Checkout</button>
              </div>
            </>
          )}
          <button className="continue-shopping" onClick={() => setActiveTab('products')}>
            Continue Shopping
          </button>
        </div>
      )}
    </div>
  )
}

export default App
