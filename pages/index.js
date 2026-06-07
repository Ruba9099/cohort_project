import Head from 'next/head';
import Link from 'next/link';
import { useEffect, useState } from 'react';
import ProductCard from '../components/ProductCard';
import StoreLayout from '../components/StoreLayout';
import { fallbackProducts, requestApi } from '../lib/store';

export default function Home() {
  const [products, setProducts] = useState(fallbackProducts);
  const [message, setMessage] = useState('');

  useEffect(() => {
    requestApi('/api/products')
      .then((data) => setProducts(data.length ? data : fallbackProducts))
      .catch(() => setMessage('Backend is offline, showing sample catalog.'));
  }, []);

  const featured = products.slice(0, 8);
  const categories = ['Apparel', 'Footwear', 'Bags', 'Tech'];

  return (
    <StoreLayout>
      <Head>
        <title>Brand Store | Premium Ecommerce</title>
        <meta name="description" content="A polished full-stack ecommerce store with catalog, cart, checkout, and orders." />
      </Head>

      <main>
        <section className="hero">
          <div className="hero-copy">
            <p className="eyebrow">Curated essentials</p>
            <h1>A premium store for everyday products that actually earn their shelf space.</h1>
            <p>
              Shop a complete catalog, create an account, add items to cart, and checkout with the
              Python backend API.
            </p>
            <div className="hero-actions">
              <Link className="button primary" href="/products">
                Shop all products
              </Link>
              <Link className="button secondary" href="/checkout">
                Checkout
              </Link>
            </div>
          </div>
          <div className="hero-image" aria-label="Premium shopping products" />
        </section>

        {message && <div className="status-message">{message}</div>}

        <section className="metric-strip" aria-label="Store highlights">
          <div>
            <strong>30</strong>
            <span>catalog products</span>
          </div>
          <div>
            <strong>8</strong>
            <span>shopping categories</span>
          </div>
          <div>
            <strong>24h</strong>
            <span>order processing</span>
          </div>
          <div>
            <strong>2 yr</strong>
            <span>warranty support</span>
          </div>
        </section>

        <section className="section">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Departments</p>
              <h2>Shop by category</h2>
            </div>
            <Link className="text-button" href="/products">
              View catalog
            </Link>
          </div>
          <div className="category-grid">
            {categories.map((category, index) => (
              <Link className={`category-tile tile-${index + 1}`} href={`/products?category=${category}`} key={category}>
                <span>{category}</span>
              </Link>
            ))}
          </div>
        </section>

        <section className="section">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Best sellers</p>
              <h2>Popular right now</h2>
            </div>
            <Link className="text-button" href="/products">
              Browse more
            </Link>
          </div>
          <div className="product-grid">
            {featured.map((product) => (
              <ProductCard product={product} key={product.id} onMessage={setMessage} />
            ))}
          </div>
        </section>
      </main>
    </StoreLayout>
  );
}
