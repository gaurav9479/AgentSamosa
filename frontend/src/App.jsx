import { useState, useEffect, useRef } from 'react'

function App() {
  const [command, setCommand] = useState('')
  const [products, setProducts] = useState([])
  const [orders, setOrders] = useState([])
  const [logs, setLogs] = useState([])
  const [isConnected, setIsConnected] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [confirmation, setConfirmation] = useState(null)
  const wsRef = useRef(null)

  // WebSocket connection
  useEffect(() => {
    connectWebSocket()
    fetchData()
    return () => {
      if (wsRef.current) wsRef.current.close()
    }
  }, [])

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

      <div className="command-section">
        <div className="command-input-wrapper">
          <input
            type="text"
            className="command-input"
            placeholder='Try: "Create a product called iPhone with price 999"'
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

      <div className="main-content">
        <div className="panel">
          <h2>Products</h2>
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
          <h2>Orders</h2>
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
