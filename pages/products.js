import Head from 'next/head';
import { useRouter } from 'next/router';
import { useEffect, useState } from 'react';
import ProductCard from '../components/ProductCard';
import StoreLayout from '../components/StoreLayout';
import { categories, fallbackProducts, requestApi } from '../lib/store';

export default function Products() {
  const router = useRouter();
  const [products, setProducts] = useState(fallbackProducts);
  const [active, setActive] = useState('All');
  const [message, setMessage] = useState('');

  useEffect(() => {
    requestApi('/api/products')
      .then((data) => setProducts(data.length ? data : fallbackProducts))
      .catch(() => setMessage('Backend offline — showing sample catalog.'));
  }, []);

  useEffect(() => {
    if (router.query.category) setActive(router.query.category);
  }, [router.query.category]);

  const visible = active === 'All' ? products : products.filter((p) => p.category === active);

  return (
    <StoreLayout>
      <Head><title>Products | Brand Store</title></Head>
      <main>
        <section className="section">
          <div className="section-heading">
            <div><p className="eyebrow">Catalog</p><h2>All products</h2></div>
          </div>
          <div className="filter-row">
            {categories.map((cat) => (
              <button key={cat} className={`filter-chip${active === cat ? ' active' : ''}`} onClick={() => setActive(cat)}>
                {cat}
              </button>
            ))}
          </div>
          {message && <div className="status-message">{message}</div>}
          <div className="product-grid">
            {visible.map((p) => <ProductCard key={p.id} product={p} onMessage={setMessage} />)}
          </div>
        </section>
      </main>
    </StoreLayout>
  );
}
