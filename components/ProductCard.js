import { useState } from 'react';
import { currency, getStoredAuth, requestApi } from '../lib/store';

export default function ProductCard({ product, onMessage }) {
  const [adding, setAdding] = useState(false);

  async function addToCart() {
    const auth = getStoredAuth();

    if (!auth.token) {
      onMessage?.('Please sign in before adding items to cart.');
      return;
    }

    setAdding(true);
    try {
      await requestApi(
        '/api/cart',
        {
          method: 'POST',
          body: JSON.stringify({ product_id: product.id, quantity: 1 }),
        },
        auth.token
      );
      onMessage?.(`${product.name} added to cart.`);
    } catch (error) {
      onMessage?.(error.message);
    } finally {
      setAdding(false);
    }
  }

  return (
    <article className="product-card">
      <div className="product-image-wrap">
        <img src={product.image_url} alt={product.name} />
        <span>{product.category || 'Featured'}</span>
      </div>
      <div className="product-body">
        <div>
          <h3>{product.name}</h3>
          <p>{product.description}</p>
        </div>
        <div className="product-meta">
          <strong>{currency(product.price)}</strong>
          <span>{product.stock} in stock</span>
        </div>
        <button className="button primary full" type="button" onClick={addToCart} disabled={adding}>
          {adding ? 'Adding...' : 'Add to cart'}
        </button>
      </div>
    </article>
  );
}
