export default function Hero() {
  return (
    <section className="hero">
      <div className="hero-media">
        <img
          src="https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=1600&q=80&auto=format&fit=crop"
          alt="Watch lifestyle"
        />
      </div>
      <div className="hero-content container">
        <h1>Precision. Simplicity. Time reimagined.</h1>
        <p className="sub">A premium minimalist watch collection crafted for modern life.</p>
        <a className="btn primary" href="#shop">Shop the Collection</a>
      </div>
    </section>
  );
}
