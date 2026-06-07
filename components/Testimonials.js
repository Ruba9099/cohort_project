const reviews = [
  { name: 'Ava', text: 'Exquisite finish — understated and elegant.' },
  { name: 'Liam', text: 'Perfect balance of form and function.' },
  { name: 'Sophia', text: 'Timeless design; I wear it daily.' }
];

export default function Testimonials() {
  return (
    <section className="testimonials container">
      <h2>What customers say</h2>
      <div className="cards">
        {reviews.map((r) => (
          <blockquote key={r.name} className="review">
            <p>“{r.text}”</p>
            <footer>— {r.name}</footer>
          </blockquote>
        ))}
      </div>
      <div className="trust">
        <span className="badge">Secure payments</span>
        <span className="badge">2-year warranty</span>
        <span className="badge">Free returns</span>
      </div>
    </section>
  );
}
