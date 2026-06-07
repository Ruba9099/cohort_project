import Head from 'next/head';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import StoreLayout from '../components/StoreLayout';
import { currency, getStoredAuth, requestApi } from '../lib/store';

export default function Cart() {
  const [cart, setCart] = useState({ items: [], total: 0 });
  const [message, setMessage] = useState('');

  useEffect(() => {
    const { token } = getStoredAuth();
    if (!token) { setMessage('Please sign in to view your cart.'); return; }
    requestApi('/api/cart', {}, token).then(setCart).catch((e) => setMessage(e.message));
  }, []);

  async function updateQty(productId, quantity) {
    const { token } = getStoredAuth();
    try {
      const data = quantity < 1
        ? await requestApi(`/api/cart/${productId}`, { method: 'DELETE' }, token)
        : await requestApi(`/api/cart/${productId}`, { method: 'PUT', body: JSON.stringify({ quantity }) }, token);
      setCart(data);
    } catch (e) { setMessage(e.message); }
  }

  return (
    <StoreLayout>
      <Head><title>Cart | Brand Store</title></Head>
      <main>
        <section className="section">
          <div className="section-heading">
            <div><p className="eyebrow">Shopping</p><h2>Your cart</h2></div>
            <Link className="text-button" href="/products">Continue shopping</Link>
          </div>
          {message && <div className="status-message">{message}</div>}
          {cart.items.length === 0 ? (
            <div className="empty-state">Cart is empty. <Link href="/products">Browse products →</Link></div>
          ) : (
            <>
              <div style={{ display: 'grid', gap: 14 }}>
                {cart.items.map((item) => (
                  <div className="cart-item" key={item.product_id}>
                    <img src={item.image_url || 'https://placehold.co/86x86?text=P'} alt={item.name} />
                    <div>
                      <h3>{item.name}</h3>
                      <p>{currency(item.subtotal)}</p>
                      <div className="quantity-row">
                        <button onClick={() => updateQty(item.product_id, item.quantity - 1)}>−</button>
                        <span>{item.quantity}</span>
                        <button onClick={() => updateQty(item.product_id, item.quantity + 1)}>+</button>
                        <button onClick={() => updateQty(item.product_id, 0)}>Remove</button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              <div className="cart-total" style={{ marginTop: 20, paddingTop: 16, borderTop: '1px solid var(--line)' }}>
                <span>Total</span><strong>{currency(cart.total)}</strong>
              </div>
              <div style={{ marginTop: 20 }}>
                <Link className="button primary" href="/checkout">Proceed to checkout →</Link>
              </div>
            </>
          )}
        </section>
      </main>
    </StoreLayout>
  );
}
