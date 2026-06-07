import Link from 'next/link';
import { useEffect, useState } from 'react';
import { clearAuth, currency, getStoredAuth, requestApi } from '../lib/store';

export default function StoreLayout({ children }) {
  const [auth, setAuth] = useState({ token: '', user: null });
  const [cartCount, setCartCount] = useState(0);
  const [cartTotal, setCartTotal] = useState(0);

  useEffect(() => {
    const storedAuth = getStoredAuth();
    setAuth(storedAuth);

    if (storedAuth.token) {
      requestApi('/api/cart', {}, storedAuth.token)
        .then((cart) => {
          setCartCount(cart.items.reduce((sum, item) => sum + Number(item.quantity || 0), 0));
          setCartTotal(cart.total);
        })
        .catch(() => {
          setCartCount(0);
          setCartTotal(0);
        });
    }
  }, []);

  async function logout() {
    try {
      if (auth.token) {
        await requestApi('/api/auth/logout', { method: 'POST' }, auth.token);
      }
    } catch (error) {
      // Local logout still clears the browser session if the API is down.
    }

    clearAuth();
    setAuth({ token: '', user: null });
    setCartCount(0);
    setCartTotal(0);
  }

  return (
    <>
      <header className="site-header">
        <Link className="brand" href="/">
          Brand Store
        </Link>
        <nav className="nav-links" aria-label="Primary navigation">
          <Link href="/products">Shop</Link>
          <Link href="/cart">Cart</Link>
          <Link href="/checkout">Checkout</Link>
          <Link href="/orders">Orders</Link>
          <Link href="/account">Account</Link>
        </nav>
        <div className="header-actions">
          {auth.user ? (
            <button className="text-button" type="button" onClick={logout}>
              Sign out
            </button>
          ) : (
            <Link className="text-button" href="/account">
              Sign in
            </Link>
          )}
          <Link className="cart-button" href="/cart">
            Cart <span>{cartCount}</span>
          </Link>
        </div>
      </header>

      {children}

      <footer className="site-footer">
        <div>
          <strong>Brand Store</strong>
          <p>Premium everyday products, simple checkout, and fast order tracking.</p>
        </div>
        <div>
          <span>{cartCount} items</span>
          <strong>{currency(cartTotal)}</strong>
        </div>
      </footer>
    </>
  );
}
