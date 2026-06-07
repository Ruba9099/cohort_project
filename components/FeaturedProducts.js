const products = new Array(8).fill(0).map((_, i) => ({
  id: i + 1,
  title: `Heritage ${i + 1}`,
  price: (250 + i * 25).toFixed(0),
  img: `https://images.unsplash.com/photo-1519744792095-2f2205e87b6f?w=600&q=60&auto=format&fit=crop&ixid=${i}`
}));

export default function FeaturedProducts() {
  return (
    <section className="featured container" id="shop">
      <h2>Best Sellers</h2>
      <div className="carousel" aria-label="Best sellers">
        {products.map((p) => (
          <article className="product-card" key={p.id}>
            <img src={p.img} alt={p.title} />
            <div className="meta">
              <h3>{p.title}</h3>
              <div className="price">${p.price}</div>
              <div className="rating">★★★★★</div>
              <button className="btn">Add to Cart</button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
