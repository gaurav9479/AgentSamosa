import { useState, useEffect, useRef } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar } from 'recharts'

const COLORS = ['#3b82f6', '#22c55e', '#f97316', '#8b5cf6', '#ef4444', '#06b6d4']

function App() {
  // View mode: 'customer' (marketplace) or 'admin' (shop owner)
  const [viewMode, setViewMode] = useState('customer')

  // Customer view states
  const [shopCategories, setShopCategories] = useState([])
  const [shops, setShops] = useState([])
  const [selectedShopCategory, setSelectedShopCategory] = useState(null)
  const [selectedShop, setSelectedShop] = useState(null)
  const [shopProducts, setShopProducts] = useState([])
  const [cart, setCart] = useState([])
  const [searchQuery, setSearchQuery] = useState('')

  // Admin view states
  const [currentShop, setCurrentShop] = useState(null) // Shop being managed
  const [activeTab, setActiveTab] = useState('dashboard')
  const [dashboardStats, setDashboardStats] = useState({})
  const [products, setProducts] = useState([])
  const [orders, setOrders] = useState([])
  const [lowStockProducts, setLowStockProducts] = useState([])
  const [categories, setCategories] = useState([])

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
    if (currentShop && viewMode === 'admin') {
      fetchAdminData()
    }
  }, [currentShop, viewMode])

  const connectWebSocket = () => {
    const ws = new WebSocket(`ws://${window.location.hostname}:8000/api/ws`)
    ws.onopen = () => { setIsConnected(true); addLog('Connected to server', 'info') }
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data)
      if (data.type === 'action_result' || data.type === 'data_update') {
        if (currentShop) fetchAdminData()
        if (selectedShop) fetchShopProducts(selectedShop)
      }
    }
    ws.onclose = () => { setIsConnected(false); setTimeout(connectWebSocket, 3000) }
    wsRef.current = ws
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

  const fetchAdminData = async () => {
    if (!currentShop) return
    try {
      const [dashRes, prodRes, ordRes, lowRes, catRes] = await Promise.all([
        fetch(`/api/shops/${currentShop.id}/dashboard`),
        fetch(`/api/shops/${currentShop.id}/products?include_inactive=true`),
        fetch(`/api/shops/${currentShop.id}/orders`),
        fetch(`/api/shops/${currentShop.id}/low-stock`),
        fetch('/api/categories')
      ])
      if (dashRes.ok) setDashboardStats(await dashRes.json())
      if (prodRes.ok) setProducts(await prodRes.json())
      if (ordRes.ok) setOrders(await ordRes.json())
      if (lowRes.ok) setLowStockProducts(await lowRes.json())
      if (catRes.ok) setCategories(await catRes.json())
    } catch (err) { console.error('Error fetching admin data:', err) }
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
        body: JSON.stringify({ command: command.trim() })
      })
      const data = await res.json()
      if (res.ok) {
        addLog(`Done: ${data.message || 'Command executed'}`, 'success')
        fetchAdminData()
      } else {
        addLog(`Error: ${data.detail || 'Failed'}`, 'error')
      }
    } catch (err) { addLog(`Error: ${err.message}`, 'error') }
    finally { setIsProcessing(false); setCommand('') }
  }

  // Product CRUD
  const createProduct = async (e) => {
    e.preventDefault()
    if (!currentShop) return
    try {
      const data = {
        name: productForm.name,
        price: parseFloat(productForm.price),
        shop_id: currentShop.id,
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
        fetchAdminData()
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
        fetchAdminData()
      }
    } catch (err) { addLog(`Error: ${err.message}`, 'error') }
  }

  const deleteProduct = async (id) => {
    if (!confirm('Delete this product?')) return
    await fetch(`/api/products/${id}`, { method: 'DELETE' })
    addLog('Product deleted', 'success')
    fetchAdminData()
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

  // Enter shop as admin
  const enterShopAsAdmin = (shop) => {
    setCurrentShop(shop)
    setViewMode('admin')
    setActiveTab('dashboard')
  }

  // Filtered products for search
  const filteredProducts = searchQuery
    ? shopProducts.filter(p =>
        p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.brand?.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : shopProducts

  // ============== CUSTOMER VIEW (MARKETPLACE) ==============
  if (viewMode === 'customer') {
    // Home - Show shop categories
    if (!selectedShopCategory && !selectedShop) {
      return (
        <div className="marketplace">
          <header className="marketplace-header">
            <h1>KommandAI Marketplace</h1>
            <p>Shop from your favorite stores</p>
          </header>

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
                <button className="admin-btn" onClick={(e) => { e.stopPropagation(); enterShopAsAdmin(shop) }}>
                  Manage Shop
                </button>
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
            <button className="admin-btn" onClick={() => enterShopAsAdmin(shop)}>Manage Shop</button>
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
  }

  // ============== ADMIN VIEW (SHOP OWNER) ==============
  return (
    <div className="admin-app">
      <header className="admin-header">
        <div className="header-left">
          <button className="back-btn" onClick={() => { setViewMode('customer'); setCurrentShop(null) }}>
            ← Marketplace
          </button>
          <div>
            <h1>{currentShop?.name || 'Shop Admin'}</h1>
            <p>Shop Management Dashboard</p>
          </div>
        </div>
        <div className="header-right">
          <div className="connection-status">
            <span className={`dot ${isConnected ? 'connected' : ''}`}></span>
            {isConnected ? 'Live' : 'Offline'}
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

          {/* Activity Log */}
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

export default App
