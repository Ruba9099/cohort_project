import Head from 'next/head';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import StoreLayout from '../components/StoreLayout';
import { currency, getStoredAuth, requestApi } from '../lib/store';

export default function Checkout() {
  const [cart, setCart] = useState({ items: [], total: 0 });
  const [form, setForm] = useState({ customer_name: '', address: '', phone: '' });
  const [message, setMessage] = useState('');
  const [success, setSuccess] = useState(null);

  useEffect(() => {
    const { token } = getStoredAuth();
    if (!token) { setMessage('Please sign in to checkout.'); return; }
    requestApi('/api/cart', {}, token).then(setCart).catch(() => {});
  }, []);

  async function submit(e) {
    e.preventDefault();
    const { token } = getStoredAuth();
    if (!token) { setMessage('Please sign in first.'); return; }
    try {
      const order = await requestApi('/api/orders/checkout', { method: 'POST', body: JSON.stringify(form) }, token);
      setSuccess(order);
      setCart({ items: [], total: 0 });
    } catch (err) { setMessage(err.message); }
  }

  if (success) return (
    <StoreLayout>
      <main>
        <section className="section">
          <p className="eyebrow">Confirmed</p>
          <h2>Order #{success.order_id} placed!</h2>
          <p style={{ color: 'var(--muted)', marginTop: 8 }}>Total: <strong>{currency(success.total)}</strong></p>
          <Link className="button primary" href="/orders" style={{ marginTop: 20, display: 'inline-flex' }}>View orders</Link>
        </section>
      </main>
    </StoreLayout>
  );

  return (
    <StoreLayout>
      <Head><title>Checkout | Brand Store</title></Head>
      <main>
        <section className="account-checkout">
          <section className="panel">
            <div className="section-heading compact">
              <p className="eyebrow">Order summary</p>
              <h2>{currency(cart.total)}</h2>
            </div>
            {cart.items.length === 0
              ? <div className="empty-state">Cart is empty.</div>
              : cart.items.map((item) => (
                <div key={item.product_id} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--line)' }}>
                  <span>{item.name} × {item.quantity}</span>
                  <strong>{currency(item.subtotal)}</strong>
                </div>
              ))}
          </section>
          <section className="panel">
            <div className="section-heading compact">
              <p className="eyebrow">Delivery</p><h2>Your details</h2>
            </div>
            {message && <div className="status-message">{message}</div>}
            <form className="form" onSubmit={submit}>
              <label>Name<input value={form.customer_name} onChange={(e) => setForm({ ...form, customer_name: e.target.value })} required /></label>
              <label>Address<textarea rows="3" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} required /></label>
              <label>Phone<input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} required /></label>
              <button className="button primary full" disabled={!cart.items.length}>Place order</button>
            </form>
          </section>
        </section>
      </main>
    </StoreLayout>
  );
}
