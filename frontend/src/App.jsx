import { useState, useEffect, useRef } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar } from 'recharts'

const EXAMPLE_COMMANDS = [
  "Create a product called MacBook Pro with price 2499",
  "Show all products",
  "Create order for product 1 quantity 2 for John Doe",
  "List all orders",
  "Create a customer named John Smith with email john@email.com",
  "List all customers",
  "Search for customers named John",
]

const COLORS = ['#3b82f6', '#22c55e', '#f97316', '#8b5cf6', '#ef4444']

function App() {
  const [command, setCommand] = useState('')
  const [products, setProducts] = useState([])
  const [orders, setOrders] = useState([])
  const [customers, setCustomers] = useState([])
  const [logs, setLogs] = useState([])
  const [isConnected, setIsConnected] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [confirmation, setConfirmation] = useState(null)
  const [activeTab, setActiveTab] = useState('analytics')
  const [stats, setStats] = useState({ products: 0, orders: 0, pending: 0, revenue: 0, customers: 0 })
  const wsRef = useRef(null)

  // Analytics data
  const [revenueData, setRevenueData] = useState([])
  const [orderStatusData, setOrderStatusData] = useState([])
  const [topProducts, setTopProducts] = useState([])
  const [topCustomers, setTopCustomers] = useState([])
  const [monthlyComparison, setMonthlyComparison] = useState(null)

  // Form states
  const [productForm, setProductForm] = useState({ name: '', price: '', quantity: '', description: '' })
  const [orderForm, setOrderForm] = useState({ product_id: '', quantity: '', customer_name: '', customer_email: '' })
  const [customerForm, setCustomerForm] = useState({ name: '', email: '', phone: '', address: '' })

  // Edit modal states
  const [editingProduct, setEditingProduct] = useState(null)
  const [editForm, setEditForm] = useState({ name: '', price: '', quantity: '', description: '' })
  const [editingCustomer, setEditingCustomer] = useState(null)
  const [editCustomerForm, setEditCustomerForm] = useState({ name: '', email: '', phone: '', address: '' })

  useEffect(() => {
    connectWebSocket()
    fetchData()
    fetchAnalytics()
    return () => {
      if (wsRef.current) wsRef.current.close()
    }
  }, [])

  useEffect(() => {
    const totalRevenue = orders.reduce((sum, o) => o.status !== 'cancelled' ? sum + o.total_amount : sum, 0)
    const pendingOrders = orders.filter(o => o.status === 'pending').length
    setStats({
      products: products.length,
      orders: orders.length,
      pending: pendingOrders,
      revenue: totalRevenue,
      customers: customers.length
    })
  }, [products, orders, customers])

  const connectWebSocket = () => {
    const ws = new WebSocket(`ws://${window.location.hostname}:8000/api/ws`)
    ws.onopen = () => {
      setIsConnected(true)
      addLog('Connected to server', 'info')
    }
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      handleWebSocketMessage(data)
    }
    ws.onclose = () => {
      setIsConnected(false)
      addLog('Disconnected from server', 'error')
      setTimeout(connectWebSocket, 3000)
    }
    ws.onerror = () => setIsConnected(false)
    wsRef.current = ws
  }

  const handleWebSocketMessage = (data) => {
    if (data.type === 'action_result') {
      addLog(`${data.action}: ${data.message}`, data.success ? 'success' : 'error')
      fetchData()
      fetchAnalytics()
    } else if (data.type === 'data_update') {
      addLog(`${data.entity} ${data.operation}`, 'info')
      fetchData()
      fetchAnalytics()
    }
  }

  const fetchData = async () => {
    try {
      const [productsRes, ordersRes, customersRes] = await Promise.all([
        fetch('/api/products'),
        fetch('/api/orders'),
        fetch('/api/customers')
      ])
      if (productsRes.ok) setProducts(await productsRes.json())
      if (ordersRes.ok) setOrders(await ordersRes.json())
      if (customersRes.ok) setCustomers(await customersRes.json())
    } catch (err) {
      console.error('Failed to fetch data:', err)
    }
  }

  const fetchAnalytics = async () => {
    try {
      const [revenueRes, statusRes, topProdRes, topCustRes, monthlyRes] = await Promise.all([
        fetch('/api/analytics/revenue?days=7'),
        fetch('/api/analytics/order-status'),
        fetch('/api/analytics/top-products?limit=5'),
        fetch('/api/analytics/top-customers?limit=5'),
        fetch('/api/analytics/monthly-comparison')
      ])
      if (revenueRes.ok) setRevenueData(await revenueRes.json())
      if (statusRes.ok) setOrderStatusData(await statusRes.json())
      if (topProdRes.ok) setTopProducts(await topProdRes.json())
      if (topCustRes.ok) setTopCustomers(await topCustRes.json())
      if (monthlyRes.ok) setMonthlyComparison(await monthlyRes.json())
    } catch (err) {
      console.error('Failed to fetch analytics:', err)
    }
  }

  const addLog = (message, type = 'info') => {
    const time = new Date().toLocaleTimeString()
    setLogs(prev => [{ message, type, time }, ...prev].slice(0, 50))
  }

  const sendCommand = async () => {
    if (!command.trim() || isLoading) return
    setIsLoading(true)
    addLog(`Command: ${command}`, 'info')
    try {
      const res = await fetch('/api/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: command })
      })
      const data = await res.json()
      if (data.requires_confirmation) {
        setConfirmation({ id: data.confirmation_id, message: data.message, action: data.action })
      } else {
        addLog(`${data.action}: ${data.message}`, data.success ? 'success' : 'error')
      }
      setCommand('')
      fetchData()
      fetchAnalytics()
    } catch (err) {
      addLog(`Error: ${err.message}`, 'error')
    } finally {
      setIsLoading(false)
    }
  }

  const handleConfirm = async (confirmed) => {
    if (confirmed && confirmation) {
      try {
        const res = await fetch(`/api/command/confirm/${confirmation.id}`, { method: 'POST' })
        const data = await res.json()
        addLog(`${data.action}: ${data.message}`, data.success ? 'success' : 'error')
        fetchData()
        fetchAnalytics()
      } catch (err) {
        addLog(`Error: ${err.message}`, 'error')
      }
    }
    setConfirmation(null)
  }

  // Product handlers
  const createProduct = async (e) => {
    e.preventDefault()
    try {
      const res = await fetch('/api/products', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: productForm.name,
          price: parseFloat(productForm.price),
          quantity: parseInt(productForm.quantity) || 0,
          description: productForm.description || null
        })
      })
      if (res.ok) {
        addLog(`Product "${productForm.name}" created`, 'success')
        setProductForm({ name: '', price: '', quantity: '', description: '' })
        fetchData()
        fetchAnalytics()
      }
    } catch (err) {
      addLog(`Error: ${err.message}`, 'error')
    }
  }

  const deleteProduct = async (id) => {
    if (!confirm('Delete this product?')) return
    try {
      await fetch(`/api/products/${id}`, { method: 'DELETE' })
      addLog(`Product ${id} deleted`, 'success')
      fetchData()
      fetchAnalytics()
    } catch (err) {
      addLog(`Error: ${err.message}`, 'error')
    }
  }

  const openEditModal = (product) => {
    setEditingProduct(product)
    setEditForm({
      name: product.name,
      price: product.price.toString(),
      quantity: (product.quantity || 0).toString(),
      description: product.description || ''
    })
  }

  const updateProduct = async (e) => {
    e.preventDefault()
    if (!editingProduct) return
    try {
      const res = await fetch(`/api/products/${editingProduct.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: editForm.name,
          price: parseFloat(editForm.price),
          quantity: parseInt(editForm.quantity) || 0,
          description: editForm.description || null
        })
      })
      if (res.ok) {
        addLog(`Product "${editForm.name}" updated`, 'success')
        setEditingProduct(null)
        fetchData()
        fetchAnalytics()
      }
    } catch (err) {
      addLog(`Error: ${err.message}`, 'error')
    }
  }

  // Order handlers
  const createOrder = async (e) => {
    e.preventDefault()
    try {
      const res = await fetch('/api/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_id: parseInt(orderForm.product_id),
          quantity: parseInt(orderForm.quantity),
          customer_name: orderForm.customer_name,
          customer_email: orderForm.customer_email || null
        })
      })
      if (res.ok) {
        addLog(`Order created for ${orderForm.customer_name}`, 'success')
        setOrderForm({ product_id: '', quantity: '', customer_name: '', customer_email: '' })
        fetchData()
        fetchAnalytics()
      }
    } catch (err) {
      addLog(`Error: ${err.message}`, 'error')
    }
  }

  const cancelOrder = async (id) => {
    if (!confirm('Cancel this order?')) return
    try {
      await fetch(`/api/orders/${id}/cancel`, { method: 'POST' })
      addLog(`Order ${id} cancelled`, 'success')
      fetchData()
      fetchAnalytics()
    } catch (err) {
      addLog(`Error: ${err.message}`, 'error')
    }
  }

  // Customer handlers
  const createCustomer = async (e) => {
    e.preventDefault()
    try {
      const res = await fetch('/api/customers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: customerForm.name,
          email: customerForm.email,
          phone: customerForm.phone || null,
          address: customerForm.address || null
        })
      })
      if (res.ok) {
        addLog(`Customer "${customerForm.name}" created`, 'success')
        setCustomerForm({ name: '', email: '', phone: '', address: '' })
        fetchData()
        fetchAnalytics()
      } else {
        const err = await res.json()
        addLog(`Error: ${err.detail}`, 'error')
      }
    } catch (err) {
      addLog(`Error: ${err.message}`, 'error')
    }
  }

  const deleteCustomer = async (id) => {
    if (!confirm('Delete this customer?')) return
    try {
      await fetch(`/api/customers/${id}`, { method: 'DELETE' })
      addLog(`Customer ${id} deleted`, 'success')
      fetchData()
      fetchAnalytics()
    } catch (err) {
      addLog(`Error: ${err.message}`, 'error')
    }
  }

  const openEditCustomerModal = (customer) => {
    setEditingCustomer(customer)
    setEditCustomerForm({
      name: customer.name,
      email: customer.email,
      phone: customer.phone || '',
      address: customer.address || ''
    })
  }

  const updateCustomer = async (e) => {
    e.preventDefault()
    if (!editingCustomer) return
    try {
      const res = await fetch(`/api/customers/${editingCustomer.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: editCustomerForm.name,
          email: editCustomerForm.email,
          phone: editCustomerForm.phone || null,
          address: editCustomerForm.address || null
        })
      })
      if (res.ok) {
        addLog(`Customer "${editCustomerForm.name}" updated`, 'success')
        setEditingCustomer(null)
        fetchData()
        fetchAnalytics()
      }
    } catch (err) {
      addLog(`Error: ${err.message}`, 'error')
    }
  }

  return (
    <div className="app">
      <header>
        <h1>AgentSamosa</h1>
        <p>Agentic AI Command & Control System</p>
        <div className="connection-status">
          <span className={`connection-dot ${isConnected ? 'connected' : ''}`}></span>
          {isConnected ? 'Connected' : 'Disconnected'}
        </div>
      </header>

      {/* Stats Dashboard */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{stats.products}</div>
          <div className="stat-label">Products</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.customers}</div>
          <div className="stat-label">Customers</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.orders}</div>
          <div className="stat-label">Orders</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">${stats.revenue.toFixed(2)}</div>
          <div className="stat-label">Revenue</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs">
        <button className={`tab ${activeTab === 'analytics' ? 'active' : ''}`} onClick={() => setActiveTab('analytics')}>
          Analytics
        </button>
        <button className={`tab ${activeTab === 'command' ? 'active' : ''}`} onClick={() => setActiveTab('command')}>
          AI Command
        </button>
        <button className={`tab ${activeTab === 'products' ? 'active' : ''}`} onClick={() => setActiveTab('products')}>
          Products
        </button>
        <button className={`tab ${activeTab === 'orders' ? 'active' : ''}`} onClick={() => setActiveTab('orders')}>
          Orders
        </button>
        <button className={`tab ${activeTab === 'customers' ? 'active' : ''}`} onClick={() => setActiveTab('customers')}>
          Customers
        </button>
      </div>

      {/* Analytics Tab */}
      {activeTab === 'analytics' && (
        <div className="analytics-container">
          {/* Monthly Comparison */}
          {monthlyComparison && (
            <div className="analytics-row">
              <div className="analytics-card comparison-card">
                <h3>This Month vs Last Month</h3>
                <div className="comparison-grid">
                  <div className="comparison-item">
                    <span className="comparison-label">This Month Revenue</span>
                    <span className="comparison-value">${monthlyComparison.this_month.revenue.toFixed(2)}</span>
                  </div>
                  <div className="comparison-item">
                    <span className="comparison-label">Last Month Revenue</span>
                    <span className="comparison-value">${monthlyComparison.last_month.revenue.toFixed(2)}</span>
                  </div>
                  <div className="comparison-item">
                    <span className="comparison-label">Growth</span>
                    <span className={`comparison-value ${monthlyComparison.growth_percentage >= 0 ? 'positive' : 'negative'}`}>
                      {monthlyComparison.growth_percentage >= 0 ? '+' : ''}{monthlyComparison.growth_percentage}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Charts Row */}
          <div className="analytics-row">
            <div className="analytics-card chart-card">
              <h3>Revenue (Last 7 Days)</h3>
              <div className="chart-container">
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={revenueData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="date" stroke="#94a3b8" tick={{ fill: '#94a3b8' }} />
                    <YAxis stroke="#94a3b8" tick={{ fill: '#94a3b8' }} />
                    <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
                    <Line type="monotone" dataKey="revenue" stroke="#3b82f6" strokeWidth={2} dot={{ fill: '#3b82f6' }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="analytics-card chart-card">
              <h3>Order Status Distribution</h3>
              <div className="chart-container">
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={orderStatusData}
                      dataKey="count"
                      nameKey="status"
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      label={({ status, count }) => `${status}: ${count}`}
                    >
                      {orderStatusData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Top Lists Row */}
          <div className="analytics-row">
            <div className="analytics-card">
              <h3>Top Selling Products</h3>
              <div className="top-list">
                {topProducts.length === 0 ? (
                  <p className="empty-state">No data yet</p>
                ) : (
                  topProducts.map((p, i) => (
                    <div key={i} className="top-item">
                      <span className="top-rank">#{i + 1}</span>
                      <span className="top-name">{p.product_name}</span>
                      <span className="top-stat">{p.total_sold} sold</span>
                      <span className="top-revenue">${p.total_revenue.toFixed(2)}</span>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="analytics-card">
              <h3>Top Customers</h3>
              <div className="top-list">
                {topCustomers.length === 0 ? (
                  <p className="empty-state">No data yet</p>
                ) : (
                  topCustomers.map((c, i) => (
                    <div key={i} className="top-item">
                      <span className="top-rank">#{i + 1}</span>
                      <span className="top-name">{c.name}</span>
                      <span className="top-stat">{c.total_orders} orders</span>
                      <span className="top-revenue">${c.total_spent.toFixed(2)}</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* AI Command Tab */}
      {activeTab === 'command' && (
        <>
          <div className="command-section">
            <div className="command-input-wrapper">
              <input
                type="text"
                className="command-input"
                placeholder='Type a command like "Create a product called iPhone with price 999"'
                value={command}
                onChange={(e) => setCommand(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendCommand()}
                disabled={isLoading}
              />
              <button className="send-btn" onClick={sendCommand} disabled={isLoading || !command.trim()}>
                {isLoading ? 'Processing...' : 'Execute'}
              </button>
            </div>
          </div>

          <div className="examples-section">
            <h3>Example Commands</h3>
            <div className="examples-grid">
              {EXAMPLE_COMMANDS.map((cmd, i) => (
                <button key={i} className="example-btn" onClick={() => setCommand(cmd)}>{cmd}</button>
              ))}
            </div>
          </div>

          <div className="main-content">
            <div className="panel">
              <h2>Products ({products.length})</h2>
              <div className="item-list">
                {products.length === 0 ? (
                  <div className="empty-state">No products yet</div>
                ) : (
                  products.map(product => (
                    <div key={product.id} className="item-card">
                      <h3>{product.name}</h3>
                      <p><span className="price">${product.price}</span> - Qty: {product.quantity}</p>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="panel">
              <h2>Orders ({orders.length})</h2>
              <div className="item-list">
                {orders.length === 0 ? (
                  <div className="empty-state">No orders yet</div>
                ) : (
                  orders.map(order => (
                    <div key={order.id} className="item-card">
                      <h3>Order #{order.id}</h3>
                      <p>{order.customer_name} - <span className="price">${order.total_amount}</span></p>
                      <span className={`status ${order.status}`}>{order.status}</span>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="panel logs">
              <h2>Activity Log</h2>
              <div className="log-list">
                {logs.length === 0 ? (
                  <div className="empty-state">No activity yet</div>
                ) : (
                  logs.map((log, i) => (
                    <div key={i} className={`log-item ${log.type}`}>
                      <div className="log-time">{log.time}</div>
                      <div>{log.message}</div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </>
      )}

      {/* Products Tab */}
      {activeTab === 'products' && (
        <div className="tab-content">
          <div className="form-panel">
            <h2>Add New Product</h2>
            <form onSubmit={createProduct}>
              <div className="form-group">
                <label>Name *</label>
                <input type="text" value={productForm.name} onChange={(e) => setProductForm({...productForm, name: e.target.value})} required />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Price *</label>
                  <input type="number" step="0.01" value={productForm.price} onChange={(e) => setProductForm({...productForm, price: e.target.value})} required />
                </div>
                <div className="form-group">
                  <label>Quantity</label>
                  <input type="number" value={productForm.quantity} onChange={(e) => setProductForm({...productForm, quantity: e.target.value})} />
                </div>
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea value={productForm.description} onChange={(e) => setProductForm({...productForm, description: e.target.value})} />
              </div>
              <button type="submit" className="submit-btn">Create Product</button>
            </form>
          </div>

          <div className="data-panel">
            <h2>All Products</h2>
            <div className="data-table">
              {products.length === 0 ? (
                <div className="empty-state">No products yet</div>
              ) : (
                <table>
                  <thead>
                    <tr><th>ID</th><th>Name</th><th>Price</th><th>Qty</th><th>Actions</th></tr>
                  </thead>
                  <tbody>
                    {products.map(p => (
                      <tr key={p.id}>
                        <td>{p.id}</td>
                        <td>{p.name}</td>
                        <td>${p.price}</td>
                        <td>{p.quantity}</td>
                        <td>
                          <button className="edit-btn" onClick={() => openEditModal(p)}>Edit</button>
                          <button className="delete-btn" onClick={() => deleteProduct(p.id)}>Delete</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Orders Tab */}
      {activeTab === 'orders' && (
        <div className="tab-content">
          <div className="form-panel">
            <h2>Create New Order</h2>
            <form onSubmit={createOrder}>
              <div className="form-group">
                <label>Product *</label>
                <select value={orderForm.product_id} onChange={(e) => setOrderForm({...orderForm, product_id: e.target.value})} required>
                  <option value="">Select a product</option>
                  {products.map(p => (<option key={p.id} value={p.id}>{p.name} - ${p.price}</option>))}
                </select>
              </div>
              <div className="form-group">
                <label>Quantity *</label>
                <input type="number" min="1" value={orderForm.quantity} onChange={(e) => setOrderForm({...orderForm, quantity: e.target.value})} required />
              </div>
              <div className="form-group">
                <label>Customer Name *</label>
                <input type="text" value={orderForm.customer_name} onChange={(e) => setOrderForm({...orderForm, customer_name: e.target.value})} required />
              </div>
              <div className="form-group">
                <label>Customer Email</label>
                <input type="email" value={orderForm.customer_email} onChange={(e) => setOrderForm({...orderForm, customer_email: e.target.value})} />
              </div>
              <button type="submit" className="submit-btn">Create Order</button>
            </form>
          </div>

          <div className="data-panel">
            <h2>All Orders</h2>
            <p className="order-note">Order prices are locked at the time of purchase</p>
            <div className="data-table">
              {orders.length === 0 ? (
                <div className="empty-state">No orders yet</div>
              ) : (
                <table>
                  <thead>
                    <tr><th>ID</th><th>Customer</th><th>Product</th><th>Unit Price</th><th>Qty</th><th>Total</th><th>Status</th><th>Actions</th></tr>
                  </thead>
                  <tbody>
                    {orders.map(o => (
                      <tr key={o.id}>
                        <td>#{o.id}</td>
                        <td>{o.customer_name}</td>
                        <td>{o.product_name || `Product #${o.product_id}`}</td>
                        <td>${o.unit_price || (o.total_amount / (o.quantity || 1)).toFixed(2)}</td>
                        <td>{o.quantity}</td>
                        <td className="price">${o.total_amount}</td>
                        <td><span className={`status ${o.status}`}>{o.status}</span></td>
                        <td>{o.status === 'pending' && (<button className="delete-btn" onClick={() => cancelOrder(o.id)}>Cancel</button>)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Customers Tab */}
      {activeTab === 'customers' && (
        <div className="tab-content">
          <div className="form-panel">
            <h2>Add New Customer</h2>
            <form onSubmit={createCustomer}>
              <div className="form-group">
                <label>Name *</label>
                <input type="text" value={customerForm.name} onChange={(e) => setCustomerForm({...customerForm, name: e.target.value})} required />
              </div>
              <div className="form-group">
                <label>Email *</label>
                <input type="email" value={customerForm.email} onChange={(e) => setCustomerForm({...customerForm, email: e.target.value})} required />
              </div>
              <div className="form-group">
                <label>Phone</label>
                <input type="text" value={customerForm.phone} onChange={(e) => setCustomerForm({...customerForm, phone: e.target.value})} />
              </div>
              <div className="form-group">
                <label>Address</label>
                <textarea value={customerForm.address} onChange={(e) => setCustomerForm({...customerForm, address: e.target.value})} />
              </div>
              <button type="submit" className="submit-btn">Add Customer</button>
            </form>
          </div>

          <div className="data-panel">
            <h2>All Customers</h2>
            <div className="data-table">
              {customers.length === 0 ? (
                <div className="empty-state">No customers yet</div>
              ) : (
                <table>
                  <thead>
                    <tr><th>ID</th><th>Name</th><th>Email</th><th>Phone</th><th>Orders</th><th>Total Spent</th><th>Actions</th></tr>
                  </thead>
                  <tbody>
                    {customers.map(c => (
                      <tr key={c.id}>
                        <td>{c.id}</td>
                        <td>{c.name}</td>
                        <td>{c.email}</td>
                        <td>{c.phone || '-'}</td>
                        <td>{c.total_orders}</td>
                        <td className="price">${c.total_spent.toFixed(2)}</td>
                        <td>
                          <button className="edit-btn" onClick={() => openEditCustomerModal(c)}>Edit</button>
                          <button className="delete-btn" onClick={() => deleteCustomer(c.id)}>Delete</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Edit Product Modal */}
      {editingProduct && (
        <div className="confirmation-modal">
          <div className="modal-content edit-modal">
            <h3>Edit Product</h3>
            <form onSubmit={updateProduct}>
              <div className="form-group">
                <label>Name *</label>
                <input type="text" value={editForm.name} onChange={(e) => setEditForm({...editForm, name: e.target.value})} required />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Price *</label>
                  <input type="number" step="0.01" value={editForm.price} onChange={(e) => setEditForm({...editForm, price: e.target.value})} required />
                </div>
                <div className="form-group">
                  <label>Quantity</label>
                  <input type="number" value={editForm.quantity} onChange={(e) => setEditForm({...editForm, quantity: e.target.value})} />
                </div>
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea value={editForm.description} onChange={(e) => setEditForm({...editForm, description: e.target.value})} />
              </div>
              <div className="modal-buttons">
                <button type="button" className="cancel-btn" onClick={() => setEditingProduct(null)}>Cancel</button>
                <button type="submit" className="confirm-btn save-btn">Save Changes</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Customer Modal */}
      {editingCustomer && (
        <div className="confirmation-modal">
          <div className="modal-content edit-modal">
            <h3>Edit Customer</h3>
            <form onSubmit={updateCustomer}>
              <div className="form-group">
                <label>Name *</label>
                <input type="text" value={editCustomerForm.name} onChange={(e) => setEditCustomerForm({...editCustomerForm, name: e.target.value})} required />
              </div>
              <div className="form-group">
                <label>Email *</label>
                <input type="email" value={editCustomerForm.email} onChange={(e) => setEditCustomerForm({...editCustomerForm, email: e.target.value})} required />
              </div>
              <div className="form-group">
                <label>Phone</label>
                <input type="text" value={editCustomerForm.phone} onChange={(e) => setEditCustomerForm({...editCustomerForm, phone: e.target.value})} />
              </div>
              <div className="form-group">
                <label>Address</label>
                <textarea value={editCustomerForm.address} onChange={(e) => setEditCustomerForm({...editCustomerForm, address: e.target.value})} />
              </div>
              <div className="modal-buttons">
                <button type="button" className="cancel-btn" onClick={() => setEditingCustomer(null)}>Cancel</button>
                <button type="submit" className="confirm-btn save-btn">Save Changes</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Confirmation Modal */}
      {confirmation && (
        <div className="confirmation-modal">
          <div className="modal-content">
            <h3>Confirmation Required</h3>
            <p>{confirmation.message}</p>
            <div className="modal-buttons">
              <button className="cancel-btn" onClick={() => handleConfirm(false)}>Cancel</button>
              <button className="confirm-btn" onClick={() => handleConfirm(true)}>Confirm</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
