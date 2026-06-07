import Head from 'next/head';
import { useEffect, useState } from 'react';
import StoreLayout from '../components/StoreLayout';
import { currency, getStoredAuth, requestApi } from '../lib/store';

export default function Orders() {
  const [orders, setOrders] = useState([]);
  const [message, setMessage] = useState('');

  useEffect(() => {
    const { token } = getStoredAuth();
    if (!token) { setMessage('Please sign in to view your orders.'); return; }
    requestApi('/api/orders', {}, token).then(setOrders).catch((e) => setMessage(e.message));
  }, []);

  return (
    <StoreLayout>
      <Head><title>Orders | Brand Store</title></Head>
      <main>
        <section className="section">
          <div className="section-heading">
            <div><p className="eyebrow">History</p><h2>Your orders</h2></div>
          </div>
          {message && <div className="status-message">{message}</div>}
          {orders.length === 0 && !message
            ? <div className="empty-state">No orders yet.</div>
            : orders.map((order) => (
              <div key={order.id} className="panel" style={{ marginBottom: 14, padding: 20 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <strong>Order #{order.id}</strong>
                    <p style={{ margin: '4px 0 0', color: 'var(--muted)', fontSize: '0.9rem' }}>{order.customer_name} · {order.phone}</p>
                    <p style={{ margin: '2px 0 0', color: 'var(--muted)', fontSize: '0.9rem' }}>{order.address}</p>
                  </div>
                  <strong style={{ fontSize: '1.1rem' }}>{currency(order.total)}</strong>
                </div>
              </div>
            ))}
        </section>
      </main>
    </StoreLayout>
  );
}
