import { useState, useEffect, useRef } from 'react'

const EXAMPLE_COMMANDS = [
  "Create a product called MacBook Pro with price 2499",
  "Show all products",
  "Update product 1 price to 1999",
  "Create order for product 1 quantity 2 for John Doe",
  "List all orders",
  "Cancel order 1",
  "Delete product 2",
]

function App() {
  const [command, setCommand] = useState('')
  const [products, setProducts] = useState([])
  const [orders, setOrders] = useState([])
  const [logs, setLogs] = useState([])
  const [isConnected, setIsConnected] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [confirmation, setConfirmation] = useState(null)
  const [activeTab, setActiveTab] = useState('command')
  const [stats, setStats] = useState({ products: 0, orders: 0, pending: 0, revenue: 0 })
  const wsRef = useRef(null)

  // Manual form states
  const [productForm, setProductForm] = useState({ name: '', price: '', quantity: '', description: '' })
  const [orderForm, setOrderForm] = useState({ product_id: '', quantity: '', customer_name: '', customer_email: '' })

  // Edit modal state
  const [editingProduct, setEditingProduct] = useState(null)
  const [editForm, setEditForm] = useState({ name: '', price: '', quantity: '', description: '' })

  useEffect(() => {
    connectWebSocket()
    fetchData()
    return () => {
      if (wsRef.current) wsRef.current.close()
    }
  }, [])

  useEffect(() => {
    // Calculate stats
    const totalRevenue = orders.reduce((sum, o) => o.status !== 'cancelled' ? sum + o.total_amount : sum, 0)
    const pendingOrders = orders.filter(o => o.status === 'pending').length
    setStats({
      products: products.length,
      orders: orders.length,
      pending: pendingOrders,
      revenue: totalRevenue
    })
  }, [products, orders])

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

    ws.onerror = () => {
      setIsConnected(false)
    }

    wsRef.current = ws
  }

  const handleWebSocketMessage = (data) => {
    if (data.type === 'action_result') {
      addLog(`${data.action}: ${data.message}`, data.success ? 'success' : 'error')
      fetchData()
    } else if (data.type === 'data_update') {
      addLog(`${data.entity} ${data.operation}`, 'info')
      fetchData()
    }
  }

  const fetchData = async () => {
    try {
      const [productsRes, ordersRes] = await Promise.all([
        fetch('/api/products'),
        fetch('/api/orders')
      ])
      if (productsRes.ok) setProducts(await productsRes.json())
      if (ordersRes.ok) setOrders(await ordersRes.json())
    } catch (err) {
      console.error('Failed to fetch data:', err)
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
        setConfirmation({
          id: data.confirmation_id,
          message: data.message,
          action: data.action
        })
      } else {
        addLog(`${data.action}: ${data.message}`, data.success ? 'success' : 'error')
      }

      setCommand('')
      fetchData()
    } catch (err) {
      addLog(`Error: ${err.message}`, 'error')
    } finally {
      setIsLoading(false)
    }
  }

  const handleConfirm = async (confirmed) => {
    if (confirmed && confirmation) {
      try {
        const res = await fetch(`/api/command/confirm/${confirmation.id}`, {
          method: 'POST'
        })
        const data = await res.json()
        addLog(`${data.action}: ${data.message}`, data.success ? 'success' : 'error')
        fetchData()
      } catch (err) {
        addLog(`Error: ${err.message}`, 'error')
      }
    }
    setConfirmation(null)
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') sendCommand()
  }

  const useExampleCommand = (cmd) => {
    setCommand(cmd)
  }

  // Manual form handlers
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
      }
    } catch (err) {
      addLog(`Error: ${err.message}`, 'error')
    }
  }

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
    } catch (err) {
      addLog(`Error: ${err.message}`, 'error')
    }
  }

  // Edit product handlers
  const openEditModal = (product) => {
    setEditingProduct(product)
    setEditForm({
      name: product.name,
      price: product.price.toString(),
      quantity: (product.quantity || 0).toString(),
      description: product.description || ''
    })
  }

  const closeEditModal = () => {
    setEditingProduct(null)
    setEditForm({ name: '', price: '', quantity: '', description: '' })
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
        closeEditModal()
        fetchData()
      } else {
        addLog('Failed to update product', 'error')
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
          <div className="stat-value">{stats.orders}</div>
          <div className="stat-label">Total Orders</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats.pending}</div>
          <div className="stat-label">Pending</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">${stats.revenue.toFixed(2)}</div>
          <div className="stat-label">Revenue</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="tabs">
        <button
          className={`tab ${activeTab === 'command' ? 'active' : ''}`}
          onClick={() => setActiveTab('command')}
        >
          AI Command
        </button>
        <button
          className={`tab ${activeTab === 'products' ? 'active' : ''}`}
          onClick={() => setActiveTab('products')}
        >
          Products
        </button>
        <button
          className={`tab ${activeTab === 'orders' ? 'active' : ''}`}
          onClick={() => setActiveTab('orders')}
        >
          Orders
        </button>
      </div>

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
                onKeyPress={handleKeyPress}
                disabled={isLoading}
              />
              <button
                className="send-btn"
                onClick={sendCommand}
                disabled={isLoading || !command.trim()}
              >
                {isLoading ? 'Processing...' : 'Execute'}
              </button>
            </div>
          </div>

          <div className="examples-section">
            <h3>Example Commands</h3>
            <div className="examples-grid">
              {EXAMPLE_COMMANDS.map((cmd, i) => (
                <button key={i} className="example-btn" onClick={() => useExampleCommand(cmd)}>
                  {cmd}
                </button>
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
                      <p>
                        <span className="price">${product.price}</span>
                        {' · '}Qty: {product.quantity}
                      </p>
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
                      <p>
                        {order.customer_name}
                        {' · '}
                        <span className="price">${order.total_amount}</span>
                      </p>
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
                <input
                  type="text"
                  value={productForm.name}
                  onChange={(e) => setProductForm({...productForm, name: e.target.value})}
                  required
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Price *</label>
                  <input
                    type="number"
                    step="0.01"
                    value={productForm.price}
                    onChange={(e) => setProductForm({...productForm, price: e.target.value})}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Quantity</label>
                  <input
                    type="number"
                    value={productForm.quantity}
                    onChange={(e) => setProductForm({...productForm, quantity: e.target.value})}
                  />
                </div>
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={productForm.description}
                  onChange={(e) => setProductForm({...productForm, description: e.target.value})}
                />
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
                    <tr>
                      <th>ID</th>
                      <th>Name</th>
                      <th>Price</th>
                      <th>Qty</th>
                      <th>Actions</th>
                    </tr>
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
                <select
                  value={orderForm.product_id}
                  onChange={(e) => setOrderForm({...orderForm, product_id: e.target.value})}
                  required
                >
                  <option value="">Select a product</option>
                  {products.map(p => (
                    <option key={p.id} value={p.id}>{p.name} - ${p.price}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Quantity *</label>
                <input
                  type="number"
                  min="1"
                  value={orderForm.quantity}
                  onChange={(e) => setOrderForm({...orderForm, quantity: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Customer Name *</label>
                <input
                  type="text"
                  value={orderForm.customer_name}
                  onChange={(e) => setOrderForm({...orderForm, customer_name: e.target.value})}
                  required
                />
              </div>
              <div className="form-group">
                <label>Customer Email</label>
                <input
                  type="email"
                  value={orderForm.customer_email}
                  onChange={(e) => setOrderForm({...orderForm, customer_email: e.target.value})}
                />
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
                    <tr>
                      <th>ID</th>
                      <th>Customer</th>
                      <th>Product</th>
                      <th>Unit Price</th>
                      <th>Qty</th>
                      <th>Total</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
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
                        <td>
                          {o.status === 'pending' && (
                            <button className="delete-btn" onClick={() => cancelOrder(o.id)}>Cancel</button>
                          )}
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
                <input
                  type="text"
                  value={editForm.name}
                  onChange={(e) => setEditForm({...editForm, name: e.target.value})}
                  required
                />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Price *</label>
                  <input
                    type="number"
                    step="0.01"
                    value={editForm.price}
                    onChange={(e) => setEditForm({...editForm, price: e.target.value})}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Quantity</label>
                  <input
                    type="number"
                    value={editForm.quantity}
                    onChange={(e) => setEditForm({...editForm, quantity: e.target.value})}
                  />
                </div>
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={editForm.description}
                  onChange={(e) => setEditForm({...editForm, description: e.target.value})}
                />
              </div>
              <div className="modal-buttons">
                <button type="button" className="cancel-btn" onClick={closeEditModal}>
                  Cancel
                </button>
                <button type="submit" className="confirm-btn save-btn">
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {confirmation && (
        <div className="confirmation-modal">
          <div className="modal-content">
            <h3>Confirmation Required</h3>
            <p>{confirmation.message}</p>
            <div className="modal-buttons">
              <button className="cancel-btn" onClick={() => handleConfirm(false)}>
                Cancel
              </button>
              <button className="confirm-btn" onClick={() => handleConfirm(true)}>
                Confirm
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
